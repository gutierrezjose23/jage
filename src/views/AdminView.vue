<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../lib/api.js'
import AccountHeading from '../components/AccountHeading.vue'
import AlertMessage from '../components/AlertMessage.vue'
import AdminReservations from '../components/AdminReservations.vue'
import AdminDrivers from '../components/AdminDrivers.vue'
import AdminPromotions from '../components/AdminPromotions.vue'
const active = ref('reservations')
const reservations = ref([])
const drivers = ref([])
const promotions = ref([])
const loading = ref(true)
const error = ref('')
const hasLoaded = ref(false)
const tabs = [
  { id: 'reservations', name: 'Reservas' },
  { id: 'drivers', name: 'Conductores y saldo' },
  { id: 'promotions', name: 'Promociones' },
]
async function load() {
  loading.value = true
  error.value = ''
  try {
    const [bookings, people, promos] = await Promise.all([
      api('/admin/reservations'),
      api('/admin/drivers'),
      api('/admin/promotions'),
    ])
    reservations.value = bookings.reservations
    drivers.value = people.drivers
    promotions.value = promos.promotions
    hasLoaded.value = true
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
      eyebrow="CENTRO DE OPERACIONES"
      title="Administración."
      description="Coordina solicitudes, conductores y comisiones desde tu espacio de trabajo."
    >
      <button
        class="btn btn-outline btn-small"
        :disabled="loading"
        @click="load"
      >
        {{ loading ? 'Actualizando…' : 'Actualizar datos' }}
      </button>
    </AccountHeading>
    <div
      class="account-tabs"
      aria-label="Secciones de administración"
    >
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: active === tab.id }"
        :aria-pressed="active === tab.id"
        @click="active = tab.id"
      >
        {{ tab.name }}
      </button>
    </div>
    <AlertMessage :message="error" />
    <p
      v-if="loading && !hasLoaded"
      class="loading-state"
      role="status"
    >
      Consultando información…
    </p>
    <template v-else-if="!error">
      <AdminReservations
        v-if="active === 'reservations'"
        :reservations="reservations"
        :drivers="drivers"
        @refresh="load"
      />
      <AdminDrivers
        v-if="active === 'drivers'"
        :drivers="drivers"
        @refresh="load"
      />
      <AdminPromotions
        v-if="active === 'promotions'"
        :promotions="promotions"
        @refresh="load"
      />
    </template>
  </section>
</template>
