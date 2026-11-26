<script setup lang="ts">
import type { VideoList } from '#shared/types/api'

// Video darsliklar (canvas: "Video darsliklar"); onlayn translatsiya — alohida sahifada (/online-translatsiya)
const { t, locale } = useI18n()

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

useSeo({ title: () => t('video.title'), description: () => t('video.lead') })
</script>

<template>
  <div v-if="data">
    <!-- Yuqori qism — boshqa sahifalar (masalan, Online translatsiya) kabi gradient banner; translatsiya videosi olib tashlangan -->
    <section class="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
      <div class="page-hero px-5 py-6 sm:px-8 sm:py-7">
        <PageBreadcrumbs dark :items="[{ label: t('video.section') }, { label: t('video.title') }]" />
        <div class="mt-4 flex flex-wrap items-end justify-between gap-5">
          <div class="max-w-[820px] min-w-0">
            <h1 class="font-display text-[2.25rem] leading-[1.06] font-semibold tracking-tight text-white sm:text-5xl lg:text-[52px]">{{ t('video.title') }}</h1>
            <p class="mt-3 text-base leading-relaxed text-white/75 sm:text-lg">{{ t('video.lead') }}</p>
          </div>
          <div class="no-print flex flex-wrap gap-2">
            <a :href="data.channelUrl" target="_blank" rel="noopener" class="hero-btn inline-flex h-11 items-center gap-2 rounded-full px-4 text-sm font-semibold">
              <Icon name="simple-icons:youtube" class="size-[18px]" />
              {{ t('video.channel') }}
            </a>
          </div>
        </div>
      </div>
    </section>

    <div class="mx-auto flex max-w-7xl flex-col gap-10 px-4 pt-12 pb-24 sm:px-6 lg:flex-row lg:items-start lg:px-8">
      <SectionSideNav />
      <section class="order-1 min-w-0 flex-1 lg:order-2">
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
      <ul v-reveal class="mt-7 grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        <li data-reveal-item v-for="v in items" :key="v.id">
          <a :href="v.url" target="_blank" rel="noopener" class="group block text-ink">
            <span class="relative block aspect-video overflow-hidden rounded-[22px]" :class="tone.bg">
              <img v-if="v.thumbnail" :src="v.thumbnail" alt="" loading="lazy" decoding="async" class="size-full object-cover">
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
    <SectionNav />
  </div>
</template>
