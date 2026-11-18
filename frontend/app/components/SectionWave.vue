<script setup lang="ts">
// Bo'limlar orasidagi egri ajratgich. `top` — bo'lim tepasiga, `bottom` — pastiga yopishadi; rangi — qo'shni (tashqi) fon rangi (`text-*`).
// Ikki qatlam: orqadagisi yarim shaffof va teskari yo'nalishda sekinroq siljiydi — suv chizig'i kabi.
defineProps<{ position: 'top' | 'bottom' }>()
</script>

<template>
  <div
    aria-hidden="true"
    class="decor pointer-events-none absolute inset-x-0 z-[1] h-8 overflow-hidden text-paper sm:h-10 lg:h-12"
    :class="position === 'top' ? 'top-0 -translate-y-px -scale-y-100' : 'bottom-0 translate-y-px'"
  >
    <svg class="wave-b absolute bottom-0 left-0 h-full w-[200%] opacity-50" viewBox="0 0 810 80" preserveAspectRatio="none">
      <path d="M0 44C67 14 135 14 202 44S337 74 405 44S540 14 607 44S742 74 810 44V80H0Z" fill="currentColor" />
    </svg>
    <svg class="wave-a absolute bottom-0 left-0 h-full w-[200%]" viewBox="0 0 810 80" preserveAspectRatio="none">
      <path d="M0 56C67 26 135 26 202 56S337 86 405 56S540 26 607 56S742 86 810 56V80H0Z" fill="currentColor" />
    </svg>
  </div>
</template>
