<script setup lang="ts">
// Eski manzil (yilga bog'langan): /qabul-20262027 → /qabul (doimiy yo'naltirish)
const localePath = useLocalePath()
await navigateTo(localePath(ADMISSION_PATH), { redirectCode: 301, replace: true })
</script>

<template>
  <div />
</template>
