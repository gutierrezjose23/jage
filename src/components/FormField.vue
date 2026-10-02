<script setup>
import { computed, ref, useAttrs, useId, watch } from 'vue'
import { VSelect, VTextarea, VTextField } from 'vuetify/components'

defineOptions({ inheritAttrs: false })
const props = defineProps({
  label: String,
  modelValue: [String, Number],
  type: { type: String, default: 'text' },
  items: { type: Array, default: () => [] },
  hint: String,
  error: [String, Array],
  required: Boolean,
})
const emit = defineEmits(['update:modelValue'])
const id = useId()
const attrs = useAttrs()
const field = ref(null)
const editedSinceError = ref(false)
const component = computed(() =>
  props.type === 'select' ? VSelect : props.type === 'textarea' ? VTextarea : VTextField,
)
const errorMessages = computed(() => (editedSinceError.value ? [] : props.error || []))

watch(
  () => props.error,
  () => {
    editedSinceError.value = false
  },
)

function updateValue(value) {
  // An API error describes the previous value; let the user correct it immediately.
  editedSinceError.value = true
  emit('update:modelValue', value ?? '')
}

function validate(value) {
  const text = String(value ?? '')
  if (props.required && !text.trim()) return 'Completa este campo.'
  if (!text) return true

  if (props.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) {
    return 'Escribe un correo válido.'
  }
  if (attrs.minlength != null && text.length < Number(attrs.minlength)) {
    return `Usa al menos ${attrs.minlength} caracteres.`
  }
  if (attrs.maxlength != null && text.length > Number(attrs.maxlength)) {
    return `Usa como máximo ${attrs.maxlength} caracteres.`
  }
  if (attrs.pattern) {
    try {
      if (!new RegExp(`^(?:${attrs.pattern})$`, 'u').test(text)) {
        return 'Revisa el formato de este campo.'
      }
    } catch {
      // Like native inputs, ignore malformed patterns instead of breaking the form.
    }
  }
  if (props.type === 'number') {
    const number = Number(text)
    if (!Number.isFinite(number)) return 'Escribe un número válido.'
    if (attrs.min != null && number < Number(attrs.min)) {
      return `El valor mínimo es ${attrs.min}.`
    }
    if (attrs.max != null && number > Number(attrs.max)) {
      return `El valor máximo es ${attrs.max}.`
    }
    const step = attrs.step == null ? 1 : Number(attrs.step)
    if (attrs.step !== 'any' && step > 0) {
      const base = Number(attrs.min ?? attrs.value ?? 0)
      const increments = (number - base) / step
      if (Math.abs(increments - Math.round(increments)) > 1e-7) {
        return `Usa incrementos de ${step}.`
      }
    }
  }
  return true
}
</script>
<template>
  <component
    :is="component"
    ref="field"
    v-bind="$attrs"
    :id="attrs.id || id"
    class="jage-field"
    :label="label"
    :model-value="modelValue"
    :type="type === 'select' || type === 'textarea' ? undefined : type"
    :items="type === 'select' ? items : undefined"
    :required="required"
    :aria-required="required"
    :aria-invalid="field?.isValid === false ? 'true' : undefined"
    :rules="[validate, ...(attrs.rules || [])]"
    :error-messages="errorMessages"
    :hint="hint"
    :persistent-hint="!!hint"
    @update:model-value="updateValue"
  />
</template>
