<script setup lang="ts">
import type { Announcement, NewsItem } from '#shared/types/api'

const props = defineProps<{ news: NewsItem[]; announcements: Announcement[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const featured = computed(() => props.news[0])
const rest = computed(() => props.news.slice(1, 4))
</script>

<template>
  <section class="border-t border-line bg-white">
    <div class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <SectionHeading
        :eyebrow="t('news.eyebrow')"
        :title="t('news.title')"
        :link="{ to: localePath('/yangiliklar'), label: t('news.all') }"
      />

      <div class="mt-12 grid gap-10 lg:grid-cols-12">
        <div class="grid gap-x-6 gap-y-10 sm:grid-cols-3 lg:col-span-8">
          <article v-if="featured" class="group relative sm:col-span-3">
            <NewsCover :item="featured" :tone="0" class="aspect-[2/1] rounded-3xl" />
            <div class="mt-5 max-w-2xl">
              <time :datetime="featured.date" class="text-sm text-muted">{{ formatDate(featured.date) }}</time>
              <h3 class="mt-2 font-display text-3xl leading-tight font-semibold text-ink sm:text-4xl">
                <NuxtLink :to="localePath(`/news/${featured.slug}`)" class="bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size] duration-300 group-hover:bg-[length:100%_2px]">
                  <span class="absolute inset-0" aria-hidden="true" />
                  {{ featured.title }}
                </NuxtLink>
              </h3>
            </div>
          </article>

          <article v-for="(item, i) in rest" :key="item.id" class="group relative">
            <NewsCover :item="item" :tone="i + 1" class="aspect-[4/3] rounded-2xl" />
            <time :datetime="item.date" class="mt-4 block text-sm text-muted">{{ formatDate(item.date) }}</time>
            <h3 class="mt-1.5 text-lg leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700">
              <NuxtLink :to="localePath(`/news/${item.slug}`)">
                <span class="absolute inset-0" aria-hidden="true" />
                {{ item.title }}
              </NuxtLink>
            </h3>
          </article>
        </div>

        <aside class="self-start rounded-3xl bg-brand-50 p-6 sm:p-8 lg:col-span-4">
          <h3 class="flex items-center gap-3 text-xl font-semibold text-ink">
            <span class="grid size-10 place-items-center rounded-xl bg-brand-800 text-accent-400">
              <Icon name="lucide:megaphone" class="size-5" />
            </span>
            {{ t('news.announcements') }}
          </h3>

          <ul class="mt-6 divide-y divide-brand-200/60">
            <li v-for="item in announcements" :key="item.id" class="group relative flex gap-4 py-5 first:pt-0">
              <time :datetime="item.date" class="flex w-14 shrink-0 flex-col items-center rounded-xl bg-white py-2 text-center shadow-sm">
                <span class="font-display text-2xl leading-none font-semibold text-brand-800">{{ formatDate(item.date, 'day') }}</span>
                <span class="mt-1 text-[11px] font-medium text-muted uppercase">{{ formatDate(item.date, 'monthShort') }}</span>
              </time>
              <NuxtLink :to="localePath(`/announcements/${item.slug}`)" class="line-clamp-3 text-[15px] leading-snug font-medium text-ink transition-colors group-hover:text-brand-700">
                <span class="absolute inset-0" aria-hidden="true" />
                {{ item.title }}
              </NuxtLink>
            </li>
          </ul>

          <NuxtLink :to="localePath('/announcements')" class="group mt-2 inline-flex items-center gap-2 text-sm font-semibold text-brand-800">
            {{ t('news.allAnnouncements') }}
            <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
          </NuxtLink>
        </aside>
      </div>
    </div>
  </section>
</template>
