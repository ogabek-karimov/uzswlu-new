<script setup lang="ts">
import type { VideoList } from '#shared/types/api'

// Video darsliklar (canvas: "Video darsliklar") + onlayn translatsiya kartasi
const { t, locale } = useI18n()
const formatDate = useFormatDate()

const { data } = await useFetch<VideoList>('/api/videos', { key: 'videos', query: { lang: locale } })

const category = ref('')
watchEffect(() => {
  if (!category.value && data.value?.categories[0]) category.value = data.value.categories[0].id
})
const current = computed(() => data.value?.categories.find(c => c.id === category.value))
const items = computed(() => (data.value?.items ?? []).filter(v => v.category === category.value))

// Kartalar fonlari (canvas'dagidek, toifa bo'yicha)
const TONES = [
  { bg: 'bg-brand-800', word: 'text-accent-400/95' },
  { bg: 'bg-accent-100', word: 'text-orange-700' },
  { bg: 'bg-brand-100', word: 'text-brand-700' },
  { bg: 'bg-brand-950', word: 'text-white/90' },
  { bg: 'bg-red-100', word: 'text-red-700' },
]
const tone = computed(() => TONES[Math.max(0, data.value?.categories.findIndex(c => c.id === category.value) ?? 0) % TONES.length]!)

useSeoMeta({ title: () => t('video.title'), description: () => t('video.lead') })
</script>

<template>
  <div v-if="data">
    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
      <PageBreadcrumbs :items="[{ label: t('video.section') }, { label: t('video.title') }]" />
      <div class="mt-7 grid items-stretch gap-8 lg:grid-cols-[1fr_1.3fr]">
        <div class="flex flex-col justify-center">
          <h1 class="font-display text-[2.75rem] leading-[1.04] font-semibold tracking-tight sm:text-6xl lg:text-[64px]">{{ t('video.title') }}</h1>
          <p class="mt-4 text-[19px] leading-relaxed text-muted">{{ t('video.lead') }}</p>
          <a :href="data.channelUrl" target="_blank" rel="noopener" class="mt-6 inline-flex h-12 items-center gap-2 self-start rounded-full border border-ink/20 px-5 font-semibold text-ink transition-colors hover:bg-ink hover:text-white">
            <Icon name="simple-icons:youtube" class="size-5 text-red-600" />
            {{ t('video.channel') }}
          </a>
        </div>

        <!-- Onlayn translatsiya -->
        <a :href="data.live.url" target="_blank" rel="noopener" class="group relative block aspect-video overflow-hidden rounded-[28px] bg-brand-950 text-white">
          <span class="decor pointer-events-none absolute -top-32 -right-20 size-[420px] rounded-full border-[42px] border-white/5" aria-hidden="true" />
          <span class="absolute top-5 left-5 inline-flex items-center gap-2 rounded-full bg-white/12 px-3 py-1.5 text-[13px] font-semibold">
            <span class="size-2 rounded-full" :class="data.live.isLive ? 'animate-pulse bg-red-500' : 'bg-gray-400'" />
            {{ t('video.live') }} · {{ data.live.isLive ? t('video.onAir') : t('video.offAir') }}
          </span>
          <span class="absolute top-1/2 left-1/2 grid size-[88px] -translate-1/2 place-items-center rounded-full bg-accent-400 text-ink transition-transform group-hover:scale-105">
            <Icon name="lucide:play" class="ml-1 size-9" />
          </span>
          <span class="absolute inset-x-6 bottom-5 flex items-end justify-between gap-4">
            <span>
              <span class="block text-[13px] text-white/60">{{ t('video.next') }}</span>
              <span class="mt-0.5 block font-display text-xl font-semibold sm:text-2xl">
                <template v-if="data.live.next">{{ data.live.next.title }} · {{ formatDate(data.live.next.startsAt, 'datetime') }}</template>
                <template v-else>{{ t('video.nextTba') }}</template>
              </span>
            </span>
            <span class="hidden shrink-0 text-[13px] font-semibold text-accent-400 sm:inline">{{ t('video.watch') }} →</span>
          </span>
        </a>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 pt-14 pb-24 sm:px-6 lg:px-8">
      <div role="group" :aria-label="t('video.categories')" class="flex flex-wrap gap-2">
        <button
          v-for="c in data.categories"
          :key="c.id"
          type="button"
          :aria-pressed="category === c.id"
          class="h-12 rounded-full border px-[18px] text-[15px] font-semibold transition-colors"
          :class="category === c.id ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
          @click="category = c.id"
        >
          {{ c.title }}
        </button>
      </div>
      <ul class="mt-7 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <li v-for="v in items" :key="v.id">
          <a :href="v.url" target="_blank" rel="noopener" class="group block text-ink">
            <span class="relative block aspect-video overflow-hidden rounded-[22px]" :class="tone.bg">
              <img v-if="v.thumbnail" :src="v.thumbnail" alt="" loading="lazy" class="size-full object-cover">
              <span v-else-if="current" :lang="current.lang" class="decor absolute bottom-3.5 left-[22px] font-display text-[64px] leading-none font-semibold italic" :class="tone.word" aria-hidden="true">{{ current.greeting }}</span>
              <span class="absolute top-[18px] right-[18px] grid size-[52px] place-items-center rounded-full bg-white/92 text-ink transition-transform group-hover:scale-110" aria-hidden="true">
                <Icon name="lucide:play" class="ml-0.5 size-5" />
              </span>
              <span v-if="v.duration" class="absolute right-[18px] bottom-4 rounded-md bg-black/60 px-2 py-0.5 text-xs font-semibold text-white">{{ v.duration }}</span>
            </span>
            <span class="mt-3.5 block text-lg leading-snug font-semibold transition-colors group-hover:text-brand-700">{{ v.title }}</span>
            <span class="mt-1 block text-sm text-muted">{{ current?.title }}<template v-if="v.teacher"> · {{ v.teacher }}</template></span>
          </a>
        </li>
      </ul>
    </section>
  </div>
</template>
