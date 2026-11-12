<script setup lang="ts">
import type { TaughtLanguage } from '#shared/types/api'

defineProps<{ languages: TaughtLanguage[] }>()

const { t } = useI18n()

// Tillar karuseli: rangli bloklar, gorizontal siljiydi (snap)
const tones = [
  'bg-brand-700 text-white',
  'bg-[#f4e7cf] text-ink',
  'bg-brand-100 text-ink',
  'bg-ink text-white',
  'bg-accent-100 text-ink',
  'bg-accent-400 text-ink',
]

const scroller = ref<HTMLElement>()
function scrollBy(dir: 1 | -1) {
  const el = scroller.value
  if (el) el.scrollBy({ left: dir * (el.clientWidth * 0.8), behavior: 'smooth' })
}
</script>

<template>
  <section class="overflow-hidden py-12 lg:py-16">
    <div class="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4 px-4 sm:px-6 lg:px-8">
      <div class="max-w-2xl">
        <p class="text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">{{ t('languages.eyebrow') }}</p>
        <h2 class="mt-3 font-display text-4xl font-semibold tracking-tight text-ink sm:text-5xl">{{ t('languages.title') }}</h2>
        <p class="mt-3 text-lg text-muted">{{ t('languages.text') }}</p>
      </div>
      <div class="flex gap-2">
        <button type="button" class="grid size-11 cursor-pointer place-items-center rounded-full border border-ink/15 text-ink transition-colors hover:bg-ink hover:text-white" :aria-label="t('languages.prev')" @click="scrollBy(-1)">
          <Icon name="lucide:arrow-left" class="size-5" />
        </button>
        <button type="button" class="grid size-11 cursor-pointer place-items-center rounded-full bg-brand-700 text-white transition-colors hover:bg-brand-800" :aria-label="t('languages.next')" @click="scrollBy(1)">
          <Icon name="lucide:arrow-right" class="size-5" />
        </button>
      </div>
    </div>

    <ul ref="scroller" class="mx-auto mt-8 flex max-w-7xl snap-x snap-mandatory gap-4 overflow-x-auto px-4 pb-2 [scrollbar-width:none] sm:px-6 lg:px-8">
      <li
        v-for="(lang, i) in languages"
        :key="lang.code"
        :lang="lang.code"
        class="flex h-44 w-64 shrink-0 snap-start items-end rounded-[1.75rem] p-6 sm:w-72"
        :class="tones[i % tones.length]"
      >
        <span class="font-display text-4xl leading-none font-semibold sm:text-5xl">{{ lang.native }}</span>
      </li>
    </ul>
  </section>
</template>
