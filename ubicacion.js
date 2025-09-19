// Botón de ubicación

function handleClick() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                // Enlace de Google Maps con las coordenadas
                const link = `https://www.google.com/maps?q=${lat},${lon}`;

                // Número en formato internacional (ejemplo Perú: +51 sin "+")
                const numero = "51934613286";

                // Texto que se mandará por WhatsApp
                const mensaje = `Hola, esta es mi ubicación: ${link}`;

                // Enlace oficial de WhatsApp
                const whatsappLink = `https://wa.me/${numero}?text=${encodeURIComponent(mensaje)}`;

                // Redirigir a WhatsApp
                window.location.href = whatsappLink;
            },
            function(error) {
                alert("No se pudo obtener la ubicación: " + error.message);
            }
        );
    } else {
        alert("Tu navegador no soporta geolocalización.");
    }

}