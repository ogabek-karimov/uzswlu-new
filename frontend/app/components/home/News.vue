<script setup lang="ts">
import type { Announcement, NewsItem } from '#shared/types/api'

// Bosh sahifa: «Yangiliklar» (4 karta) va «E'lonlar» (4 afisha) — hozirgi saytdagi tuzilish, yangi dizaynda.
// Kartada BRM maqsadi bo'lsa — rasm burchagida rangli belgi
// show: 'news' — faqat yangiliklar, 'announcements' — faqat e'lonlar (har biri o'z fonida), berilmasa ikkalasi
const props = defineProps<{ news: NewsItem[]; announcements: Announcement[]; show?: 'news' | 'announcements' }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const news = computed(() => props.news.slice(0, 4))
const announcements = computed(() => props.announcements.slice(0, 4))
</script>

<template>
  <!-- Yangiliklar va E'lonlar ketma-ket: oradagi bo'shliq qisqa (yangiliklar pasti va e'lonlar tepasi ixcham), tashqi chetlar avvalgidek -->
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :class="show === 'news' ? 'pt-16 pb-6 lg:pt-20 lg:pb-8' : show === 'announcements' ? 'pt-6 pb-16 lg:pt-8 lg:pb-20' : 'py-16 lg:py-20'">
    <!-- Yangiliklar -->
    <template v-if="show !== 'announcements'">
    <SectionHeading
      :eyebrow="t('news.eyebrow')"
      :title="t('news.title')"
      :link="{ to: localePath('/yangiliklar'), label: t('news.all') }"
    />

    <ul class="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <li data-reveal-item class="group/li" v-for="(item, i) in news" :key="item.id">
        <article data-spot class="group relative flex h-full cursor-pointer flex-col rounded-[26px] border border-line bg-white p-2.5 transition duration-300 group-hover/li:-translate-y-1 hover:border-brand-200 hover:shadow-[0_30px_60px_-34px_rgba(19,17,47,0.45)] motion-reduce:transition-none motion-reduce:group-hover/li:translate-y-0">
          <div class="relative">
            <NewsCover :item="item" :tone="i" class="aspect-[4/3] rounded-[20px]" />
            <!-- Rasm pastidan qorong'i qatlam va shisha sana belgisi -->
            <span class="pointer-events-none absolute inset-x-0 bottom-0 h-1/2 rounded-b-[20px] bg-gradient-to-t from-brand-950/55 to-transparent" aria-hidden="true" />
            <time :datetime="item.date" class="absolute bottom-3 left-3 inline-flex items-center gap-1.5 rounded-full border border-white/30 bg-white/20 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur-md">
              <Icon name="lucide:calendar" class="size-3.5" />
              {{ formatDate(item.date) }}
            </time>
            <span
              v-if="item.sdg"
              class="absolute right-3 bottom-3 grid size-10 place-items-center rounded-xl text-sm font-bold shadow-[0_8px_20px_-8px_rgba(0,0,0,0.5)]"
              :style="{ background: sdgColor(item.sdg), color: sdgInk(item.sdg) }"
              :title="t('news.sdg', { n: item.sdg })"
            >{{ item.sdg }}</span>
          </div>
          <div class="flex flex-1 flex-col px-3 pt-4 pb-2">
            <h3 class="mt-1 line-clamp-3 min-h-[3lh] text-[17px] leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700">
              <NuxtLink :to="localePath(`/news/${item.slug}`)">
                <span class="absolute inset-0" aria-hidden="true" />
                {{ item.title }}
              </NuxtLink>
            </h3>
            <NuxtLink :to="localePath(`/news/${item.slug}`)" tabindex="-1" class="relative z-10 mt-auto flex items-center justify-between pt-5 text-sm font-semibold text-brand-700">
              {{ t('news.readMore') }}
              <span class="grid size-9 place-items-center rounded-full border border-brand-200 transition duration-300 group-hover:-rotate-45 group-hover:border-accent-400 group-hover:bg-accent-400 group-hover:text-ink motion-reduce:transition-none" aria-hidden="true">
                <Icon name="lucide:arrow-right" class="size-4" />
              </span>
            </NuxtLink>
          </div>
          <span class="pointer-events-none absolute inset-x-8 bottom-0 h-1 origin-left scale-x-0 rounded-full bg-accent-400 transition-transform duration-500 group-hover:scale-x-100 motion-reduce:transition-none" aria-hidden="true" />
        </article>
      </li>
    </ul>

    </template>

    <!-- E'lonlar: bosh sahifada o'z fonli bo'limida (HomeBackdrop variant="mint") -->
    <div v-if="announcements.length && show !== 'news'" :class="show !== 'announcements' && 'mt-16'">
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
        <li data-reveal-item class="group/li" v-for="(item, i) in announcements" :key="item.id">
          <article data-spot class="group relative flex h-full cursor-pointer flex-col overflow-hidden rounded-[24px] bg-white shadow-[0_1px_0_rgba(19,17,47,0.04)] transition duration-300 group-hover/li:-translate-y-1 hover:shadow-[0_30px_60px_-34px_rgba(19,17,47,0.5)] motion-reduce:transition-none motion-reduce:group-hover/li:translate-y-0">
            <div class="relative aspect-[4/5] overflow-hidden" :class="!item.image && (i % 2 ? 'bg-brand-100' : 'bg-[#e9ecfd]')">
              <img v-if="item.image" :src="item.image" :alt="item.title" loading="lazy" decoding="async" class="size-full object-cover object-top transition-transform duration-700 group-hover:scale-105 motion-reduce:transition-none">
              <div v-else class="decor absolute inset-0 grid place-items-center" aria-hidden="true">
                <span class="absolute -right-10 -bottom-10 size-44 rounded-full border-[1.75rem] border-brand-600/[0.07]" />
                <Icon name="lucide:megaphone" class="size-14 text-[3.5rem] text-brand-600/70" />
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
              <NuxtLink :to="localePath(`/announcements/${item.slug}`)" tabindex="-1" class="relative z-10 mt-auto inline-flex items-center gap-1.5 pt-4 text-[13px] font-semibold text-brand-700">
                {{ t('news.readMore') }}
                <Icon name="lucide:arrow-up-right" class="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </NuxtLink>
            </div>
          </article>
        </li>
      </ul>
    </div>
  </section>
</template>
