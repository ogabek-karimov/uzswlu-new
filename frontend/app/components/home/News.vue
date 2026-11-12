<script setup lang="ts">
import type { Announcement, NewsItem } from '#shared/types/api'

// Bosh sahifa: «Yangiliklar» (4 karta) va «E'lonlar» (4 afisha) — hozirgi saytdagi tuzilish, yangi dizaynda.
// Kartada BRM maqsadi bo'lsa — rasm burchagida rangli belgi
const props = defineProps<{ news: NewsItem[]; announcements: Announcement[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const news = computed(() => props.news.slice(0, 4))
const announcements = computed(() => props.announcements.slice(0, 4))
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 lg:py-20">
    <!-- Yangiliklar -->
    <SectionHeading
      :eyebrow="t('news.eyebrow')"
      :title="t('news.title')"
      :link="{ to: localePath('/yangiliklar'), label: t('news.all') }"
    />

    <ul class="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <li v-for="(item, i) in news" :key="item.id">
        <article class="group relative flex h-full flex-col rounded-[26px] border border-line bg-white p-2.5 transition duration-300 hover:-translate-y-1 hover:border-brand-200 hover:shadow-[0_30px_60px_-34px_rgba(19,17,47,0.45)] motion-reduce:transition-none motion-reduce:hover:translate-y-0">
          <div class="relative">
            <NewsCover :item="item" :tone="i" class="aspect-[4/3] rounded-[20px]" />
            <span
              v-if="item.sdg"
              class="absolute right-3 bottom-3 grid size-10 place-items-center rounded-xl text-sm font-bold shadow-[0_8px_20px_-8px_rgba(0,0,0,0.5)]"
              :style="{ background: sdgColor(item.sdg), color: sdgInk(item.sdg) }"
              :title="t('news.sdg', { n: item.sdg })"
            >{{ item.sdg }}</span>
          </div>
          <div class="flex flex-1 flex-col px-3 pt-4 pb-2">
            <time :datetime="item.date" class="inline-flex items-center gap-1.5 text-[13px] font-medium text-accent-600">
              <Icon name="lucide:calendar" class="size-3.5" />
              {{ formatDate(item.date) }}
            </time>
            <h3 class="mt-2 line-clamp-3 min-h-[3lh] text-[17px] leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700">
              <NuxtLink :to="localePath(`/news/${item.slug}`)">
                <span class="absolute inset-0" aria-hidden="true" />
                {{ item.title }}
              </NuxtLink>
            </h3>
            <span class="mt-auto flex items-center justify-between pt-5 text-sm font-semibold text-brand-700">
              {{ t('news.readMore') }}
              <span class="grid size-9 place-items-center rounded-full border border-brand-200 transition duration-300 group-hover:-rotate-45 group-hover:border-accent-400 group-hover:bg-accent-400 group-hover:text-ink motion-reduce:transition-none" aria-hidden="true">
                <Icon name="lucide:arrow-right" class="size-4" />
              </span>
            </span>
          </div>
        </article>
      </li>
    </ul>

    <!-- E'lonlar: afishalar alohida «doska»da -->
    <div v-if="announcements.length" class="mt-16 rounded-[32px] bg-brand-50 p-5 sm:p-8 lg:p-10">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <h2 class="flex items-center gap-3 font-display text-3xl font-semibold text-ink sm:text-4xl">
          <span class="grid size-11 place-items-center rounded-2xl bg-brand-800 text-xl text-accent-400">
            <Icon name="lucide:megaphone" class="size-5" />
          </span>
          {{ t('news.announcements') }}
        </h2>
        <NuxtLink :to="localePath('/announcements')" class="group inline-flex items-center gap-2 rounded-full border border-brand-200 bg-white px-5 py-2.5 text-sm font-semibold text-brand-800 transition-colors hover:border-brand-400">
          {{ t('news.allAnnouncements') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
        </NuxtLink>
      </div>

      <ul class="mt-8 grid grid-cols-2 gap-4 sm:gap-5 lg:grid-cols-4">
        <li v-for="(item, i) in announcements" :key="item.id">
          <article class="group relative flex h-full flex-col overflow-hidden rounded-[24px] bg-white shadow-[0_1px_0_rgba(19,17,47,0.04)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_-34px_rgba(19,17,47,0.5)] motion-reduce:transition-none motion-reduce:hover:translate-y-0">
            <div class="relative aspect-[4/5] overflow-hidden" :class="!item.image && (i % 2 ? 'bg-brand-800' : 'bg-brand-950')">
              <img v-if="item.image" :src="item.image" :alt="item.title" loading="lazy" decoding="async" class="size-full object-cover object-top transition-transform duration-700 group-hover:scale-105 motion-reduce:transition-none">
              <div v-else class="decor absolute inset-0 grid place-items-center" aria-hidden="true">
                <span class="absolute -right-10 -bottom-10 size-44 rounded-full border-[1.75rem] border-white/5" />
                <Icon name="lucide:megaphone" class="size-14 text-[3.5rem] text-accent-400/80" />
              </div>
              <!-- Varaqli taqvim ko'rinishidagi sana -->
              <time :datetime="item.date" class="absolute top-3 left-3 w-14 overflow-hidden rounded-xl bg-white text-center shadow-[0_10px_24px_-12px_rgba(0,0,0,0.55)]">
                <span class="block bg-accent-400 py-0.5 text-[10px] font-bold tracking-wider text-ink uppercase">{{ formatDate(item.date, 'monthShort') }}</span>
                <span class="block py-1 font-display text-2xl leading-none font-semibold text-ink">{{ formatDate(item.date, 'day') }}</span>
              </time>
              <span
                v-if="item.sdg"
                class="absolute top-3 right-3 grid size-9 place-items-center rounded-xl text-[13px] font-bold"
                :style="{ background: sdgColor(item.sdg), color: sdgInk(item.sdg) }"
                :title="t('news.sdg', { n: item.sdg })"
              >{{ item.sdg }}</span>
            </div>
            <div class="flex flex-1 flex-col p-4 sm:p-5">
              <h3 class="line-clamp-3 min-h-[3lh] text-[15px] leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700 sm:text-base">
                <NuxtLink :to="localePath(`/announcements/${item.slug}`)">
                  <span class="absolute inset-0" aria-hidden="true" />
                  {{ item.title }}
                </NuxtLink>
              </h3>
              <span class="mt-auto inline-flex items-center gap-1.5 pt-4 text-[13px] font-semibold text-brand-700">
                {{ t('news.readMore') }}
                <Icon name="lucide:arrow-up-right" class="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </span>
            </div>
          </article>
        </li>
      </ul>
    </div>
  </section>
</template>
