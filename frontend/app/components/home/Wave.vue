<script setup lang="ts">
// Bo'limlar orasidagi suv chizig'i: ikki qavat to'lqin qarama-qarshi yo'nalishda oqadi. Rangi — `text-*` (currentColor).
// `flip` — to'lqin tepaga qaragan (bo'limning pastki chetida) ko'rinishidan teskari (tepa chetida)
defineProps<{ flip?: boolean }>()
</script>

<template>
  <div class="decor pointer-events-none absolute inset-x-0 h-11 overflow-hidden lg:h-[70px]" :class="flip ? 'top-0 [transform:scaleY(-1)]' : 'bottom-0'" aria-hidden="true">
    <svg class="bg-wave-b absolute bottom-0 left-0 h-full w-[200%] opacity-50" viewBox="0 0 810 80" preserveAspectRatio="none"><path d="M0 44C67 14 135 14 202 44S337 74 405 44S540 14 607 44S742 74 810 44V80H0Z" fill="currentColor" /></svg>
    <svg class="bg-wave-a absolute bottom-0 left-0 h-full w-[200%]" viewBox="0 0 810 80" preserveAspectRatio="none"><path d="M0 56C67 26 135 26 202 56S337 86 405 56S540 26 607 56S742 86 810 56V80H0Z" fill="currentColor" /></svg>
  </div>
</template>
