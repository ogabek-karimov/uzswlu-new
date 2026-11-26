<script setup lang="ts">
// Menyu havolasining belgisi — barça menyularda bir xil: yumşoq fonli kvadrat, içida sahifa belgisi (admin → Sahifalar → «Belgi»).
// Belgisi yöq sahifada — böliming umumiy belgisi. Hover'da (ota element `group/link`) fon töq indigo, belgi mint.
defineProps<{ icon?: string | null; group?: string; small?: boolean }>()
</script>

<template>
  <span
    class="grid shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-700 transition-colors group-hover/link:bg-brand-800 group-hover/link:text-accent-400"
    :class="small ? 'size-8' : 'size-9'"
    aria-hidden="true"
  >
    <Icon v-if="icon" :name="`lucide:${icon}`" :class="small ? 'size-5 text-xl' : 'size-6 text-2xl'" />
    <NavGroupIcon v-else :id="group ?? ''" :class="small ? 'size-4' : 'size-[18px]'" />
  </span>
</template>
