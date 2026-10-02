<script setup>
import AppForm from '../components/AppForm.vue'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../lib/api.js'
import { services, limaToday, isFutureTrip } from '../lib/format.js'
import AccountHeading from '../components/AccountHeading.vue'
import FormField from '../components/FormField.vue'
import AlertMessage from '../components/AlertMessage.vue'
import LocationPicker from '../components/LocationPicker.vue'
import AppIcon from '../components/AppIcon.vue'
const route = useRoute()
const router = useRouter()
const serviceOptions = Object.entries(services).map(([value, title]) => ({ value, title }))
const form = reactive({
  service: Object.hasOwn(services, route.query.servicio || '') ? route.query.servicio : '',
  origin: '',
  destination: '',
  travel_date: '',
  travel_time: '',
  passengers: '1',
  notes: '',
})
const error = ref('')
const fields = ref({})
const busy = ref(false)
async function submit() {
  if (busy.value) return
  error.value = ''
  fields.value = {}
  if (!isFutureTrip(form.travel_date, form.travel_time)) {
    error.value = 'Elige una fecha y hora futuras, en hora de Perú.'
    fields.value.travel_time = error.value
    return
  }
  busy.value = true
  try {
    await api('/reservations', {
      method: 'POST',
      body: {
        ...form,
        origin: form.origin.trim(),
        destination: form.destination.trim(),
        notes: form.notes.trim(),
        passengers: Number(form.passengers),
      },
    })
    await router.push({ path: '/mis-reservas', query: { creada: '1' } })
  } catch (cause) {
    error.value = cause.message
    fields.value = cause.fields || {}
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <section class="page-shell account-page">
    <AccountHeading
      eyebrow="ORGANICEMOS TU VIAJE"
      title="¿A dónde vamos?"
      description="Completa los detalles y envía tu solicitud. JAGE revisará la disponibilidad para confirmarla."
    />
    <div class="booking-grid">
      <AppForm
        class="surface form-stack"
        :disabled="busy"
        @submit="submit"
      >
        <AlertMessage :message="error" />
        <FormField
          label="Servicio"
          type="select"
          v-model="form.service"
          :error="fields.service"
          required
          :items="serviceOptions"
        />
        <FormField
          label="Origen"
          v-model="form.origin"
          maxlength="180"
          :error="fields.origin"
          placeholder="Dirección o punto de referencia"
          required
        />
        <LocationPicker
          :disabled="busy"
          @apply="form.origin = $event"
        />
        <FormField
          label="Destino"
          v-model="form.destination"
          maxlength="180"
          :error="fields.destination"
          placeholder="¿A dónde te llevamos?"
          required
        />
        <div class="grid gap-5 sm:grid-cols-2">
          <FormField
            label="Fecha de viaje"
            type="date"
            v-model="form.travel_date"
            :min="limaToday()"
            :error="fields.travel_date"
            required
          />
          <FormField
            label="Hora de salida"
            type="time"
            v-model="form.travel_time"
            :error="fields.travel_time"
            hint="Hora de Perú (UTC−5)."
            required
          />
        </div>
        <FormField
          label="Número de pasajeros"
          type="number"
          v-model="form.passengers"
          min="1"
          max="8"
          step="1"
          inputmode="numeric"
          :error="fields.passengers"
          hint="De 1 a 8 pasajeros. La capacidad se coordina al confirmar."
          required
        />
        <FormField
          label="Observaciones (opcional)"
          type="textarea"
          v-model="form.notes"
          rows="4"
          maxlength="1000"
          :error="fields.notes"
          placeholder="Equipaje, número de vuelo o detalles para coordinar."
        />
        <button
          type="submit"
          class="btn btn-primary w-full"
          :disabled="busy"
        >
          {{ busy ? 'Enviando solicitud…' : 'Enviar solicitud de reserva' }}
          <AppIcon />
        </button>
        <p class="field-hint">No se realiza ningún cobro al enviar esta solicitud.</p>
      </AppForm>
      <aside class="booking-aside">
        <span class="service-icon">
          <AppIcon
            name="route"
            :size="28"
          />
        </span>
        <h2>
          Primero coordinamos.
          <br />
          Después viajamos.
        </h2>
        <ol>
          <li>Envías los detalles de tu viaje.</li>
          <li>JAGE revisa la solicitud y coordina contigo.</li>
          <li>Consultas la confirmación en Mis reservas.</li>
        </ol>
        <p class="pending-note">
          El estado inicial será
          <strong>pendiente</strong>
          . Espera la confirmación antes de dar el viaje por reservado.
        </p>
        <RouterLink
          to="/mis-reservas"
          class="text-action"
        >
          Ver mis reservas
          <AppIcon :size="16" />
        </RouterLink>
      </aside>
    </div>
  </section>
</template>
