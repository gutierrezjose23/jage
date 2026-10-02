# Crear una base JAGE desde cero en MySQL

Esta guía crea un esquema nuevo sin borrar ni modificar `jage_local`. Usa un administrador de MySQL en Workbench o en el cliente para crear la base y los usuarios; después Flask crea las tablas mediante las migraciones del proyecto.

## 1. Crear base y usuarios

Conéctate al servidor MySQL local en `127.0.0.1:3307` usando una cuenta administradora. Ejecuta lo siguiente y reemplaza cada contraseña de ejemplo por una contraseña fuerte y única:

```sql
CREATE DATABASE jage_desde_cero
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

CREATE USER 'jage_migrator_nuevo'@'localhost'
  IDENTIFIED BY 'REEMPLAZA_CON_CLAVE_FUERTE_DE_MIGRACIONES';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON jage_desde_cero.* TO 'jage_migrator_nuevo'@'localhost';

CREATE USER 'jage_app_nuevo'@'localhost'
  IDENTIFIED BY 'REEMPLAZA_CON_OTRA_CLAVE_FUERTE_DE_APLICACION';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON jage_desde_cero.* TO 'jage_app_nuevo'@'localhost';
```

No ejecutes `DROP DATABASE` ni reutilices `jage_local` si contiene datos que deban conservarse.

## 2. Configurar `.env` para migrar

En la raíz del proyecto, conserva una `SECRET_KEY` aleatoria de al menos 32 caracteres y configura temporalmente la URL con el usuario migrador:

```dotenv
APP_ENV=development
SECRET_KEY=TU_SECRETO_ALEATORIO_LOCAL_DE_64_CARACTERES
DATABASE_URL=mysql+pymysql://jage_migrator_nuevo:CLAVE_URL_ENCODED@127.0.0.1:3307/jage_desde_cero?charset=utf8mb4
SESSION_COOKIE_SECURE=false
MYSQL_SSL=false
DB_POOL_MODE=null
```

Genera el secreto sin publicarlo:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Si una contraseña contiene caracteres reservados de URL, codifícalos antes de guardarla en `DATABASE_URL`. Por ejemplo, `@` se representa como `%40`, `#` como `%23`, `%` como `%25` y `:` como `%3A`. No pongas comillas alrededor del valor en `.env`. Mantén el archivo ignorado por Git y no compartas su contenido.

## 3. Crear tablas con las migraciones

Desde PowerShell en la raíz del proyecto:

```powershell
.\.venv\Scripts\flask.exe --app app:create_app db-upgrade
```

El comando aplica en orden `001` a `004`. Crea `users`, `reservations`, saldos, movimientos, promociones, límites de intentos y perfiles `clientes`/`conductores`; también registra cada migración en `schema_migrations`. Es reanudable y no borra tablas ni datos. Para una base nueva deben aparecer las cuatro migraciones como aplicadas.

## 4. Cambiar al usuario de ejecución y verificar

Reemplaza solo el usuario y la contraseña de `DATABASE_URL` por los de `jage_app_nuevo`. Conserva host, puerto, nombre de base y opciones. El usuario de ejecución no debe tener permisos DDL.

```powershell
.\.venv\Scripts\flask.exe --app app:create_app db-check
```

La salida debe confirmar `127.0.0.1:3307 / jage_desde_cero` y listar las tablas verificadas.

## 5. Crear administrador e iniciar

```powershell
.\.venv\Scripts\flask.exe --app app:create_app init-admin
```

El comando pide los datos y la contraseña del administrador sin credenciales predeterminadas. Después inicia Flask y Vite en terminales separadas:

```powershell
.\.venv\Scripts\flask.exe --app app:create_app run --host 127.0.0.1 --port 5000
```

```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Abre <http://127.0.0.1:5173>. Vite envía las peticiones `/api` a Flask en el puerto `5000`.

## Si aparece `Access denied`

Una base sin tablas no produce este error. `Access denied` indica que MySQL rechazó usuario/contraseña o que la contraseña quedó mal codificada en la URL. Comprueba que el usuario migrador exista, que el `.env` use la clave que asignaste en `CREATE USER` y que los caracteres reservados estén codificados. No pegues la contraseña en el chat.

Si `db-check` conecta pero muestra tablas faltantes, ejecuta `db-upgrade` con el usuario migrador. No uses `db.create_all()` ni apuntes las pruebas automatizadas a esta base.