# Clientes y conductores en MySQL

La conexión local está activa en **127.0.0.1:3307**, base **jage_local**. Flask usa SQLAlchemy y PyMySQL; `DATABASE_URL` y la contraseña están en `.env`, fuera de Git. Vue envía los formularios a `/api`; la contraseña de MySQL nunca se incluye en el frontend.

## Organización de los datos

Se conserva `users` para las cuentas y los datos de contacto, y se crearon dos tablas de perfiles relacionadas por `user_id`. Así, las reservas, las sesiones y los saldos siguen usando los mismos identificadores.

| Dato solicitado | Cliente | Conductor |
| --- | --- | --- |
| Nombre | `users.first_name` | `users.first_name` |
| Apellido | `users.last_name` | `users.last_name` |
| Teléfono | `users.phone` | `users.phone` |
| DNI | `clientes.dni` | `conductores.dni` |
| Correo | `users.email` | `users.email` |
| Placa del carro | — | `conductores.placa` |

Cada perfil tiene una relación uno a uno con su cuenta. El correo es único entre todas las cuentas; el DNI es único dentro de cada tipo de perfil. La placa tiene un índice y puede compartirse entre conductores que utilizan el mismo vehículo.

El DNI se guarda como `VARCHAR(8)` para conservar ceros iniciales. Los registros nuevos requieren 8 dígitos. La placa admite 6 letras/números con un guion opcional y se guarda en mayúsculas con el formato `ABC-123`. Estas comprobaciones validan el formato, no consultan registros externos de identidad o vehículos.

La migración `004_customer_driver_profiles.sql` crea los perfiles de las cuentas anteriores con DNI/placa `NULL`, porque esos datos aún no se habían solicitado. No cambia sus contraseñas, cuentas, reservas ni saldos. Los formularios nuevos sí exigen los datos correspondientes.

## Consultas para ver todos los campos juntos

Ejecuta [consultas_perfiles.sql](consultas_perfiles.sql) en MySQL Workbench, seleccionando la base `jage_local`. Las consultas unen cada perfil con `users` y muestran los nombres de columnas en español.

## Guardado desde la web

- `/registro`: nombre, apellido, DNI, celular, correo y contraseña. El servidor crea la cuenta y el perfil de cliente en una transacción.
- Administración → Conductores y saldo → Crear conductor: los mismos datos más la placa. Se crea la cuenta, el perfil de conductor y el saldo inicial de cero en una transacción.
- La lista administrativa muestra el DNI y la placa; al asignar una reserva, la placa ayuda a identificar al conductor.

El registro público crea clientes. Para dar de alta conductores se necesita una cuenta administradora. Si aún no existe una, créala desde la carpeta del proyecto con `.\.venv\Scripts\python.exe -m flask --app app init-admin` y completa los datos que solicita la terminal.

## Comprobar la conexión

```powershell
.\.venv\Scripts\python.exe -m flask --app app db-check
```

Comprueba la conexión y las tablas/columnas del modelo sin imprimir contraseñas. Para otra instalación, configura `.env` y ejecuta `db-upgrade` con una cuenta con permisos de migración; después usa la cuenta de aplicación con permisos de lectura y escritura.

En esta computadora la migración ya está aplicada. Se guardó un respaldo previo en `.local-backup/mysql-before-profiles-20261002-044605.sql`, ignorado por Git. La cuenta `jage_app` conserva permisos de aplicación; los cambios de esquema se ejecutaron con `jage_migrator`.

## Verificación realizada

- Conexión y esquema de `jage_local` comprobados con la cuenta de aplicación.
- Migración ejecutada y repetida sin duplicar perfiles; cuentas y reservas conservadas.
- Suite API en SQLite: 138 aprobadas, 5 omitidas porque requieren concurrencia MySQL.
- Pruebas de perfiles en MySQL real: 23 aprobadas sobre una base temporal independiente, eliminada al terminar.
- Navegador: 12 aprobadas, incluyendo registro con DNI y alta de conductor con DNI/placa.
- Compilación Vue y formato: aprobados.
