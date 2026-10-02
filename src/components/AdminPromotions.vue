<script setup>
import AppForm from './AppForm.vue'
import { reactive, ref } from 'vue'
import { api } from '../lib/api.js'
import { dateLabel, money, limaToday } from '../lib/format.js'
import FormField from './FormField.vue'
import AlertMessage from './AlertMessage.vue'
defineProps({ promotions: Array })
const emit = defineEmits(['refresh'])
const creating = ref(false)
const busy = ref(false)
const error = ref('')
const success = ref('')
const fields = ref({})
const form = reactive({ title: '', description: '', amount: '', expires_at: '', active: true })
function toggleCreateForm() {
  creating.value = !creating.value
  error.value = ''
}
async function create() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  success.value = ''
  fields.value = {}
  try {
    await api('/admin/promotions', { method: 'POST', body: { ...form } })
    Object.assign(form, { title: '', description: '', amount: '', expires_at: '', active: true })
    creating.value = false
    success.value = 'Promoción publicada. Cada conductor puede canjearla una sola vez.'
    emit('refresh')
  } catch (cause) {
    error.value = cause.message
    fields.value = cause.fields || {}
  } finally {
    busy.value = false
  }
}
async function toggle(promotion) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await api(`/admin/promotions/${promotion.id}`, {
      method: 'PATCH',
      body: { active: !promotion.active },
    })
    success.value = 'Estado de la promoción actualizado.'
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
    <div class="flex justify-between items-center flex-wrap gap-4 mb-6">
      <div>
        <h2 class="panel-title">Promociones para conductores</h2>
        <p class="muted text-sm mt-2">
          Bonos de saldo para cubrir comisiones, con un canje por conductor.
        </p>
      </div>
      <button
        class="btn btn-primary btn-small"
        :disabled="busy"
        @click="toggleCreateForm"
      >
        {{ creating ? 'Cerrar formulario' : 'Crear promoción' }}
      </button>
    </div>
    <AlertMessage :message="error" />
    <AlertMessage
      :message="success"
      type="success"
    />
    <AppForm
      v-if="creating"
      class="surface form-stack mb-6"
      :disabled="busy"
      @submit="create"
    >
      <FormField
        label="Nombre de la promoción"
        v-model="form.title"
        maxlength="120"
        :error="fields.title"
        required
      />
      <FormField
        label="Descripción y condiciones"
        v-model="form.description"
        type="textarea"
        rows="3"
        maxlength="500"
        :error="fields.description"
        required
      />
      <div class="grid gap-5 sm:grid-cols-2">
        <FormField
          label="Bono de saldo (S/)"
          v-model="form.amount"
          type="number"
          inputmode="decimal"
          min="0.01"
          max="100000"
          step="0.01"
          :error="fields.amount"
          required
        />
        <FormField
          label="Fecha de vencimiento"
          v-model="form.expires_at"
          type="date"
          :min="limaToday()"
          :error="fields.expires_at"
          hint="Válida hasta el final de este día, hora de Perú."
          required
        />
      </div>
      <button
        type="submit"
        class="btn btn-primary self-start"
        :disabled="busy"
      >
        {{ busy ? 'Publicando…' : 'Publicar promoción' }}
      </button>
    </AppForm>
    <div
      v-if="promotions.length"
      class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <article
        v-for="promotion in promotions"
        :key="promotion.id"
        class="surface promo-card"
      >
        <div class="flex justify-between gap-3 items-center">
          <span class="promo-amount">{{ money(promotion.amount) }}</span>
          <span
            :class="['status-badge', promotion.active ? 'status-confirmada' : 'status-cancelada']"
          >
            {{ promotion.active ? 'Activa' : 'Pausada' }}
          </span>
        </div>
        <h3>{{ promotion.title }}</h3>
        <p class="muted text-sm whitespace-pre-wrap break-words">{{ promotion.description }}</p>
        <p class="field-hint mt-4">Vence: {{ dateLabel(promotion.expires_at) }}</p>
        <button
          class="btn btn-outline btn-small w-full mt-5"
          :disabled="busy"
          @click="toggle(promotion)"
        >
          {{ promotion.active ? 'Pausar promoción' : 'Activar promoción' }}
        </button>
      </article>
    </div>
    <p
      v-else
      class="empty-state"
    >
      No hay promociones creadas. Las promociones publicadas aparecerán en el espacio de los
      conductores.
    </p>
  </div>
</template>
