<script setup lang="ts">
import AppToaster from './components/AppToaster.vue'
import SessionExpiredModal from './components/SessionExpiredModal.vue'
</script>

<template>
  <RouterView />
  <SessionExpiredModal />
  <AppToaster />
</template>
