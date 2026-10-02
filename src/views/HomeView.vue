<script setup>
import AppForm from '../components/AppForm.vue'
import { computed, reactive, ref } from 'vue'
import carImage from '../../img/background.png'
import AppIcon from '../components/AppIcon.vue'
import FormField from '../components/FormField.vue'
import LocationPicker from '../components/LocationPicker.vue'
import AlertMessage from '../components/AlertMessage.vue'
import { whatsappUrl } from '../../ubicacion.js'
import { session, accountPath } from '../lib/api.js'
const contact = reactive({ name: '', email: '', origin: '', message: '' })
const prepared = ref(false)
const contactError = ref('')
function applyOrigin(origin) {
  contact.origin = origin
  prepared.value = false
}
function prepareMessage() {
  contactError.value = ''
  if (!contact.name.trim() || !contact.message.trim()) {
    contactError.value = 'Escribe tu nombre y una consulta antes de preparar el mensaje.'
    prepared.value = false
    return
  }
  prepared.value = true
}
const contactMessage = computed(
  () =>
    `Hola JAGE, soy ${contact.name.trim()}.\nCorreo: ${contact.email.trim()}${contact.origin.trim() ? `\nOrigen: ${contact.origin.trim()}` : ''}\n\n${contact.message.trim()}`,
)
const reservationPath = computed(() =>
  session.user && session.user.role !== 'passenger' ? accountPath() : '/reservar',
)
const serviceItems = [
  {
    icon: 'car',
    number: '01',
    title: 'Tu ruta. Tu horario.',
    name: 'Viajes privados',
    copy: 'Un traslado para tus planes. Cuéntanos dónde empieza tu viaje y a dónde quieres llegar.',
    service: 'privado',
  },
  {
    icon: 'route',
    number: '02',
    title: 'Más cerca de tu destino.',
    name: 'Huaral — Lima',
    copy: 'Conecta Huaral y Lima. Coordina tu punto de partida, destino y horario con anticipación.',
    service: 'huaral-lima',
  },
  {
    icon: 'plane',
    number: '03',
    title: 'Tu viaje empieza antes.',
    name: 'Al aeropuerto',
    copy: 'Organiza tu traslado al aeropuerto. Incluye los datos de tu vuelo para coordinar los detalles.',
    service: 'aeropuerto',
  },
]
</script>
<template>
  <section
    class="hero"
    id="inicio"
  >
    <div class="hero-content">
      <p class="eyebrow">
        <span class="live-dot" />
        HUARAL · LIMA · AEROPUERTO
      </p>
      <h1>
        Tu próximo
        <br />
        destino.
        <br />
        <span>Vamos contigo.</span>
      </h1>
      <p class="hero-description">
        Viajes privados que empiezan con una buena coordinación. Tú eliges el destino; juntos
        organizamos el camino.
      </p>
      <div class="hero-actions">
        <RouterLink
          :to="reservationPath"
          class="btn btn-accent"
        >
          Solicitar una reserva
          <AppIcon />
        </RouterLink>
        <RouterLink
          to="/servicios"
          class="hero-link"
        >
          Explorar servicios
          <AppIcon
            name="down"
            :size="17"
          />
        </RouterLink>
      </div>
      <p class="hero-note">
        <AppIcon
          name="clock"
          :size="16"
        />
        Solicitud en línea. Confirmación por JAGE.
      </p>
    </div>
    <div class="hero-image">
      <img
        :src="carImage"
        alt="Automóvil sedán con los faros encendidos para un traslado privado"
        fetchpriority="high"
        width="1536"
        height="1024"
      />
      <div class="hero-image-top">
        <span class="image-tag">EL CAMINO EMPIEZA AQUÍ</span>
        <AppIcon
          name="arrow"
          :size="32"
        />
      </div>
      <div class="hero-image-bottom">
        <div>
          <span class="eyebrow">NUESTRO PUNTO DE PARTIDA</span>
          <p>Huaral, Perú.</p>
        </div>
        <span
          class="coordinate-mark"
          aria-hidden="true"
        >
          DE TU ORIGEN
          <br />
          A TU DESTINO
        </span>
      </div>
    </div>
  </section>
  <div
    class="route-strip"
    aria-label="Servicios JAGE"
  >
    <div class="page-shell">
      <span>Viaja a tu manera</span>
      <span>
        <AppIcon
          name="car"
          :size="18"
        />
        Privados
      </span>
      <span>
        <AppIcon
          name="route"
          :size="18"
        />
        Huaral — Lima
      </span>
      <span>
        <AppIcon
          name="plane"
          :size="18"
        />
        Aeropuerto
      </span>
    </div>
  </div>
  <section
    class="page-shell section-space"
    id="servicios"
    tabindex="-1"
  >
    <div class="section-heading">
      <div>
        <p class="eyebrow muted">01 / ELIGE TU CAMINO</p>
        <h2>
          Un servicio para
          <br />
          cada plan.
        </h2>
      </div>
      <p>
        Una salida, un encuentro o un vuelo.
        <br />
        El primer paso es contarnos a dónde vas.
      </p>
    </div>
    <div class="service-grid">
      <article
        v-for="service in serviceItems"
        :key="service.number"
        class="service-card"
      >
        <div class="service-card-top">
          <span class="service-icon">
            <AppIcon
              :name="service.icon"
              :size="27"
            />
          </span>
          <span class="service-index">{{ service.number }}</span>
        </div>
        <p class="service-tagline">{{ service.title }}</p>
        <h3>{{ service.name }}</h3>
        <p>{{ service.copy }}</p>
        <RouterLink
          :to="`${reservationPath}?servicio=${service.service}`"
          class="service-link"
        >
          Solicitar traslado
          <AppIcon :size="21" />
        </RouterLink>
      </article>
    </div>
  </section>
  <section
    class="process-section"
    id="como-reservar"
    tabindex="-1"
  >
    <div class="page-shell process-grid">
      <div>
        <p class="eyebrow">02 / ASÍ DE SENCILLO</p>
        <h2>
          Menos vueltas.
          <br />
          Más camino.
        </h2>
        <p class="process-copy">
          Organiza tu viaje desde un solo lugar y consulta el estado de tu solicitud cuando lo
          necesites.
        </p>
        <RouterLink
          to="/registro"
          class="btn btn-accent mt-8"
        >
          Crear mi cuenta
          <AppIcon />
        </RouterLink>
      </div>
      <ol class="process-list">
        <li>
          <span>01</span>
          <div>
            <h3>Crea tu cuenta</h3>
            <p>
              Registra tus datos de contacto. Tendrás tu propio espacio para consultar tus reservas.
            </p>
          </div>
        </li>
        <li>
          <span>02</span>
          <div>
            <h3>Cuéntanos tu ruta</h3>
            <p>Elige el servicio, origen, destino, fecha, hora y número de pasajeros.</p>
          </div>
        </li>
        <li>
          <span>03</span>
          <div>
            <h3>Espera la confirmación</h3>
            <p>
              JAGE revisará tu solicitud. Una reserva pendiente todavía no es un viaje confirmado.
            </p>
          </div>
        </li>
      </ol>
    </div>
  </section>
  <section
    class="page-shell section-space contact-grid"
    id="contacto"
    tabindex="-1"
  >
    <div class="contact-copy">
      <p class="eyebrow muted">03 / CONVERSEMOS</p>
      <h2>
        Un mensaje.
        <br />
        El inicio de tu viaje.
      </h2>
      <p>
        ¿Tienes una ruta en mente o una consulta? Cuéntanos los detalles y coordinemos por WhatsApp.
      </p>
      <a
        class="contact-phone"
        href="https://wa.me/51934613286"
        target="_blank"
        rel="noopener noreferrer"
      >
        <span class="service-icon"><AppIcon name="message" /></span>
        <span>
          <small>ESCRÍBENOS</small>
          +51 934 613 286
        </span>
        <AppIcon />
      </a>
      <div class="contact-note">
        <AppIcon
          name="pin"
          :size="20"
        />
        <p>
          Desde Huaral, Perú.
          <br />
          <span>Viajes privados, Lima y aeropuerto.</span>
        </p>
      </div>
    </div>
    <AppForm
      class="surface contact-form"
      @submit="prepareMessage"
      @input="prepared = false"
    >
      <div class="grid gap-5 sm:grid-cols-2">
        <FormField
          label="Tu nombre"
          v-model="contact.name"
          autocomplete="name"
          maxlength="120"
          required
          placeholder="¿Cómo te llamas?"
        />
        <FormField
          label="Correo electrónico"
          v-model="contact.email"
          type="email"
          autocomplete="email"
          maxlength="254"
          required
          placeholder="tucorreo@ejemplo.com"
        />
      </div>
      <FormField
        label="Punto de partida (opcional)"
        v-model="contact.origin"
        maxlength="180"
        placeholder="Escribe una dirección o referencia"
      />
      <LocationPicker @apply="applyOrigin" />
      <FormField
        label="¿En qué podemos ayudarte?"
        v-model="contact.message"
        type="textarea"
        rows="4"
        maxlength="1000"
        required
        placeholder="Cuéntanos sobre tu viaje…"
      />
      <button
        class="btn btn-primary w-full"
        type="submit"
      >
        Preparar mensaje
        <AppIcon name="message" />
      </button>
      <p class="field-hint">
        No se envía nada automáticamente. Abrir WhatsApp prepara el mensaje; tú debes enviarlo.
      </p>
      <AlertMessage :message="contactError" />
      <div
        v-if="prepared"
        class="message-preview"
        role="status"
      >
        <p class="font-semibold mb-3">Revisa tu mensaje</p>
        <p class="whitespace-pre-wrap break-words text-sm">{{ contactMessage }}</p>
        <a
          :href="whatsappUrl(contactMessage)"
          target="_blank"
          rel="noopener noreferrer"
          class="btn btn-accent mt-5"
        >
          Abrir WhatsApp
          <AppIcon />
        </a>
        <p class="field-hint mt-3">
          Una consulta por WhatsApp no registra ni confirma una reserva en la plataforma.
        </p>
      </div>
    </AppForm>
  </section>
  <section class="closing-cta page-shell">
    <div>
      <p class="eyebrow muted">TU SIGUIENTE PARADA</p>
      <h2>Hagamos camino.</h2>
    </div>
    <RouterLink
      :to="reservationPath"
      class="btn btn-primary"
    >
      Solicitar mi reserva
      <AppIcon />
    </RouterLink>
  </section>
</template>
