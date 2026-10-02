<script setup>
import AppForm from './AppForm.vue'
import { computed, reactive, ref } from 'vue'
import { api } from '../lib/api.js'
import { statuses, money } from '../lib/format.js'
import ReservationCard from './ReservationCard.vue'
import FormField from './FormField.vue'
import AlertMessage from './AlertMessage.vue'
const props = defineProps({ reservations: Array, drivers: Array })
const emit = defineEmits(['refresh'])
const filter = ref('')
const selected = ref(null)
const busy = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({ status: '', driver_id: '', commission: '' })
const filterOptions = [
  { title: 'Todos los estados', value: '' },
  ...statuses.map((value) => ({ title: value, value })),
]
const driverOptions = computed(() => [
  { title: 'Sin asignar', value: '' },
  ...props.drivers.map((driver) => ({
    value: driver.id,
    title: `${driver.first_name} ${driver.last_name}${driver.license_plate ? ` · ${driver.license_plate}` : ''} — ${money(driver.balance)}`,
  })),
])
const filtered = computed(() =>
  props.reservations.filter((item) => !filter.value || item.status === filter.value),
)
const transitions = {
  pendiente: ['pendiente', 'confirmada', 'cancelada'],
  confirmada: ['confirmada', 'completada', 'cancelada'],
  completada: ['completada'],
  cancelada: ['cancelada'],
}
function edit(item) {
  selected.value = item.id
  error.value = ''
  success.value = ''
  Object.assign(form, {
    status: item.status,
    driver_id: item.driver_id || '',
    commission: item.commission ?? '',
  })
}
async function save() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await api(`/admin/reservations/${selected.value}`, {
      method: 'PATCH',
      body: {
        status: form.status,
        driver_id: form.driver_id ? Number(form.driver_id) : null,
        commission: form.commission === '' ? null : form.commission,
      },
    })
    selected.value = null
    success.value =
      'Reserva actualizada. La comisión se descuenta una sola vez al completar el viaje.'
    emit('refresh')
  } catch (cause) {
    error.value = cause.message
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-5 mb-6">
      <div>
        <h2 class="panel-title">Solicitudes de viaje</h2>
        <p class="muted text-sm mt-2">Confirma, coordina y actualiza cada reserva.</p>
      </div>
      <FormField
        label="Filtrar por estado"
        type="select"
        v-model="filter"
        :items="filterOptions"
      />
    </div>
    <AlertMessage
      :message="success"
      type="success"
    />
    <p
      v-if="!filtered.length"
      class="empty-state"
    >
      No hay reservas para este estado.
    </p>
    <div class="grid gap-5 xl:grid-cols-2">
      <ReservationCard
        v-for="reservation in filtered"
        :key="reservation.id"
        :reservation="reservation"
      >
        <div class="admin-reservation-details">
          <p>
            <strong>Cliente:</strong>
            {{ reservation.user?.first_name }}
            {{ reservation.user?.last_name }}
          </p>
          <p class="break-all">{{ reservation.user?.email }} · {{ reservation.user?.phone }}</p>
          <p>
            <strong>Conductor:</strong>
            {{
              reservation.driver
                ? `${reservation.driver.first_name} ${reservation.driver.last_name}`
                : 'Sin asignar'
            }}
          </p>
          <p>
            <strong>Comisión:</strong>
            {{ reservation.commission === null ? 'Por definir' : money(reservation.commission) }}
            <span v-if="reservation.commission_charged">· Descontada</span>
          </p>
        </div>
        <button
          v-if="
            selected !== reservation.id && !['completada', 'cancelada'].includes(reservation.status)
          "
          class="btn btn-outline btn-small mt-5"
          @click="edit(reservation)"
        >
          Gestionar reserva
        </button>
        <AppForm
          v-if="selected === reservation.id"
          class="form-stack reservation-edit"
          :disabled="busy"
          @submit="save"
        >
          <AlertMessage :message="error" />
          <FormField
            label="Estado"
            type="select"
            v-model="form.status"
            required
            :items="transitions[reservation.status].map((value) => ({ title: value, value }))"
          />
          <FormField
            label="Asignar conductor"
            type="select"
            v-model="form.driver_id"
            :items="driverOptions"
          />
          <FormField
            label="Comisión de este viaje (S/)"
            type="number"
            inputmode="decimal"
            v-model="form.commission"
            min="0"
            max="100000"
            step="0.01"
            hint="Importe fijo a descontar del saldo al completar el viaje. Puede ser 0."
          />
          <p
            v-if="form.status === 'completada'"
            class="pending-note"
          >
            Al guardar, se descontará {{ money(form.commission) }} del conductor asignado. El saldo
            debe cubrir la comisión. Un viaje completado no podrá modificarse.
          </p>
          <p
            v-if="form.status === 'cancelada'"
            class="pending-note"
          >
            Una reserva cancelada no podrá reabrirse. No se descontará comisión.
          </p>
          <div class="flex flex-wrap gap-3">
            <button
              type="submit"
              class="btn btn-primary btn-small"
              :disabled="busy"
            >
              {{ busy ? 'Guardando…' : 'Guardar cambios' }}
            </button>
            <button
              class="btn btn-outline btn-small"
              type="button"
              :disabled="busy"
              @click="selected = null"
            >
              Volver
            </button>
          </div>
        </AppForm>
      </ReservationCard>
    </div>
  </div>
</template>
