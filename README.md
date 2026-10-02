# JAGE · Vamos contigo

Aplicación de transporte de Huaral, Perú: viajes privados, Huaral–Lima y aeropuerto. **Vue 3 + Vue Router + Vuetify 3 + Tailwind CSS**, API **Flask** y persistencia **MySQL**. La navegación, formularios y paneles funcionan sin recargar la página. No se usan `localStorage` ni datos de demostración para simular reservas o saldos.

Una solicitud nueva está **pendiente**: JAGE debe confirmarla. El saldo de conductor sirve para **descontar comisiones por viajes completados**; no es una cuenta bancaria ni un procesador de pagos.

**MySQL: clientes y conductores.** La conexión local usa `127.0.0.1:3307`, base `jage_local`. Las tablas `clientes` y `conductores` se relacionan con `users`: conservan nombre, apellido, teléfono y correo de la cuenta, agregan DNI al perfil y placa al conductor. La migración está en `migrations/004_customer_driver_profiles.sql`. Consulta [el esquema, la conexión y el guardado](docs/mysql-clientes-conductores.md) o [las consultas SQL con todos los campos](docs/consultas_perfiles.sql).

Para crear una base vacía y aislada, sin modificar `jage_local`, sigue [la guía de MySQL desde cero](docs/mysql-desde-cero.md).

## Diseño e interfaz

La portada, el acceso, las reservas y los paneles comparten una identidad minimalista: azul intenso `#083bfa`, celeste `#6dd5e8`, blanco y fondo gris suave `#f5f7fb`. Los estilos compartidos están en `style.css` y el tema de Vuetify en `src/plugins/vuetify.js`; ambos deben mantenerse alineados al cambiar la paleta. La tipografía base es de 18 px en escritorio y 17 px en móvil, con ayudas y estados de al menos 14 px.

El header y su menú móvil usan azul con enlaces blancos. La foto original del vehículo se integra con el fondo mediante filtros, mezcla de luminosidad y degradados CSS; el archivo de imagen se conserva. El acceso y registro comparten una tarjeta blanca con un panel azul y detalles geométricos discretos.

`FormField.vue` utiliza `VTextField`, `VTextarea` y `VSelect`; `AppForm.vue` utiliza `VForm`. Los campos conservan etiquetas, autocompletado y validaciones; los errores del servidor se pueden corregir antes de volver a enviar. Los selectores son componentes accesibles con opciones desplegables y navegación por teclado. Los iconos SVG y estilos se sirven localmente, sin depender de fuentes de iconos externas.

## Qué hace la aplicación y en qué sección

| Sección / ruta | Quién accede | Funciones |
| --- | --- | --- |
| Inicio `/` | Todos | Presentación de JAGE y acceso a reservas. Usa la imagen existente del vehículo. |
| Servicios `/servicios` | Todos | Viajes privados, Huaral–Lima y aeropuerto; selecciona el servicio al solicitar. |
| Cómo reservar `/como-reservar` | Todos | Explica registro, solicitud y confirmación. |
| Contacto `/contacto` | Todos | Nombre, correo, origen opcional y consulta; muestra una vista previa y prepara WhatsApp al **51934613286**. La persona debe enviar el mensaje en WhatsApp. Esto no crea una reserva. |
| Ubicación, dentro de contacto y reserva | Todos / clientes | Solicita geolocalización solo al pulsar el botón, muestra coordenadas y enlace para revisarlas, y permite aplicar o descartar. Maneja denegación, tiempo de espera y ubicación no disponible. Siempre puedes escribir el origen. |
| Crear cuenta `/registro` | Visitantes | Nombre, apellido, DNI, celular, correo y contraseña. Solo crea **clientes** (`passenger` en base de datos); no permite elegir administrador o conductor. |
| Ingresar `/ingresar` | Usuarios registrados | Sesión mediante cookie protegida; redirige al panel del rol. Cierre de sesión desde la navegación. |
| Solicitar `/reservar` | Clientes | Servicio, origen, destino, fecha/hora de Perú, 1–8 pasajeros y observaciones opcionales. Validación de cliente y servidor. |
| Mis reservas `/mis-reservas` | Clientes | Sus propias solicitudes y estado; sin acceso a información de otros clientes. |
| Administración `/administracion`, reservas | Administradores | Consulta solicitudes y datos de coordinación, filtra estados, asigna manualmente conductor, define comisión y cambia estado. |
| Administración, conductores | Administradores | Crea cuentas de conductor con nombre, apellido, DNI, celular, correo y placa; consulta saldo y registra ajustes con motivo. No hay alta pública de conductores. |
| Administración, promociones | Administradores | Publica beneficios de saldo con título, descripción, importe y vencimiento; activa/desactiva. No se crean promociones ficticias. |
| Mi espacio `/conductor` | Conductores | Sus viajes asignados, saldo para comisiones, movimientos e historial, promociones disponibles y canje único. |

## Reglas de reservas, saldo y promociones

La navegación pública usa rutas de Vue Router con historial HTML5, sin `#` en la URL. `/servicios`, `/como-reservar` y `/contacto` llevan a la sección correspondiente de la portada sin recargar la página; también funcionan al abrir el enlace directamente. Los enlaces antiguos con fragmento redirigen a la ruta nueva.

1. Los estados son `pendiente`, `confirmada`, `cancelada` y `completada`. Se puede confirmar o cancelar una pendiente; completar o cancelar una confirmada. Canceladas y completadas son terminales.
2. El administrador asigna un conductor y define la **comisión en soles** por reserva. No hay tarifa inventada, cálculo automático ni asignación automática.
3. Al completar un viaje, MySQL registra el cambio de estado y descuenta la comisión en **una transacción**. Repetir la petición no vuelve a cobrar. Un saldo insuficiente impide completar: primero se debe registrar un ajuste válido.
4. Los ajustes manuales de saldo requieren motivo y clave de operación única. Los negativos no pueden dejar saldo bajo cero. El historial conserva importe, saldo resultante, fecha, motivo y responsable; la API no permite editar ni borrar esos movimientos.
5. Cada conductor puede canjear una promoción activa y vigente una sola vez. El importe se suma al saldo para comisiones; no hay retiro ni pago a tarjeta.
6. Registrar una recarga en el panel es **un apunte administrativo**. No verifica transferencias ni mueve dinero externo. JAGE debe verificar fuera del sistema cualquier acuerdo o abono antes de anotarlo.
7. Las cantidades se guardan como `DECIMAL`, no como números de coma flotante. Bloqueos de filas y restricciones únicas protegen descuentos y canjes simultáneos.

No se incluyen pagos, seguimiento en tiempo real, asignación automática, recuperación de contraseña por correo ni verificación de correo. Los dos últimos requieren configurar un proveedor de correo y un flujo adicional antes de habilitarlos.

## Requisitos en Windows / VS Code

- Python **3.11 o posterior** con `py`/`python` accesible; extensión Python de VS Code.
- Node.js **22.18 o posterior** (se verificó con Node 24); npm incluido en su instalador.
- MySQL **8.0.16 o posterior**, recomendado 8.4 LTS, o una instancia MySQL remota. MySQL 9.5 se usa en las comprobaciones locales de esta entrega.
- Git opcional para ver el historial original.

Abre **esta carpeta**, no `app/`, en VS Code. No abras `index.html` por doble clic ni con Live Server: necesita Vite o el build servido por Flask.

## 1. Preparar Python y Vue

En PowerShell, desde la raíz:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd ci
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Copia el secreto generado en `SECRET_KEY` dentro de `.env`. No compartas ni subas `.env` a Git. Los comandos usan el ejecutable del entorno directamente; no necesitas cambiar la política de ejecución de PowerShell. En VS Code selecciona `.venv\Scripts\python.exe` como intérprete.

## 2. Configurar MySQL local

Abre MySQL Workbench como administrador y ejecuta, **cambiando ambas contraseñas**:

```sql
CREATE DATABASE jage CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'jage_migrator'@'localhost' IDENTIFIED BY 'CAMBIA_ESTA_CLAVE_MIGRACIONES';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
ON jage.* TO 'jage_migrator'@'localhost';
CREATE USER 'jage_app'@'localhost' IDENTIFIED BY 'CAMBIA_ESTA_CLAVE_APLICACION';
GRANT SELECT, INSERT, UPDATE, DELETE ON jage.* TO 'jage_app'@'localhost';
```

Configura temporalmente `DATABASE_URL` en `.env` con el usuario de migraciones:

```dotenv
APP_ENV=development
SECRET_KEY=PEGA_EL_SECRETO_ALEATORIO_GENERADO
DATABASE_URL=mysql+pymysql://jage_migrator:CONTRASENA_CODIFICADA@localhost:3306/jage?charset=utf8mb4
SESSION_COOKIE_SECURE=false
MYSQL_SSL=false
```

En la URL, caracteres especiales de usuario/contraseña deben codificarse (por ejemplo `@` → `%40`, `#` → `%23`). No uses literalmente los ejemplos como credenciales. Verifica host y puerto: MySQL local normalmente usa `3306`.

## 3. Migraciones y primer administrador

```powershell
.\.venv\Scripts\python.exe -m flask --app app db-upgrade
.\.venv\Scripts\python.exe -m flask --app app init-admin
```

El primer comando aplica y registra las migraciones SQL pendientes. No ejecutes `db.create_all()` en una base de producción. Las migraciones iniciales existentes se conservan; la tercera amplía usuarios/reservas y agrega saldos, promociones y protección de intentos. La cuarta crea los perfiles `clientes` y `conductores` con DNI y placa. Haz una copia de seguridad antes de migrar datos existentes. Los cambios de esquema de MySQL pueden hacer commit implícito: no interrumpas la operación y revisa cualquier error antes de reintentar.

El segundo solicita correo, nombre, apellido, celular y contraseña con confirmación. No existen usuario ni contraseña de administrador predeterminados. Solo crea el primer administrador; rechaza su ejecución si ya hay uno. El registro público jamás sirve para hacerse administrador.

Después de migrar, cambia `DATABASE_URL` al usuario `jage_app`, que no tiene permisos de modificación de esquema. Para futuras migraciones utiliza nuevamente la cuenta de migraciones solo durante ese comando.

## 4. Iniciar el proyecto

**Desarrollo con recarga de código**: usa dos terminales en la raíz.

Terminal 1, API:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Terminal 2, Vue:

```powershell
npm.cmd run dev
```

Abre **http://127.0.0.1:5173**. Vite reenvía `/api` a Flask en `127.0.0.1:5000`; no hace falta habilitar CORS. Usa siempre el mismo host en esa sesión para evitar confundir cookies de `localhost` y `127.0.0.1`.

**Aplicación compilada con un solo servidor**:

```powershell
npm.cmd run build
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Abre **http://127.0.0.1:5000**. Flask sirve `dist/` y la API. `npm run preview` sirve únicamente el build para revisión visual; usa Flask para validar la aplicación completa.

No uses el servidor de desarrollo de Flask como servidor público. El punto de entrada WSGI es `wsgi:app`; un alojamiento Linux puede usar Gunicorn y Windows puede usar Waitress tras instalarlo. La publicación no se ha realizado ni autorizado en esta entrega.

## MySQL en la nube y Vercel

Consulta [opciones verificadas y fuentes oficiales](docs/hosting.md). Para empezar: **MySQL local o Aiven MySQL Free**. Para un piloto gratuito: Flask + build Vue en Render y MySQL externo, aceptando que Render suspende el servicio por inactividad. Vercel Hobby restringe el uso a proyectos personales no comerciales; JAGE necesita evaluar un plan comercial. No hay una promesa de alojamiento comercial gratuito permanente.

En la instancia remota, configura `DATABASE_URL` con host, puerto y credenciales del proveedor; `MYSQL_SSL=true` y, si corresponde, `MYSQL_SSL_CA` con la ruta de su certificado CA. La conexión verifica certificado y nombre del servidor. Nunca uses variables `VITE_*` para secretos. En producción: `APP_ENV=production`, HTTPS, cookie segura y secreto estable; `TRUST_PROXY=true` solo detrás de **un proxy de confianza** configurado por el alojamiento.

**Pendiente para la nube:** elegir proveedor/región, crear instancia y credenciales, configurar TLS, aplicar migraciones allí y validar esa conexión. La base de nube no fue creada. Vercel además requiere adaptar los estáticos según su integración Flask, como explica el documento de alojamiento.

## Organización del código

```text
index.html                 Entrada Vite, español y metadatos
style.css                  Tailwind + identidad visual y responsive
ubicacion.js               Geolocalización reactiva y enlaces WhatsApp
src/App.vue                Navegación, cierre de sesión y layout
src/router.js              Rutas SPA y guardas de interfaz
src/components/            Campos, mensajes, tarjetas, estados, ubicación, iconos
src/views/                 Inicio, auth, reservas, administración, conductor
src/lib/                   Cliente API/CSRF, sesión en memoria y formatos
app/__init__.py            Fábrica Flask, cookies, errores y cabeceras
app/models.py              Usuarios, reservas, monederos, movimientos, promociones
app/auth.py                Registro, login, logout y sesión
app/reservations.py        Solicitudes y acceso por propietario
app/admin.py               Gestión de reservas y conductores
app/drivers.py             Panel conductor y canjes
app/wallets.py             Movimientos de saldo y reglas monetarias
app/security.py            Validadores, autorización y límite de intentos
app/main.py                Build SPA, archivos y salud de la API
migrations/                Migraciones SQL versionadas
tests/                     API y navegador sobre bases aisladas
docs/hosting.md            Alternativas de nube y restricciones
wsgi.py                    Entrada WSGI del servidor
```

Vue separa plantillas (`<template>`), lógica (`<script setup>`) y estilos compartidos. Las antiguas plantillas Flask no forman parte del flujo activo. La fábrica Flask, SQLAlchemy y la separación por rutas existentes fueron aprovechadas y ampliadas.

Los originales `index.html`, `style.css`, `ubicacion.js` y `fog.js` están en el historial Git anterior (por ejemplo `41d9b7b`). Puedes leerlos con `git show 41d9b7b:index.html`; no ejecutes `git reset --hard` sobre tu trabajo. Además, se conservó una copia local del estado Flask previo en `.local-backup/pre-vue-project.zip` (ignorada por Git).

## Seguridad implementada

- Contraseñas mediante `scrypt`, validación estricta y consultas parametrizadas con SQLAlchemy.
- Cookies `HttpOnly`, `SameSite=Lax`, caducidad, `Secure` obligatorio en producción y renovación de sesión al autenticar.
- CSRF en **todas** las operaciones de escritura, incluido login/logout; el cliente recibe un token y lo envía en cabecera. Los errores no reintentan automáticamente cargos ni ajustes.
- Roles y propiedad comprobados en Flask; las guardas Vue solo mejoran la navegación.
- Límites de intentos de acceso persistidos en MySQL, con identificadores protegidos por HMAC. No se guardan contraseñas ni IP/correo en claro en esos contadores.
- Cabeceras de seguridad, política CSP, respuestas privadas sin caché y mensajes de error sin credenciales ni trazas para el cliente.
- Precisión decimal, transacciones y bloqueo de filas para movimientos; claves únicas para impedir doble comisión/canje/ajuste.

Para limpiar contadores de intentos con más de dos días de antigüedad, ejecuta periódicamente `.\.venv\Scripts\python.exe -m flask --app app cleanup-rate-limits`. Conserva copias de MySQL y comprueba su restauración; no borres movimientos para corregir saldos: registra un ajuste con motivo.

## Pruebas

API con base SQLite efímera **solo para pruebas**, nunca como alternativa silenciosa a MySQL:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

La misma suite puede ejecutarse con MySQL real. Crea una base **vacía y exclusiva** llamada `jage_test`, configura una cuenta con permisos de crear/borrar tablas en ella y ejecuta:

```powershell
$env:TEST_DATABASE_URL = 'mysql+pymysql://USUARIO:CLAVE@127.0.0.1:3306/jage_test'
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:TEST_DATABASE_URL
```

**Las pruebas crean y borran tablas.** La protección rechaza bases cuyo nombre no empieza por `jage_test`; jamás apuntes a la base de negocio.

Navegador (usa una base efímera de pruebas por defecto y crea cuentas de prueba solo ahí):

```powershell
npm.cmd run build
npx.cmd playwright install chromium
$env:JAGE_E2E_PASSWORD = (& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(24))")
npm.cmd run test:e2e
Remove-Item Env:JAGE_E2E_PASSWORD
```

Playwright inicia automáticamente un servidor aislado en `127.0.0.1:5010`. Para usar Chrome instalado, define `PLAYWRIGHT_CHROME_PATH`; para Python fuera de `.venv`, define `JAGE_TEST_PYTHON`. Puedes usar `TEST_DATABASE_URL` con una **segunda base vacía**, por ejemplo `jage_test_browser`. Las capturas quedan en `.test-artifacts/`, ignorada por Git.

Cobertura: registro, login/logout, CSRF, validación, aislamiento de clientes y conductores, roles, estados, comisión única, saldo insuficiente, idempotencia, promociones, formularios, WhatsApp, errores de ubicación y pantallas de 360/768/1440 px. Consulta [el registro de verificación](docs/verificacion.md) para los resultados realmente ejecutados y sus límites.

## Problemas frecuentes

### Base local preparada para probar el login

En esta computadora se configuró una instancia independiente de MySQL en `127.0.0.1:3307`, base `jage_local`. La instancia temporal de las pruebas anteriores fue eliminada; esta nueva instancia conserva los datos en `.local-runtime/mysql/data`. No es una base en la nube ni afecta al servicio MySQL del puerto 3306.

La conexión de Flask ya está en `.env`, con una cuenta de aplicación limitada a consultar y modificar datos. Las contraseñas aleatorias de administración y migraciones están en `.local-runtime/mysql-credentials.json`. Ambos archivos se excluyen de Git; no los compartas. Esta configuración local no se incluye al clonar el repositorio.

Para probar: abre `http://127.0.0.1:5173/registro`, crea tu cuenta, cierra sesión y entra en `http://127.0.0.1:5173/ingresar`. No hay cuentas ni contraseñas predeterminadas. Se verificaron registro, login, logout y rechazo de contraseña incorrecta a través de Vue y MySQL; la cuenta automatizada utilizada se eliminó.

Después de reiniciar Windows, desde la raíz del proyecto inicia MySQL con el script local (requiere la instalación actual de MySQL 9.5):

```powershell
powershell -ExecutionPolicy Bypass -File .\.local-runtime\start-mysql.ps1
```

Luego inicia Flask y Vue en dos terminales, dejándolas abiertas:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

No borres `.local-runtime/mysql/data` si deseas conservar las cuentas y reservas locales. No ejecutes las pruebas automatizadas contra `jage_local`; utilizan sus propias bases aisladas.

### Diagnóstico

- **`node`/`npm` no se reconoce:** instala Node, cierra y vuelve a abrir VS Code. En PowerShell usa `npm.cmd` si se bloquea `npm.ps1`.
- **Falta `SECRET_KEY` o `DATABASE_URL`:** copia `.env.example`, configura valores reales y ejecuta desde la raíz.
- **MySQL access denied / connection refused:** revisa usuario, contraseña codificada, host, puerto y servicio activo; la aplicación no inventa una base ni simula guardado.
- **Faltan tablas:** aplica `flask --app app db-upgrade` con la cuenta de migraciones y verifica que ambas cuentas apunten a la misma base.
- **No aparece el frontend en Flask:** ejecuta `npm ci` y `npm run build`, o entra por el puerto de Vite en desarrollo.
- **Sesión caducada / CSRF:** vuelve a iniciar sesión o reintenta después del mensaje de renovación. Revisa que el navegador acepte cookies y que todo use el mismo origen.
- **Geolocalización en un celular de otra red:** los navegadores requieren HTTPS (o localhost); escribir el origen siempre está disponible.
- **Saldo insuficiente:** verifica el abono fuera del sistema, registra un ajuste con motivo y vuelve a completar el viaje. No cambies tablas directamente para saltarte el historial.
