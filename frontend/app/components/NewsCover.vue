<script setup lang="ts">
import type { NewsItem } from '#shared/types/api'

const props = defineProps<{ item: NewsItem; tone?: number }>()

// Rasm bo'lmaganda chiqadigan bezak muqova (backend rasm bersa, rasm ko'rsatiladi)
const tones = [
  { bg: 'bg-brand-800', ring: 'border-white/10', glyph: 'text-accent-400' },
  { bg: 'bg-accent-100', ring: 'border-accent-400/30', glyph: 'text-accent-600' },
  { bg: 'bg-brand-100', ring: 'border-brand-300/40', glyph: 'text-brand-700' },
  { bg: 'bg-brand-950', ring: 'border-white/10', glyph: 'text-brand-300' },
]

const tone = computed(() => tones[(props.tone ?? 0) % tones.length]!)
</script>

<template>
  <div class="relative overflow-hidden" :class="!item.image && tone.bg">
    <img v-if="item.image" :src="item.image" :alt="item.title" loading="lazy" decoding="async" class="size-full object-cover transition-transform duration-500 group-hover:scale-105">
    <div v-else class="decor absolute inset-0 transition-transform duration-500 group-hover:scale-105" aria-hidden="true">
      <span class="absolute -right-[15%] -bottom-[40%] aspect-square w-[80%] rounded-full border-[2.5rem]" :class="tone.ring" />
      <span class="absolute -right-[5%] -bottom-[20%] aspect-square w-[45%] rounded-full border-[1.25rem]" :class="tone.ring" />
      <span class="absolute top-[12%] left-[8%] font-display text-[clamp(4rem,12vw,9rem)] leading-none font-semibold" :class="tone.glyph">“</span>
    </div>
    <span v-if="item.category" class="absolute top-4 left-4 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-ink backdrop-blur">
      {{ item.category }}
    </span>
  </div>
</template>
