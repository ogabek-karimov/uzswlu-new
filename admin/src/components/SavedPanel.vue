<script setup lang="ts">
import Icon from './Icon.vue'

// Tahrir oynasi yopiq paytda örnida turadigan karta (Sahifalar).
// idle — hali hec narsa tanlanmagan (kirganda): yöl-yöriq; aks holda — «… saqlandi», qayta tahrirlaş va saytda köriş
defineProps<{ title?: string | null; siteUrl?: string | null; text: string; idle?: boolean }>()
defineEmits<{ reopen: [] }>()
</script>

<template>
  <section v-if="idle" class="card flex min-w-0 flex-[999_1_520px] flex-col items-center border-2 border-dashed border-field! bg-transparent! px-6 py-14 text-center shadow-none!">
    <span class="grid size-14 place-items-center rounded-full bg-brand-50 text-brand-700"><Icon name="edit" :size="24" /></span>
    <h2 class="mt-5 text-[20px] font-bold tracking-tight">Tahrirlaş uçun sahifani tanlang</h2>
    <p class="mt-2 max-w-md text-[15px] leading-relaxed text-muted">Çapdagi röyxatdan sahifani bosing yoki yuqoridagi «Yangi sahifa» tugmasi bilan yangisini yarating.</p>
  </section>
  <section v-else class="card flex min-w-0 flex-[999_1_520px] flex-col items-center px-6 py-14 text-center">
    <span class="grid size-14 place-items-center rounded-full bg-mint text-brand-950 shadow-[0_0_28px_-4px_var(--color-mint)]"><Icon name="check" :size="26" /></span>
    <h2 class="mt-5 text-[22px] font-bold tracking-tight">«{{ title }}» saqlandi</h2>
    <p class="mt-2 max-w-md text-[15px] leading-relaxed text-muted">{{ text }}</p>
    <div class="mt-6 flex flex-wrap justify-center gap-2.5">
      <button type="button" class="btn-ghost" @click="$emit('reopen')">Qayta tahrirlaş</button>
      <a v-if="siteUrl" :href="siteUrl" target="_blank" rel="noopener" class="btn-primary">Saytda köriş ↗</a>
    </div>
  </section>
</template>
