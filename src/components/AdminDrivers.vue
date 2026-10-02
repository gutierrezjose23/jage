<script setup>
import AppForm from './AppForm.vue'
import { reactive, ref } from 'vue'
import { api, operationKey } from '../lib/api.js'
import { money } from '../lib/format.js'
import FormField from './FormField.vue'
import AlertMessage from './AlertMessage.vue'
defineProps({ drivers: Array })
const emit = defineEmits(['refresh'])
const creating = ref(false)
const selected = ref(null)
const busy = ref(false)
const error = ref('')
const success = ref('')
const fields = ref({})
const driverForm = reactive({
  first_name: '',
  last_name: '',
  phone: '',
  dni: '',
  email: '',
  license_plate: '',
  password: '',
})
const adjustment = reactive({ amount: '', reason: '' })
let balanceKey = ''
function toggleCreateForm() {
  creating.value = !creating.value
  selected.value = null
  error.value = ''
  success.value = ''
}
function openAdjustment(driver) {
  creating.value = false
  selected.value = driver
  error.value = ''
  success.value = ''
  adjustment.amount = ''
  adjustment.reason = ''
  balanceKey = operationKey()
}
async function create() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  success.value = ''
  fields.value = {}
  try {
    await api('/admin/drivers', { method: 'POST', body: { ...driverForm } })
    Object.keys(driverForm).forEach((key) => {
      driverForm[key] = ''
    })
    creating.value = false
    success.value =
      'Cuenta de conductor creada. Entrega la contraseña de forma privada al conductor.'
    emit('refresh')
  } catch (cause) {
    error.value = cause.message
    fields.value = cause.fields || {}
  } finally {
    busy.value = false
  }
}
async function adjust() {
  if (busy.value) return
  if (!Number(adjustment.amount)) {
    error.value = 'Escribe un importe diferente de cero.'
    return
  }
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await api(`/admin/drivers/${selected.value.id}/balance`, {
      method: 'POST',
      body: { ...adjustment, idempotency_key: balanceKey },
    })
    selected.value = null
    success.value = 'Ajuste registrado con su motivo en el historial del conductor.'
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
    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="panel-title">Conductores y saldo</h2>
        <p class="muted text-sm mt-2">
          Crea cuentas y registra las recargas o correcciones de saldo.
        </p>
      </div>
      <button
        class="btn btn-primary btn-small"
        :disabled="busy"
        @click="toggleCreateForm"
      >
        {{ creating ? 'Cerrar formulario' : 'Crear conductor' }}
      </button>
    </div>
    <AlertMessage
      :message="success"
      type="success"
    />
    <AlertMessage :message="error" />
    <AppForm
      v-if="creating"
      class="surface form-stack mb-6"
      :disabled="busy"
      @submit="create"
    >
      <h3>Nueva cuenta de conductor</h3>
      <div class="grid gap-5 sm:grid-cols-2">
        <FormField
          label="Nombre"
          v-model="driverForm.first_name"
          maxlength="80"
          :error="fields.first_name"
          required
        />
        <FormField
          label="Apellido"
          v-model="driverForm.last_name"
          maxlength="80"
          :error="fields.last_name"
          required
        />
        <FormField
          label="DNI"
          v-model="driverForm.dni"
          inputmode="numeric"
          autocomplete="off"
          minlength="8"
          maxlength="8"
          pattern="[0-9]{8}"
          hint="Documento de 8 dígitos."
          :error="fields.dni"
          required
        />
        <FormField
          label="Placa del carro"
          v-model="driverForm.license_plate"
          autocomplete="off"
          autocapitalize="characters"
          maxlength="7"
          pattern="[A-Za-z0-9]{3}-?[A-Za-z0-9]{3}"
          placeholder="ABC-123"
          hint="6 letras o números; el guion es opcional."
          :error="fields.license_plate"
          required
        />
        <FormField
          label="Celular"
          v-model="driverForm.phone"
          type="tel"
          maxlength="20"
          pattern="[+0-9 \(\)\-]{7,20}"
          :error="fields.phone"
          required
        />
        <FormField
          label="Correo"
          v-model="driverForm.email"
          type="email"
          maxlength="254"
          :error="fields.email"
          required
        />
      </div>
      <FormField
        label="Contraseña inicial"
        v-model="driverForm.password"
        type="password"
        autocomplete="new-password"
        minlength="12"
        maxlength="128"
        :error="fields.password"
        hint="12 a 128 caracteres. Coordina la contraseña con el conductor por un canal privado."
        required
      />
      <button
        type="submit"
        class="btn btn-primary self-start"
        :disabled="busy"
      >
        {{ busy ? 'Creando…' : 'Crear cuenta de conductor' }}
      </button>
    </AppForm>
    <div class="info-panel mb-6">
      <p>
        El saldo cubre las comisiones de viajes completados. Una recarga manual registra un importe
        recibido o autorizado fuera de la aplicación: aquí no se procesan pagos ni retiros.
      </p>
    </div>
    <AppForm
      v-if="selected"
      class="surface form-stack mb-6"
      :disabled="busy"
      @submit="adjust"
    >
      <h3>Ajustar saldo · {{ selected.first_name }} {{ selected.last_name }}</h3>
      <p class="muted">Saldo al abrir: {{ money(selected.balance) }}</p>
      <div class="grid gap-5 sm:grid-cols-2">
        <FormField
          label="Importe del ajuste (S/)"
          type="number"
          inputmode="decimal"
          v-model="adjustment.amount"
          min="-100000"
          max="100000"
          step="0.01"
          hint="Positivo para recargar; negativo para corregir. No puede dejar saldo negativo."
          required
        />
        <FormField
          label="Motivo o referencia"
          v-model="adjustment.reason"
          minlength="5"
          maxlength="255"
          hint="Incluye una referencia que permita revisar el ajuste."
          required
        />
      </div>
      <p class="pending-note">
        Se registrará {{ money(adjustment.amount) }} en el historial. Verifica el importe y el
        motivo antes de guardar.
      </p>
      <div class="flex gap-3 flex-wrap">
        <button
          type="submit"
          class="btn btn-primary btn-small"
          :disabled="busy"
        >
          {{ busy ? 'Registrando…' : 'Registrar ajuste' }}
        </button>
        <button
          type="button"
          class="btn btn-outline btn-small"
          :disabled="busy"
          @click="selected = null"
        >
          Cerrar
        </button>
      </div>
    </AppForm>
    <div
      v-if="drivers.length"
      class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <article
        v-for="driver in drivers"
        :key="driver.id"
        class="surface driver-card"
      >
        <div class="avatar">
          {{ driver.first_name.slice(0, 1) }}{{ driver.last_name.slice(0, 1) }}
        </div>
        <h3>{{ driver.first_name }} {{ driver.last_name }}</h3>
        <p class="muted break-all text-sm mt-2">{{ driver.email }}</p>
        <p class="muted text-sm">{{ driver.phone }}</p>
        <p class="muted text-sm">DNI: {{ driver.dni || 'Por completar' }}</p>
        <p class="text-sm mt-2">
          Placa:
          <strong>{{ driver.license_plate || 'Por completar' }}</strong>
        </p>
        <div class="driver-balance">
          <span>Saldo para comisiones</span>
          <strong>{{ money(driver.balance) }}</strong>
        </div>
        <button
          class="btn btn-outline btn-small w-full"
          :disabled="busy"
          @click="openAdjustment(driver)"
        >
          Ajustar saldo
        </button>
      </article>
    </div>
    <p
      v-else
      class="empty-state"
    >
      Todavía no hay conductores. Crea una cuenta para empezar a coordinar los viajes.
    </p>
  </div>
</template>
