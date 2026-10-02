<script setup>
defineProps({ eyebrow: String, title: String, description: String })
</script>
<template>
  <header class="account-heading">
    <div>
      <p class="eyebrow muted">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p
        v-if="description"
        class="muted max-w-2xl"
      >
        {{ description }}
      </p>
    </div>
    <slot />
  </header>
</template>
