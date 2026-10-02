# Opciones de alojamiento y MySQL en la nube

Revisión de documentación oficial: **1 de octubre de 2026**. Los planes, cupos y condiciones pueden cambiar. Este documento compara alternativas; no se crearon cuentas, bases remotas ni despliegues.

## Recomendación para JAGE

Para desarrollar sin gasto de alojamiento, ejecuta **Vue + Flask localmente y usa MySQL local o Aiven MySQL Free**. Así puedes probar persistencia real antes de publicar. Para un piloto público de costo inicial cero, una alternativa técnica es **Flask sirviendo el build de Vue en Render Free y MySQL en Aiven Free**. Las suspensiones y límites descritos abajo impiden prometer disponibilidad continua. Conviene pasar a un servicio sin suspensión cuando las reservas de clientes dependan de la web.

Una sola dirección HTTPS para frontend y API simplifica las cookies de sesión y la protección CSRF. El navegador llama a `/api/...`; únicamente Flask conoce las credenciales de MySQL. La ubicación de la base de datos puede cambiar mediante configuración, sin mover los datos al navegador.

**Vercel Hobby no es una opción gratuita adecuada para JAGE comercial:** su documentación restringe ese plan a uso personal no comercial. Captar solicitudes de transporte para el negocio tiene una finalidad comercial aunque no se cobre dentro de la web. Para esa opción, debe evaluarse un plan comercial como Pro. [Vercel Hobby](https://vercel.com/docs/plans/hobby), [condiciones de Vercel](https://vercel.com/legal/terms).

## Comparación

| Alternativa | Qué aloja | Evaluación para este proyecto |
| --- | --- | --- |
| MySQL local | Base de datos | Sin tarifa de nube; requiere que el equipo esté disponible. Ideal para desarrollo. |
| Aiven MySQL Free | MySQL administrado | Primera opción para probar MySQL real remoto; pocos recursos y sin SLA. |
| TiDB Cloud Starter | Base compatible con MySQL | Alternativa con cuota gratuita mayor; exige validar compatibilidad antes de adoptarla. |
| Render Free | API Flask y build Vue | Piloto con suspensión por inactividad; no garantiza respuesta inmediata. |
| Cloudflare Pages Free | Build estático Vue | Solo frontend; Flask y MySQL necesitan otros servicios. |
| Vercel Pro | Vue y Flask con funciones Python | Posible ruta futura de pago; MySQL sigue siendo un servicio externo. |

### Aiven MySQL Free

Ofrece un nodo, 1 CPU, 1 GB de RAM y 1 GB de disco. Incluye copias de seguridad y fija `max_connections` en 76. No solicita tarjeta para comenzar y no impone una fecha de expiración al plan; puede apagar instancias sin actividad y cambiar región o configuración. No incluye alta disponibilidad, soporte ni el SLA de los planes comerciales. Hay un servicio gratuito por tipo y organización. Revisa la región ofrecida y mantén pocas conexiones desde Flask. [Límites oficiales](https://aiven.io/docs/products/mysql/concepts/mysql-free-tier).

Aiven presenta este nivel para aprendizaje, prototipos y cargas pequeñas, no como solución para producción de alto tráfico. Subir a un plan de pago requiere añadir un medio de pago; confirma el plan seleccionado antes de crear el servicio. [Descripción y preguntas frecuentes de MySQL Free](https://aiven.io/free-mysql-database).

### TiDB Cloud Starter

Su cuota inicial incluye 5 GiB de almacenamiento por filas, 5 GiB columnar y 50 millones de unidades de petición mensuales por instancia elegible; una unidad de petición no equivale a una consulta SQL. No requiere tarjeta para empezar. Al agotar una cuota, puede rechazar nuevas conexiones y limitar las existentes hasta ampliar el cupo o su restablecimiento aplicable. Añadir tarjeta y un límite de gasto habilita consumo pagado: para mantener costo cero, conserva la modalidad gratuita. [Planes y cuotas](https://docs.pingcap.com/tidbcloud/select-cluster-tier/).

Es un motor **compatible con MySQL**, no MySQL idéntico. Antes de usarlo con JAGE, ejecuta migraciones y pruebas reales de claves foráneas, restricciones, bloqueos y cobro único de comisiones; aquí no se ha verificado esa integración. Consulta sus [limitaciones](https://docs.pingcap.com/tidbcloud/serverless-limitations/). La copia automática gratuita tiene retención de un día; prepara además tu propia exportación recuperable. [Copias de seguridad](https://docs.pingcap.com/tidbcloud/backup-and-restore-serverless/).

### Render Free

El servicio web se suspende después de 15 minutos sin tráfico entrante y el siguiente arranque puede tardar aproximadamente un minuto. El espacio de trabajo comparte 750 horas gratuitas mensuales. El disco del servicio es efímero: usuarios, reservas y movimientos deben permanecer en MySQL externo. Render advierte que estas instancias no se usen para aplicaciones de producción; también puede suspenderlas por tráfico saliente elevado, incluidas conexiones a bases externas. [Condiciones técnicas gratuitas](https://render.com/docs/free).

Si hay tarjeta registrada, exceder ancho de banda o minutos de compilación puede generar cargos. Sin medio de pago, Render suspende servicios o compilaciones según el límite alcanzado. Comprueba el panel de consumo y no actives ampliaciones de pago si buscas costo cero. No se presupone que toda cuenta esté exenta de verificaciones durante el alta. [Facturación del nivel gratuito](https://render.com/docs/faq).

### Cloudflare Pages Free

Puede servir el frontend compilado. Incluye 500 compilaciones mensuales, una simultánea, hasta 20 000 archivos y 25 MiB por archivo; las funciones tienen cuotas diferentes. [Límites de Pages](https://developers.cloudflare.com/pages/platform/limits/).

En las condiciones generales consultadas no se encontró la restricción de uso exclusivamente personal de Vercel Hobby; el acuerdo contempla entidades y servicios gratuitos. Esta es una lectura de esas condiciones, no una garantía contractual. Deben respetarse los términos específicos y las cuotas; Cloudflare puede terminar servicios gratuitos. [Acuerdo de autoservicio](https://www.cloudflare.com/terms/).

Pages estático no ejecuta este servidor Flask ni almacena MySQL. Separar frontend y API requiere diseñar un proxy de mismo origen o configurar explícitamente los orígenes y cookies permitidos, además de verificar CSRF. No basta con subir únicamente la carpeta del frontend y esperar que funcionen las reservas. Para esta primera versión es más sencillo servir ambos desde Flask.

## Si más adelante eliges Vercel

Vercel soporta Flask mediante una instancia `app` en un punto de entrada reconocido, como `wsgi.py`. La aplicación se convierte en una función Python. Los archivos estáticos deben publicarse desde `public/` según su integración; no se debe asumir que `app.static_folder` se comportará como en un servidor Flask tradicional. Antes de desplegar hay que adaptar la salida de Vite y las rutas, y probar navegación directa, API y cookies. [Flask en Vercel](https://vercel.com/docs/frameworks/backend/flask).

Las funciones tienen límites de tiempo y tamaño que dependen del plan y de Fluid Compute. Usa la configuración vigente del proveedor, limita conexiones a MySQL y evita tareas permanentes o migraciones al recibir solicitudes. [Límites de Functions](https://vercel.com/docs/functions/limitations). El sistema de archivos de ejecución no es almacenamiento persistente; MySQL debe permanecer en la nube. [Runtimes y sistema de archivos](https://vercel.com/docs/functions/runtimes).

Esta entrega no afirma que el proyecto esté validado en Vercel ni incluye un despliegue. La opción comercial debe presupuestarse antes de publicarla.

## Preparación concreta de la base remota

1. Elige el proveedor y crea una instancia **MySQL**, verificando en su panel que el plan sea gratuito y no una prueba temporal de un plan pagado.
2. Guarda host, puerto, nombre de base, usuario y contraseña en el `.env` local y después en las variables privadas del alojamiento. No los escribas en archivos Vue ni en variables `VITE_*`, porque esas terminan en el navegador.
3. Usa una conexión TLS con verificación del certificado y del nombre del servidor. Descarga la CA oficial del servicio si la necesita; configura las variables indicadas en `.env.example` y en el README. No desactives la verificación para ocultar errores de conexión.
4. Autoriza solo las redes necesarias cuando el proveedor permita restringirlas. Usa una cuenta de aplicación con los permisos necesarios sobre la base de JAGE; reserva los permisos de cambios de esquema para ejecutar migraciones.
5. Desde la terminal local, aplica las migraciones documentadas en el README y crea el primer administrador con el comando interactivo. No uses credenciales predeterminadas ni ejecutes estos pasos automáticamente en cada petición.
6. Comprueba registro, login, logout, aislamiento entre clientes, asignación manual, saldo, comisión al completar y promociones usando esa base. Las pruebas temporales con SQLite no sustituyen esta comprobación de MySQL remoto.
7. Configura copias recuperables y prueba una restauración antes de depender del servicio para las reservas.

## Antes de publicar

Construye Vue con las dependencias bloqueadas del proyecto y sirve los artefactos junto con la API. Mantén HTTPS, cookies `Secure` y `HttpOnly`, CSRF, un secreto largo estable fuera de Git y el modo debug desactivado. Configura correctamente el proxy de confianza del proveedor antes de interpretar cabeceras reenviadas. No cachees respuestas autenticadas ni compartas secretos entre entornos.

Faltan elegir proveedor y región, crear sus credenciales, configurar TLS, aplicar migraciones a esa instancia y realizar la verificación de extremo a extremo en el alojamiento elegido. Estas acciones quedan pendientes porque no se proporcionaron credenciales y se pidió **no publicar todavía**.
