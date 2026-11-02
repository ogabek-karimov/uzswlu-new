<script setup lang="ts">
// E'lonlar ro'yxati — yangiliklar sahifasining "E'lonlar" tabi
const localePath = useLocalePath()
await navigateTo({ path: localePath('/yangiliklar'), query: { type: 'announcements' } }, { redirectCode: 301, replace: true })
</script>

<template>
  <div />
</template>
