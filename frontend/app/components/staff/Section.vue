<script setup lang="ts">
// O'ng tomondagi katta karta: sarlavha + chiziq (+ ixtiyoriy tugma). Hover'da faqat yengil ko'tariladi.
defineProps<{ title: string; active?: boolean }>()
</script>

<template>
  <section
    class="rounded-[28px] border bg-white p-6 transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_24px_50px_-34px_rgba(17,12,46,0.35)] sm:p-7"
    :class="active ? 'border-accent-500' : 'border-line'"
  >
    <div class="flex items-center gap-3.5">
      <h2 class="flex flex-1 items-center gap-3.5 text-xs font-bold tracking-[0.18em] text-accent-600 uppercase">
        {{ title }}
        <span class="h-px flex-1 bg-line" />
      </h2>
      <slot name="action" />
    </div>
    <slot />
  </section>
</template>
