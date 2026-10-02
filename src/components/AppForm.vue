<script setup>
import { nextTick, ref } from 'vue'
import { VForm } from 'vuetify/components'

const emit = defineEmits(['submit'])
const form = ref(null)
const validating = ref(false)

async function submit(event) {
  if (validating.value) return
  validating.value = true
  try {
    const { valid } = await event
    await nextTick()
    const element = form.value?.$el
    if (!element) return
    if (!valid) {
      element.querySelector('.v-input--error input, .v-input--error textarea')?.focus()
      return
    }
    // Keep native date, time, number range and step validation alongside Vuetify rules.
    if (element.reportValidity()) emit('submit', event)
  } finally {
    validating.value = false
  }
}
</script>
<template>
  <VForm
    ref="form"
    validate-on="blur invalid-input lazy"
    @submit.prevent="submit"
  >
    <slot />
  </VForm>
</template>
