<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../lib/api.js'
import AccountHeading from '../components/AccountHeading.vue'
import ReservationCard from '../components/ReservationCard.vue'
import AlertMessage from '../components/AlertMessage.vue'
import AppIcon from '../components/AppIcon.vue'
const route = useRoute()
const reservations = ref([])
const loading = ref(true)
const error = ref('')
async function load() {
  loading.value = true
  error.value = ''
  try {
    reservations.value = (await api('/reservations')).reservations
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>
<template>
  <section class="page-shell account-page">
    <AccountHeading
      eyebrow="TU ESPACIO JAGE"
      title="Mis reservas."
      description="Tus próximas rutas y el estado de cada solicitud, en un solo lugar."
    >
      <RouterLink
        to="/reservar"
        class="btn btn-primary"
      >
        Nueva reserva
        <AppIcon />
      </RouterLink>
    </AccountHeading>
    <AlertMessage
      v-if="route.query.creada"
      type="success"
      message="Solicitud recibida como pendiente. JAGE revisará los detalles; el viaje aún no está confirmado."
    />
    <AlertMessage :message="error" />
    <div class="flex justify-end mb-6">
      <button
        class="text-action"
        :disabled="loading"
        @click="load"
      >
        {{ loading ? 'Consultando…' : 'Actualizar reservas' }}
      </button>
    </div>
    <p
      v-if="loading"
      class="loading-state"
      role="status"
    >
      Consultando tus reservas…
    </p>
    <div
      v-else-if="!error && !reservations.length"
      class="empty-state"
    >
      <span class="service-icon">
        <AppIcon
          name="route"
          :size="30"
        />
      </span>
      <h2>Tu próxima ruta empieza aquí.</h2>
      <p>Aún no tienes solicitudes. Cuéntanos a dónde quieres ir.</p>
      <RouterLink
        to="/reservar"
        class="btn btn-primary mt-5"
      >
        Solicitar mi primer viaje
        <AppIcon />
      </RouterLink>
    </div>
    <div
      v-else-if="!error"
      class="grid gap-5 lg:grid-cols-2"
    >
      <ReservationCard
        v-for="reservation in reservations"
        :key="reservation.id"
        :reservation="reservation"
      />
    </div>
    <RouterLink
      v-if="error"
      to="/ingresar"
      class="text-action mt-4"
    >
      Revisar mi sesión
    </RouterLink>
  </section>
</template>
