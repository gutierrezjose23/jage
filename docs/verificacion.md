# Registro de verificación

## Perfiles de clientes y conductores · 1 de octubre de 2026

La migración `004_customer_driver_profiles.sql` está aplicada en `jage_local` y `db-check` verifica la conexión con la cuenta de aplicación. Se conservan las cuentas y reservas anteriores. La suite API aprobó 138 casos en SQLite, con 5 omitidos de concurrencia MySQL; las 23 pruebas de perfiles aprobaron también sobre MySQL real aislado. Los 12 casos de navegador aprobaron con los campos DNI y placa. Compilación y formato aprobados. Detalles y consultas en [MySQL: clientes y conductores](mysql-clientes-conductores.md).

## Actualización visual y Vuetify · 1 de octubre de 2026

Se completó la interfaz azul, celeste, blanca y gris, incluyendo el header azul y el tratamiento CSS de la foto del automóvil. Los formularios comparten VForm, VTextField, VTextarea y VSelect; el texto base usa 18 px en escritorio y 17 px en móvil.

- Compilación de producción: aprobada con `vite build --configLoader runner`. Este cargador evita el acceso a directorios superiores bloqueado para esbuild en el entorno de revisión.
- Formato: `prettier --check src index.html style.css ubicacion.js vite.config.js playwright.config.js tests/e2e` aprobado.
- Navegador: **12 pruebas aprobadas**, con Chrome instalado, Flask real y SQLite efímero aislado. En esta actualización no se repitió la suite MySQL.
- Inicio y menú responsive a **360, 768, 900 y 1440 px**, sin desbordamiento horizontal; imágenes válidas y campos etiquetados de al menos 16 px.
- Validación de campos requeridos, correo, contraseña, confirmación, pasajeros y recuperación tras corregir errores; selección por teclado y clic en opciones Vuetify.
- Registro, acceso, reserva, paneles, alta de conductor, ajuste de saldo, promoción, asignación, confirmación, comisión y canje completos.
- Capturas revisadas de portada, acceso y reserva en escritorio/móvil. El texto de nombres largos en el panel se ajusta al ancho disponible.

Durante la revisión se adaptaron los selectores de las pruebas al área visible de VSelect y se corrigió un desbordamiento móvil. El servidor de pruebas serializa las peticiones solo con SQLite en memoria, cuya conexión compartida no admite transacciones concurrentes; el modo MySQL conserva los hilos. Las capturas están en `.test-artifacts/`, incluyendo `home-1440-viewport.png`, `home-360-viewport.png`, `login-desktop.png` y `booking-mobile.png`.

## Verificación anterior de la base funcional

Comprobaciones locales realizadas el **1 de octubre de 2026**, en Windows, con Python 3.13.4, Node 24.14.0, MySQL 9.5 y Chrome instalado. No se utilizaron datos de clientes ni credenciales de una base de negocio. El MySQL temporal se ejecutó exclusivamente en `127.0.0.1:3307`, separado del servicio MySQL existente.

## Resultados de backend

| Comprobación | Resultado |
| --- | --- |
| `pytest tests/test_app.py` con SQLite en memoria | **109 aprobadas** |
| La misma suite con MySQL real aislado | **109 aprobadas** |
| `pytest tests/test_security_extra.py` con MySQL real | **11 aprobadas** |
| Suite adicional con SQLite | **6 aprobadas, 5 omitidas**; las cinco requieren bloqueos de filas de MySQL |
| Migraciones `001`, `002`, `003` sobre MySQL vacío | Aprobado |
| Segunda ejecución de `db-upgrade` | Aprobado, sin duplicar cambios |
| Migración de tablas originales con usuario y reserva existentes | Aprobado; conserva IDs, datos, hash y estado, sin cobrar comisiones retroactivas |
| `pip check` | Sin dependencias incompatibles |

Las **120 pruebas de backend en MySQL** cubren registro público sin privilegios, hash de contraseñas, normalización de correo, login/logout, CSRF real, tipos y longitudes inválidos, fechas y horas de Perú, consultas seguras, propiedad de reservas, matriz de roles, asignación manual, transiciones, comisión única, saldo insuficiente, importes decimales, UUID de operación, promociones, vencimiento y creación local del administrador.

Las cinco comprobaciones de concurrencia usan peticiones simultáneas con sesiones distintas:

1. Completar la misma reserva dos veces descuenta una sola comisión.
2. Dos viajes compitiendo por saldo limitado no dejan la billetera negativa.
3. Dos ajustes con la misma clave de operación acreditan una sola vez.
4. Dos ajustes distintos conservan ambos importes, sin perder actualizaciones.
5. Dos canjes simultáneos de la misma promoción solo generan un abono.

También se comprueba que los límites de intentos persisten entre navegadores, que sus claves no almacenan correos/IP en claro y que la configuración de producción exige TLS verificado para MySQL remoto.

## Build e interfaz

`npm run build` compila Vue y Tailwind sin errores y `npm run format:check` aprueba. Los recursos se sirven desde el proyecto; no se usan CDNs. `npm audit --omit=dev` notificó **0 vulnerabilidades** conocidas en las dependencias de ejecución durante esta verificación.

**Los 10 casos de Playwright aprobaron**: siete casos públicos/responsive, un recorrido de cliente y dos recorridos de administración/conductor. Tras corregir selectores de las pruebas y esperar explícitamente la finalización del logout, se repitieron los casos afectados hasta aprobar. Las comprobaciones siguientes corresponden al build final.

Las pruebas de navegador utilizan **el build real servido por Flask y MySQL real**, no respuestas simuladas de la API. Comprueban:

- Inicio a **360, 768 y 1440 px**, sin desbordamiento horizontal, con imágenes/scripts válidos y campos etiquetados de al menos 16 px.
- Menú móvil y navegación hacia autenticación.
- WhatsApp con nombre, correo, consulta y origen, vista previa y número correcto. No se abre una conversación externa ni se envían mensajes durante las pruebas.
- Ubicación solicitada únicamente por clic, revisión antes de aplicarla y entrada manual. La API de geolocalización del navegador se simula para probar éxito y errores de permiso, disponibilidad y tiempo de espera; no se afirma haber probado el GPS físico de un teléfono.
- Registro de cliente, solicitud pendiente, consulta, logout y login sin recargas entre acciones de la SPA.
- Paneles de administración y conductor, acceso por URL directa, recarga explícita y vista móvil.
- Alta de conductor, recarga administrativa, publicación de promoción, asignación de reserva, confirmación, descuento de comisión al completar, canje único y consulta del historial.

Las capturas locales están en `.test-artifacts/` (fuera de Git): inicio móvil/tablet/escritorio, panel administrativo y saldo/historial del conductor.

## Límites y configuración pendiente

- MySQL en la nube y su conexión TLS real quedan pendientes de elegir proveedor y proporcionar credenciales. Las pruebas locales no equivalen a una prueba del proveedor remoto.
- No se desplegó en Vercel, Render ni otro alojamiento. Sus condiciones y configuración se explican en [hosting.md](hosting.md).
- La revisión responsive utiliza tamaños de pantalla en Chrome, no una matriz física de dispositivos ni Safari/Firefox.
- No se procesaron pagos, abonos reales, retiros ni mensajes de WhatsApp. Los registros de pruebas pertenecen exclusivamente a bases temporales.
- Los resultados describen los escenarios ejecutados; no constituyen una garantía absoluta de ausencia de errores ni una auditoría externa de seguridad.
