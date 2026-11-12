<script setup lang="ts">
import type { NewsItem, Stat } from '#shared/types/api'

// Slayder tagida, uning pastki qirrasiga qisman chiqib turadigan qabul paneli va so'nggi yangiliklar
const props = defineProps<{ students?: Stat; news: NewsItem[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const latest = computed(() => props.news.slice(0, 3))
</script>

<template>
  <section class="relative z-10 mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:-mt-20 lg:px-8" :aria-label="t('admission.title')">
    <div class="grid gap-5 lg:grid-cols-12">
      <!-- Qabul paneli -->
      <div class="relative overflow-hidden rounded-[1.75rem] bg-brand-900 p-7 text-white shadow-[0_30px_60px_-30px_var(--color-brand-950)] sm:p-8 lg:col-span-7">
        <div class="decor pointer-events-none absolute -top-16 -right-16 grid size-52 place-items-center rounded-full border border-accent-400/40" aria-hidden="true">
          <span class="mt-10 mr-10 font-display text-2xl text-accent-400">1949</span>
        </div>
        <p class="text-xs font-semibold tracking-[0.14em] text-accent-300 uppercase">{{ t('admission.eyebrow') }}</p>
        <h2 class="mt-2 max-w-sm font-display text-3xl leading-tight font-semibold sm:text-4xl">{{ t('admission.title') }}</h2>
        <p class="mt-3 max-w-md text-[15px] leading-relaxed text-white/65">{{ t('admission.text') }}</p>
        <div class="mt-6 flex flex-wrap gap-3">
          <NuxtLink
            :to="localePath('/qabul-20262027')"
            class="group inline-flex items-center gap-2 rounded-full bg-accent-400 px-6 py-3 font-semibold text-ink transition-colors hover:bg-accent-300"
          >
            {{ t('admission.cta') }}
            <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-0.5" />
          </NuxtLink>
          <NuxtLink
            :to="localePath('/bakalavriat')"
            class="inline-flex items-center rounded-full border border-white/30 px-6 py-3 font-semibold text-white transition-colors hover:bg-white/10"
          >
            {{ t('hero.ctaSecondary') }}
          </NuxtLink>
        </div>
        <div v-if="props.students" class="mt-6 inline-flex items-center gap-3 rounded-2xl bg-white/10 px-4 py-3">
          <span class="font-display text-2xl leading-none font-semibold">{{ formatStat(props.students.value).number }}<span class="text-accent-400">{{ formatStat(props.students.value).suffix }}</span></span>
          <span class="text-xs text-white/70">{{ t('hero.students') }}</span>
        </div>
      </div>

      <!-- So'nggi yangiliklar -->
      <div class="rounded-[1.75rem] border border-line bg-white p-6 shadow-[0_30px_60px_-40px_var(--color-brand-900)] lg:col-span-5">
        <div class="flex items-center justify-between gap-3">
          <h2 class="text-base font-semibold text-ink">{{ t('news.title') }}</h2>
          <NuxtLink :to="localePath('/yangiliklar')" class="text-sm font-semibold text-brand-700 hover:text-brand-900">{{ t('news.all') }} →</NuxtLink>
        </div>
        <ul v-if="latest.length" class="mt-3 divide-y divide-line">
          <li v-for="item in latest" :key="item.id">
            <NuxtLink :to="localePath(`/news/${item.slug}`)" class="group flex items-center gap-4 py-3">
              <NewsCover :item="item" :tone="0" class="size-14 shrink-0 rounded-xl" />
              <span class="min-w-0">
                <span class="line-clamp-2 text-[15px] leading-snug font-medium text-ink group-hover:text-brand-700">{{ item.title }}</span>
                <time :datetime="item.date" class="mt-0.5 block text-xs text-muted">{{ formatDate(item.date) }}</time>
              </span>
            </NuxtLink>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
