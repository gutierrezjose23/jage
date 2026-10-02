<script setup>
defineProps({
  name: { type: String, default: 'arrow' },
  size: { type: [Number, String], default: 20 },
})
const paths = {
  arrow: 'M7 17 17 7M7 7h10v10',
  next: 'M4 12h16m-6-6 6 6-6 6',
  pin: 'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0ZM15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
  car: 'm5 7 2-4h10l2 4M3 8h18v10H3V8ZM6 18v3m12-3v3M6 12h2m8 0h2',
  plane: 'm22 2-7 20-4-9-9-4L22 2ZM11 13 22 2',
  route: 'M5 5h10a4 4 0 0 1 0 8H9a4 4 0 0 0 0 8h10M5 2v6m14 10v6',
  check: 'm5 12 4 4L19 6',
  clock: 'M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
  user: 'M20 21v-2a7 7 0 0 0-14 0v2M17 7a5 5 0 1 1-10 0 5 5 0 0 1 10 0Z',
  menu: 'M4 6h16M4 12h16M4 18h16',
  close: 'm6 6 12 12M6 18 18 6',
  message: 'M21 11a9 9 0 0 1-9 9 10 10 0 0 1-4-1l-6 3 2-6a9 9 0 1 1 17-5Z',
  wallet: 'M20 7H5a3 3 0 0 1 0-6h13v6M2 4v15a3 3 0 0 0 3 3h15V7m-4 5h6v6h-6v-6Z',
  down: 'M12 4v16m-6-6 6 6 6-6',
}
</script>
<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name] || paths.arrow" />
  </svg>
</template>
