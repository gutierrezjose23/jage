<script setup>
import { useLocation } from '../../ubicacion.js'
import AppIcon from './AppIcon.vue'
import AlertMessage from './AlertMessage.vue'
defineProps({ disabled: Boolean })
const emit = defineEmits(['apply'])
const { coordinates, loading, error, mapUrl, label, requestLocation, clearLocation } = useLocation()
function applyLocation() {
  emit('apply', mapUrl.value)
  clearLocation()
}
</script>
<template>
  <div class="location-picker">
    <button
      type="button"
      class="text-action"
      :disabled="loading || disabled"
      @click="requestLocation"
    >
      <AppIcon
        name="pin"
        :size="18"
      />
      {{ loading ? 'Buscando ubicación…' : 'Usar mi ubicación actual' }}
    </button>
    <p class="field-hint">
      Solo pedimos permiso al pulsar este botón. También puedes escribir el origen.
    </p>
    <AlertMessage :message="error" />
    <div
      v-if="coordinates"
      class="location-preview"
    >
      <p class="font-semibold">Revisa tu punto de partida</p>
      <p class="field-hint mt-2">
        {{ label }} · Precisión aproximada: {{ coordinates.accuracy }} m.
      </p>
      <a
        :href="mapUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="text-action"
      >
        Revisar en Google Maps
        <AppIcon :size="16" />
      </a>
      <div class="flex flex-wrap gap-2 mt-3">
        <button
          class="btn btn-primary btn-small"
          type="button"
          :disabled="disabled"
          @click="applyLocation"
        >
          Usar este origen
        </button>
        <button
          class="btn btn-outline btn-small"
          type="button"
          :disabled="disabled"
          @click="clearLocation"
        >
          Descartar
        </button>
      </div>
      <p class="field-hint mt-3">
        Aún no has compartido tu ubicación. Al usar este origen, podrás revisarlo en el formulario.
      </p>
    </div>
  </div>
</template>
