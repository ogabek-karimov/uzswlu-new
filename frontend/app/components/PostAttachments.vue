<script setup lang="ts">
import type { Attachment } from '#shared/types/api'

// Maqola ostidagi PDF'lar — har biri admin tanlagan ko'rinishda (canvas: "Komponent — PDF ko'rinishi"):
// link — faqat nomi (AVTOREFERAT), embed — ramka ichida, open/download — karta
defineProps<{ items: Attachment[] }>()
const { t } = useI18n()
</script>

<template>
  <div v-if="items.length" class="mt-9 flex flex-col gap-4">
    <template v-for="(a, i) in items" :key="i">
      <!-- Matn-havola: masalan, dissertatsiya e'lonidagi AVTOREFERAT -->
      <p v-if="a.display === 'link'" class="py-1 text-center">
        <a :href="a.url" target="_blank" rel="noopener" class="text-xl font-extrabold tracking-wide text-brand-800 underline decoration-2 underline-offset-[6px] transition hover:text-brand-600">{{ a.title }}</a>
      </p>

      <!-- Ichi ko'rinadi: o'z ramkasida aylantiriladi -->
      <figure v-else-if="a.display === 'embed'" class="overflow-hidden rounded-[22px] border border-line bg-white">
        <figcaption class="flex flex-wrap items-center gap-3 border-b border-line px-[18px] py-3.5">
          <span aria-hidden="true" class="grid h-11 w-9 shrink-0 place-items-center rounded-lg bg-red-50 text-[10px] font-extrabold text-red-700">PDF</span>
          <span class="min-w-0 flex-[1_1_220px]"><span class="block font-semibold text-ink">{{ a.title }}</span><span v-if="a.meta" class="mt-0.5 block text-[13px] text-muted">{{ a.meta }}</span></span>
          <a :href="a.url" target="_blank" rel="noopener" class="inline-flex h-10 items-center rounded-full border border-line px-3.5 text-[13px] font-semibold text-ink hover:border-brand-300">{{ t('pdf.fullscreen') }} ⤢</a>
          <a :href="a.url" download class="inline-flex h-10 items-center rounded-full bg-brand-800 px-4 text-[13px] font-semibold text-white hover:bg-brand-900">{{ t('pdf.download') }} ↓</a>
        </figcaption>
        <iframe
          :src="`${a.url}#view=FitH`" :title="t('pdf.viewer', { title: a.title })" loading="lazy"
          class="block w-full bg-[#ECEAF3]" :style="{ height: `${a.height ?? 680}px` }"
        />
      </figure>

      <!-- Karta: bosib ochiladi yoki yuklab olinadi -->
      <a
        v-else :href="a.url" target="_blank" rel="noopener" :download="a.display === 'download' ? '' : undefined"
        class="flex items-center gap-4 rounded-[18px] border border-line bg-white px-[18px] py-4 text-ink transition hover:border-brand-300"
      >
        <span aria-hidden="true" class="grid h-[52px] w-11 shrink-0 place-items-center rounded-[10px] bg-red-50 text-[10px] font-extrabold text-red-700">PDF</span>
        <span class="min-w-0 flex-1"><span class="block font-semibold">{{ a.title }}</span><span v-if="a.meta" class="mt-0.5 block text-[13px] text-muted">{{ a.meta }}</span></span>
        <span
          class="inline-flex h-10 shrink-0 items-center rounded-full px-4 text-[13px] font-semibold"
          :class="a.display === 'download' ? 'bg-brand-800 text-white' : 'border border-brand-800 text-brand-800'"
        >{{ a.display === 'download' ? `${t('pdf.download')} ↓` : `${t('pdf.open')} ↗` }}</span>
      </a>
    </template>
  </div>
</template>
