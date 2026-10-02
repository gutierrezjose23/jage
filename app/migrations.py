"""Local CLI for versioned, restartable MySQL schema migrations and the first admin."""

import hashlib
import re
from datetime import timedelta
from pathlib import Path

import click
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db

MIGRATION_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _already_applied(connection, statement):
    """MySQL DDL commits implicitly; inspect individual steps after interruptions."""
    inspector = inspect(connection)
    # Profile backfills use NOT EXISTS and can safely run again after interruption.
    if re.match(r"INSERT INTO (clientes|conductores) \(user_id\)\s+SELECT\b", statement, re.I):
        return False
    create = re.match(r"CREATE TABLE (\w+)\s*\(", statement, re.I)
    if create:
        table = create.group(1)
        if not inspector.has_table(table):
            return False
        # Baseline the original manually executed SQL only when its columns exist.
        expected = set(re.findall(r"^\s{4}([a-z_]+)\s+(?:INT|VARCHAR|DATETIME|DATE|TIME|SMALLINT|DECIMAL|BOOLEAN)\b", statement, re.M))
        actual = {column["name"] for column in inspector.get_columns(table)}
        if not expected.issubset(actual):
            raise click.ClickException(f"La tabla {table} existe con un esquema diferente. Revisa una copia de seguridad antes de continuar.")
        if not inspector.get_pk_constraint(table).get("constrained_columns"):
            raise click.ClickException(f"La tabla {table} no tiene la clave primaria esperada.")
        if table == "users" and not any(item["column_names"] == ["email"] for item in inspector.get_unique_constraints(table)):
            raise click.ClickException("La tabla users necesita una restricción única para email.")
        if table == "reservations" and not any(item["constrained_columns"] == ["user_id"] and item["referred_table"] == "users" for item in inspector.get_foreign_keys(table)):
            raise click.ClickException("La tabla reservations no tiene la relación esperada con users.")
        if table in {"clientes", "conductores"}:
            if not any(item["constrained_columns"] == ["user_id"] and item["referred_table"] == "users" for item in inspector.get_foreign_keys(table)):
                raise click.ClickException(f"La tabla {table} necesita la relación con users.")
            if not any(item["column_names"] == ["dni"] for item in inspector.get_unique_constraints(table)):
                raise click.ClickException(f"La tabla {table} necesita una restricción única para DNI.")
        return True
    alter = re.match(r"ALTER TABLE (\w+) (ADD COLUMN|ADD INDEX|ADD CONSTRAINT|DROP CHECK) (\w+)", statement, re.I)
    if not alter:
        raise click.ClickException("Una migración contiene un paso DDL no reconocido.")
    table, action, name = alter.groups()
    action = action.upper()
    if action == "ADD COLUMN":
        return name in {column["name"] for column in inspector.get_columns(table)}
    if action == "ADD INDEX":
        return name in {index["name"] for index in inspector.get_indexes(table)}
    constraints = {item["name"] for item in inspector.get_check_constraints(table)}
    if action == "DROP CHECK":
        return name not in constraints
    constraints |= {item["name"] for item in inspector.get_foreign_keys(table)}
    constraints |= {item["name"] for item in inspector.get_unique_constraints(table)}
    return name in constraints


def upgrade_database():
    if db.engine.dialect.name != "mysql":
        raise click.ClickException("db-upgrade requiere MySQL 8.0.16 o posterior; SQLite se usa únicamente en pruebas.")
    lock_suffix = hashlib.sha256((db.engine.url.database or "jage").encode()).hexdigest()[:24]
    lock_name = "jage_migrations_" + lock_suffix
    with db.engine.connect() as connection:
        if connection.scalar(text("SELECT GET_LOCK(:name, 15)"), {"name": lock_name}) != 1:
            raise click.ClickException("Otra migración está en curso. Intenta nuevamente.")
        try:
            connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(100) PRIMARY KEY, applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB"))
            connection.commit()
            applied = set(connection.scalars(text("SELECT version FROM schema_migrations")))
            for migration in sorted(MIGRATION_DIR.glob("[0-9][0-9][0-9]_*.sql")):
                if migration.name in applied:
                    continue
                contents = re.sub(r"^\s*--.*$", "", migration.read_text(encoding="utf-8"), flags=re.M)
                statements = [statement.strip() for statement in contents.split(";") if statement.strip()]
                for statement in statements:
                    if not _already_applied(connection, statement):
                        connection.execute(text(statement))
                        connection.commit()
                connection.execute(text("INSERT INTO schema_migrations (version) VALUES (:version)"), {"version": migration.name})
                connection.commit()
                click.echo(f"Aplicada: {migration.name}")
            click.echo("Base de datos actualizada.")
        finally:
            connection.rollback()
            connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
            connection.commit()


def register_cli(app):
    @app.cli.command("db-check")
    def db_check():
        """Comprueba la conexión y las tablas del modelo sin mostrar credenciales."""
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                inspector = inspect(connection)
                missing = [name for name in db.metadata.tables if not inspector.has_table(name)]
                if missing:
                    raise click.ClickException("Faltan tablas: " + ", ".join(missing) + ". Ejecuta db-upgrade.")
                for name, table in db.metadata.tables.items():
                    columns = {column["name"] for column in inspector.get_columns(name)}
                    if not set(table.columns.keys()).issubset(columns):
                        raise click.ClickException(f"Faltan columnas en {name}. Ejecuta db-upgrade.")
                url = db.engine.url
                click.echo(f"Conexión correcta: {url.host}:{url.port or 3306} / {url.database}.")
                click.echo("Tablas verificadas: " + ", ".join(sorted(db.metadata.tables)))
        except SQLAlchemyError as error:
            raise click.ClickException(f"No se pudo comprobar MySQL ({type(error).__name__}). Revisa .env y el servicio.") from None

    @app.cli.command("db-upgrade")
    def db_upgrade():
        """Aplica las migraciones pendientes de MySQL sin borrar los datos existentes."""
        try:
            upgrade_database()
        except SQLAlchemyError as error:
            raise click.ClickException(f"No se pudo aplicar la migración ({type(error).__name__}). Verifica conexión, permisos y respaldo; vuelve a ejecutar db-upgrade.") from None

    @app.cli.command("init-admin")
    def init_admin():
        """Crea el primer administrador con datos interactivos, sin credenciales predeterminadas."""
        from app.models import User
        from app.security import APIError, validate_user

        if db.session.scalar(db.select(User).where(User.role == User.ROLE_ADMIN)):
            raise click.ClickException("Ya existe una cuenta administradora.")
        data = {"email": click.prompt("Correo del administrador"), "first_name": click.prompt("Nombre"),
                "last_name": click.prompt("Apellido"), "phone": click.prompt("Celular"),
                "password": click.prompt("Contraseña (12 a 128 caracteres)", hide_input=True, confirmation_prompt=True)}
        try:
            values = validate_user(data)
        except APIError as error:
            detail = " ".join((error.fields or {}).values())
            raise click.ClickException(f"{error.message} {detail}".strip()) from None
        password = values.pop("password")
        admin = User(**values, role=User.ROLE_ADMIN)
        admin.set_password(password)
        db.session.add(admin)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise click.ClickException("Ese correo ya está registrado.") from None
        click.echo("Administrador creado. Inicia sesión con el correo y contraseña que acabas de ingresar.")

    @app.cli.command("cleanup-rate-limits")
    def cleanup_rate_limits():
        """Elimina contadores de acceso inactivos de más de dos días."""
        from app.models import RateLimitBucket, utc_now
        result = db.session.execute(db.delete(RateLimitBucket).where(RateLimitBucket.window_start < utc_now() - timedelta(days=2)))
        db.session.commit()
        click.echo(f"Contadores eliminados: {result.rowcount}")
