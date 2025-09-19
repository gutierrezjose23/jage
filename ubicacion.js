document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("btn-ubicacion");
    const mensajeUbicacion = document.getElementById("mensaje-ubicacion");
        console.log("Botón de ubicación presionado1");

    btn.addEventListener("click", () => {
        console.log("Botón de ubicación presionado2");
        // if (navigator.geolocation) {
        //     navigator.geolocation.getCurrentPosition(
        //         function(position) {
        //             const lat = position.coords.latitude;
        //             const lon = position.coords.longitude;

        //             // Link de Google Maps
        //             const link = `https://www.google.com/maps?q=${lat},${lon}`;

        //             // Número en formato internacional
        //             const numero = "51934613286";

        //             // Detectar si es iPhone/iPad
        //             const esIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);

        //             // Generar link para WhatsApp
        //             let whatsappLink;
        //             if (esIOS) {
        //                 whatsappLink = `https://api.whatsapp.com/send?phone=${numero}&text=${encodeURIComponent("Hola, esta es mi ubicación: " + link)}`;
        //             } else {
        //                 whatsappLink = `https://wa.me/${numero}?text=${encodeURIComponent("Hola, esta es mi ubicación: " + link)}`;
        //             }

        //             // Mostrar mensaje en pantalla (opcional)
        //             mensajeUbicacion.textContent = "Ubicación detectada, abriendo WhatsApp...";

        //             // Redirigir a WhatsApp (funciona mejor que window.open en móviles)
        //             window.location.href = whatsappLink;
        //         },
        //         function(error) {
        //             alert("No se pudo obtener la ubicación: " + error.message);
        //         }
        //     );
        // } else {
        //     alert("Tu navegador no soporta Geolocalización.");
        // }
    });
});
