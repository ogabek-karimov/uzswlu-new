<script setup lang="ts">
import type { PostList, PostType } from '#shared/types/api'

// Yangiliklar ro'yxati (canvas: "Yangiliklar ro'yxati"): tablar — yangiliklar / tadbirlar / e'lonlar.
// Filtrlar URL'da saqlanadi: ?type=&q=&month=&page=
const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const TYPES: PostType[] = ['news', 'events', 'announcements']
const PER_PAGE = 12

const str = (v: unknown) => (typeof v === 'string' ? v : '')
const type = computed<PostType>(() => (TYPES as string[]).includes(str(route.query.type)) ? str(route.query.type) as PostType : 'news')
const q = computed(() => str(route.query.q))
const month = computed(() => str(route.query.month))
const page = computed(() => Math.max(1, Number.parseInt(str(route.query.page), 10) || 1))

const { data, status } = await useFetch<PostList>('/api/posts', {
  key: 'posts-list',
  query: { lang: locale, type, q, month, page, perPage: PER_PAGE },
})

function setFilters(patch: { type?: PostType; q?: string; month?: string }) {
  const merged = { type: type.value, q: q.value, month: month.value, ...patch }
  const next: Record<string, string> = {}
  if (merged.type !== 'news') next.type = merged.type
  if (merged.q) next.q = merged.q
  if (merged.month) next.month = merged.month
  router.replace({ query: next })
}

const search = ref(q.value)
let timer: ReturnType<typeof setTimeout> | undefined
watch(search, (value) => {
  clearTimeout(timer)
  timer = setTimeout(() => {
    if (value.trim() !== q.value) setFilters({ q: value.trim() })
  }, 300)
})
watch(q, (value) => {
  if (value !== search.value.trim()) search.value = value
})

// Asosiy yangilik — faqat filtrsiz birinchi sahifada
const showFeatured = computed(() => type.value === 'news' && page.value === 1 && !q.value && !month.value)
const featured = computed(() => (showFeatured.value ? data.value?.items[0] : undefined))
const items = computed(() => (showFeatured.value ? data.value?.items.slice(1) : data.value?.items) ?? [])
const totalPages = computed(() => (data.value ? Math.ceil(data.value.total / data.value.perPage) : 0))

const monthLabel = (m: string) => {
  const name = formatDate(`${m}-15T12:00:00+05:00`, 'month')
  return `${name.charAt(0).toUpperCase()}${name.slice(1)}, ${m.slice(0, 4)}`
}

const results = ref<HTMLElement>()
watch(page, () => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  results.value?.scrollIntoView({ block: 'start', behavior: reduce ? 'auto' : 'smooth' })
})

useSeoMeta({ title: () => t('posts.title'), description: () => t('posts.lead') })
</script>

<template>
  <div>
    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
      <PageBreadcrumbs :items="[{ label: t(`posts.tabs.${type}`) }]" />
      <div class="mt-7 flex flex-wrap items-end justify-between gap-6">
        <h1 class="font-display text-[2.75rem] leading-[1.04] font-semibold tracking-tight text-ink sm:text-6xl lg:text-[64px]">{{ t('posts.title') }}</h1>
        <div role="search" class="flex w-full flex-wrap items-center gap-2.5 sm:w-auto">
          <label class="flex h-12 min-w-0 flex-1 items-center gap-2 rounded-full border border-line bg-white px-4 focus-within:border-accent-600 sm:w-72 sm:flex-none">
            <Icon name="lucide:search" class="size-[18px] shrink-0 text-muted" />
            <span class="sr-only">{{ t('posts.search') }}</span>
            <input v-model="search" type="search" autocomplete="off" :placeholder="t('posts.searchPlaceholder')" class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-muted">
          </label>
          <label class="relative">
            <span class="sr-only">{{ t('posts.month') }}</span>
            <select
              :value="month"
              class="h-12 cursor-pointer appearance-none rounded-full border border-line bg-white pr-10 pl-4 text-[15px] font-medium outline-none focus:border-accent-600"
              @change="setFilters({ month: ($event.target as HTMLSelectElement).value })"
            >
              <option value="">{{ t('posts.allMonths') }}</option>
              <option v-for="m in data?.months ?? []" :key="m" :value="m">{{ monthLabel(m) }}</option>
            </select>
            <Icon name="lucide:chevron-down" class="pointer-events-none absolute top-1/2 right-4 size-4 -translate-y-1/2 text-muted" />
          </label>
        </div>
      </div>

      <div role="tablist" :aria-label="t('posts.typeLabel')" class="mt-7 flex gap-1 overflow-x-auto border-b border-line">
        <button
          v-for="tab in TYPES"
          :key="tab"
          type="button"
          role="tab"
          :aria-selected="type === tab"
          class="-mb-px flex h-[52px] shrink-0 items-center gap-1.5 border-b-[3px] px-4 text-base transition-colors sm:px-5"
          :class="type === tab ? 'border-brand-800 font-semibold text-ink' : 'border-transparent font-medium text-muted hover:text-ink'"
          @click="setFilters({ type: tab, month: '' })"
        >
          {{ t(`posts.tabs.${tab}`) }}
          <span class="rounded-full px-2 py-0.5 text-xs" :class="type === tab ? 'bg-brand-800 text-white' : 'bg-brand-50 text-brand-800'">{{ data?.counts[tab]?.toLocaleString('ru-RU') ?? '' }}</span>
        </button>
      </div>
    </section>

    <!-- Asosiy yangilik -->
    <section v-if="featured" class="mx-auto max-w-7xl px-4 pt-10 sm:px-6 lg:px-8">
      <article class="group relative grid items-center gap-8 lg:grid-cols-[1.3fr_1fr] lg:gap-10">
        <NewsCover :item="featured" :tone="3" class="aspect-[16/10] rounded-[28px]" />
        <div>
          <p class="text-sm text-muted"><time :datetime="featured.date">{{ formatDate(featured.date) }}</time></p>
          <h2 class="mt-3 font-display text-3xl leading-tight font-semibold text-ink sm:text-[38px]">
            <NuxtLink :to="localePath(`/news/${featured.slug}`)">
              <span class="absolute inset-0" aria-hidden="true" />
              {{ featured.title }}
            </NuxtLink>
          </h2>
          <p v-if="featured.excerpt" class="mt-4 line-clamp-4 text-[17px] leading-relaxed text-muted">{{ featured.excerpt }}</p>
          <span class="mt-5 inline-flex items-center gap-2 font-semibold text-brand-700">
            {{ t('posts.read') }}
            <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
          </span>
        </div>
      </article>
    </section>

    <!-- Ro'yxat -->
    <section ref="results" class="mx-auto max-w-7xl scroll-mt-32 px-4 pt-12 sm:px-6 lg:px-8" :aria-busy="status === 'pending'">
      <NuxtLink v-if="type === 'events'" :to="localePath('/events')" class="mb-8 inline-flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-accent-500">
        <Icon name="lucide:calendar-days" class="size-4 text-accent-600" />
        {{ t('posts.calendar') }}
      </NuxtLink>

      <ul v-if="items.length" class="grid gap-x-6 gap-y-10 transition-opacity sm:grid-cols-2 lg:grid-cols-3" :class="status === 'pending' && 'opacity-60'">
        <li v-for="(item, i) in items" :key="item.id">
          <PostCard :item="item" :tone="i" />
        </li>
      </ul>
      <div v-else-if="!featured" class="rounded-[28px] border border-dashed border-brand-200 bg-white px-6 py-16 text-center">
        <Icon name="lucide:newspaper" class="mx-auto size-10 text-brand-300" />
        <p class="mt-4 text-lg font-semibold text-ink">{{ t('posts.empty') }}</p>
        <button v-if="q || month" type="button" class="mt-5 rounded-full bg-brand-900 px-5 py-2.5 text-sm font-semibold text-white" @click="setFilters({ q: '', month: '' })">{{ t('staff.reset') }}</button>
      </div>

      <AppPagination v-if="data" :page="page" :total-pages="totalPages" class="mt-12" />
    </section>

    <!-- Telegram -->
    <section class="mx-auto max-w-7xl px-4 pt-16 pb-24 sm:px-6 lg:px-8">
      <a href="https://t.me/UzSWLU" target="_blank" rel="noopener" class="group flex flex-wrap items-center justify-between gap-5 rounded-[28px] bg-brand-950 px-6 py-7 text-white sm:px-9 sm:py-8">
        <span class="flex items-center gap-4">
          <span class="grid size-14 shrink-0 place-items-center rounded-full bg-accent-400 text-ink">
            <Icon name="simple-icons:telegram" class="size-6" />
          </span>
          <span>
            <span class="block font-display text-2xl font-semibold sm:text-[26px]">{{ t('posts.telegram.title') }}</span>
            <span class="mt-1 block text-white/65">{{ t('posts.telegram.text') }}</span>
          </span>
        </span>
        <span class="inline-flex h-[52px] items-center gap-2 rounded-full border border-white/25 px-6 font-semibold transition-colors group-hover:bg-white group-hover:text-ink">
          {{ t('posts.telegram.cta') }}
          <Icon name="lucide:arrow-right" class="size-4" />
        </span>
      </a>
    </section>
  </div>
</template>
