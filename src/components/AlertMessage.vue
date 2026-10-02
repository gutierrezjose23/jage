<script setup>
defineProps({ type: { type: String, default: 'error' }, message: String })
</script>
<template>
  <div
    v-if="message"
    :class="['alert', `alert-${type}`]"
    :role="type === 'error' ? 'alert' : 'status'"
  >
    {{ message }}
  </div>
</template>
