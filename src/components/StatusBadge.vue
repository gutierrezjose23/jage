<script setup>
defineProps({ status: String })
</script>
<template>
  <span :class="['status-badge', `status-${status}`]">
    <span aria-hidden="true" />
    {{ status }}
  </span>
</template>
