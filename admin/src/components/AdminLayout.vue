<script setup lang="ts">
import { ref } from 'vue'
import AppFooter from './AppFooter.vue'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const menuOpen = ref(false)
</script>

<template>
  <div class="flex min-h-dvh">
    <AppSidebar :open="menuOpen" @close="menuOpen = false" />
    <div class="flex min-w-0 flex-1 flex-col">
      <AppTopbar @menu="menuOpen = true" />
      <main class="flex-1 px-4 pt-6 pb-14 sm:px-8">
        <RouterView />
      </main>
      <AppFooter />
    </div>
  </div>
</template>
