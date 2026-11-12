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

    <ul ref="scroller" class="mx-auto mt-8 flex max-w-7xl snap-x snap-mandatory gap-4 overflow-x-auto px-4 pt-3 pb-6 [scrollbar-width:none] sm:px-6 lg:px-8">
      <li
        v-for="(lang, i) in languages"
        :key="lang.code"
        :lang="lang.code"
        class="group relative flex h-56 w-64 shrink-0 snap-start flex-col justify-between overflow-hidden rounded-[1.75rem] p-6 transition duration-500 ease-out hover:-translate-y-2 hover:-rotate-1 hover:shadow-[0_28px_50px_-24px_rgba(19,17,47,0.55)] sm:w-72"
        :class="tones[i % tones.length]"
      >
        <!-- Orqa fondagi katta yozuv: kursor kelganda kattalashib buriladi -->
        <span
          class="decor pointer-events-none absolute -right-4 -bottom-10 font-display text-[9rem] leading-none font-semibold whitespace-nowrap opacity-[0.12] transition duration-700 ease-out select-none group-hover:-rotate-6 group-hover:scale-125 group-hover:opacity-25"
          aria-hidden="true"
        >{{ lang.native }}</span>

        <div class="relative flex items-center justify-between">
          <span class="rounded-full border border-current/30 px-2.5 py-0.5 text-xs font-semibold tracking-widest uppercase opacity-80">{{ lang.code }}</span>
          <span class="grid size-9 -translate-x-2 scale-75 place-items-center rounded-full bg-current/15 opacity-0 transition duration-300 group-hover:translate-x-0 group-hover:scale-100 group-hover:opacity-100" aria-hidden="true">
            <Icon name="lucide:arrow-up-right" class="size-4" />
          </span>
        </div>

        <div class="relative">
          <p class="font-display text-4xl leading-none font-semibold sm:text-5xl">{{ lang.native }}</p>
          <ul v-if="lang.faculties || lang.programs" class="mt-4 flex flex-wrap gap-1.5 text-xs font-medium">
            <li v-if="lang.faculties" class="inline-flex items-center gap-1 rounded-full bg-current/10 px-2.5 py-1 transition-colors group-hover:bg-current/20">
              <Icon name="lucide:building-2" class="size-3.5" />{{ t('languages.faculties', { n: lang.faculties }) }}
            </li>
            <li v-if="lang.programs" class="inline-flex items-center gap-1 rounded-full bg-current/10 px-2.5 py-1 transition-colors group-hover:bg-current/20">
              <Icon name="lucide:book-open" class="size-3.5" />{{ t('languages.programs', { n: lang.programs }) }}
            </li>
          </ul>
        </div>
      </li>
    </ul>
  </section>
</template>
