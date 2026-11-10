<script setup lang="ts">
import type { SearchKind, SearchResults } from '#shared/types/api'

// Qidiruv natijalari (canvas: "Qidiruv natijalari"). So'rov URL'da: /search?q=&type=&page=
const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const KINDS: SearchKind[] = ['pages', 'news', 'documents']
const str = (v: unknown) => (typeof v === 'string' ? v : '')
const q = computed(() => str(route.query.q).trim())
const type = computed(() => (KINDS as string[]).includes(str(route.query.type)) ? str(route.query.type) as SearchKind : '')
const page = computed(() => Math.max(1, Number.parseInt(str(route.query.page), 10) || 1))

const { data, status } = await useFetch<SearchResults>('/api/search', {
  key: 'search',
  query: { lang: locale, q, type, page },
})

const input = ref(q.value)
watch(q, value => (input.value = value))

function submit() {
  const value = input.value.trim()
  router.push({ query: value ? { q: value } : {} })
}
const setType = (value: SearchKind | '') => router.replace({ query: { q: q.value, ...(value ? { type: value } : {}) } })

const all = computed(() => (data.value ? data.value.counts.pages + data.value.counts.news + data.value.counts.documents : 0))
const totalPages = computed(() => (data.value ? Math.ceil(data.value.total / data.value.perPage) : 0))

// Topilgan so'zlarni ajratib ko'rsatish (HTML'siz — matn bo'laklari)
const escapeRe = (v: string) => v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
function highlight(text: string) {
  const terms = q.value.split(/\s+/).filter(w => w.length > 1).map(escapeRe)
  if (!terms.length) return [{ text, hit: false }]
  const split = new RegExp(`(${terms.join('|')})`, 'gi')
  const exact = new RegExp(`^(?:${terms.join('|')})$`, 'i')
  return text.split(split).filter(Boolean).map(part => ({ text: part, hit: exact.test(part) }))
}

const isInternal = (url: string) => url.startsWith('/')
const NuxtLink = resolveComponent('NuxtLink')

useSeo({ title: () => (q.value ? `${q.value} — ${t('search.title')}` : t('search.title')), noindex: true })
</script>

<template>
  <div>
    <section class="mx-auto max-w-[960px] px-4 pt-12 sm:px-6 lg:px-8">
      <h1 class="font-display text-5xl font-semibold">{{ t('search.title') }}</h1>
      <form role="search" class="mt-5" @submit.prevent="submit">
        <label for="search-q" class="sr-only">{{ t('search.label') }}</label>
        <div class="flex h-16 items-center gap-2.5 rounded-[20px] border-2 border-brand-800 bg-white pr-2 pl-5">
          <Icon name="lucide:search" class="size-[22px] shrink-0 text-brand-800" />
          <input id="search-q" v-model="input" type="search" autocomplete="off" :placeholder="t('nav.searchPlaceholder')" class="h-full min-w-0 flex-1 bg-transparent text-lg font-medium outline-none sm:text-xl">
          <button type="submit" class="h-12 shrink-0 rounded-[14px] bg-ink px-5 text-[15px] font-semibold text-white transition-colors hover:bg-brand-800">{{ t('search.submit') }}</button>
        </div>
      </form>

      <div v-if="q && data" role="tablist" :aria-label="t('search.types')" class="mt-6 flex flex-wrap gap-2 text-sm font-semibold">
        <button
          v-for="kind in (['', ...KINDS] as const)"
          :key="kind"
          type="button"
          role="tab"
          :aria-selected="type === kind"
          class="rounded-full border px-4 py-2.5 transition-colors"
          :class="type === kind ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
          @click="setType(kind)"
        >
          {{ kind ? t(`search.kinds.${kind}`) : t('search.all') }} · {{ kind ? data.counts[kind] : all }}
        </button>
      </div>
    </section>

    <section class="mx-auto max-w-[960px] px-4 pt-8 pb-24 sm:px-6 lg:px-8" :aria-busy="status === 'pending'">
      <template v-if="q && data">
        <!-- Tezkor javob -->
        <NuxtLink v-if="data.quick && !type && page === 1" :to="localePath(data.quick.url)" class="group flex flex-wrap items-center gap-5 rounded-3xl bg-brand-900 px-7 py-6 text-white">
          <span class="grid size-14 shrink-0 place-items-center rounded-2xl bg-accent-400 text-ink"><Icon name="lucide:zap" class="size-6" /></span>
          <span class="min-w-0 flex-[1_1_300px]">
            <span class="block text-xs font-semibold tracking-[0.16em] text-accent-400 uppercase">{{ t('search.quick') }}</span>
            <span class="mt-1 block font-display text-[28px] font-semibold">{{ data.quick.title }}</span>
            <span class="mt-1 block text-white/70">{{ data.quick.text }}</span>
          </span>
          <span class="font-semibold text-accent-400">{{ t('search.open') }} →</span>
        </NuxtLink>

        <ol v-if="data.items.length" class="mt-7">
          <li v-for="item in data.items" :key="item.url + item.title" class="border-b border-line py-[22px] last:border-0">
            <p class="text-[13px] text-muted">
              {{ t(`search.kinds.${item.kind}`) }} · {{ item.meta }}<template v-if="item.date"> · {{ formatDate(item.date) }}</template>
            </p>
            <component
              :is="isInternal(item.url) ? NuxtLink : 'a'"
              v-bind="isInternal(item.url) ? { to: localePath(item.url) } : { href: item.url, target: '_blank', rel: 'noopener' }"
              class="mt-1.5 block text-[21px] leading-snug font-semibold text-brand-800 hover:underline hover:underline-offset-4"
            >
              <template v-for="(part, i) in highlight(item.title)" :key="i"><mark v-if="part.hit" class="rounded bg-accent-100 px-0.5 text-ink">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template>
            </component>
            <p v-if="item.excerpt" class="mt-1.5 line-clamp-2 text-[15px] leading-relaxed text-muted">
              <template v-for="(part, i) in highlight(item.excerpt)" :key="i"><mark v-if="part.hit" class="rounded bg-accent-100 px-0.5 text-ink">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template>
            </p>
          </li>
        </ol>
        <div v-else class="mt-7 rounded-3xl border border-dashed border-brand-200 bg-white px-6 py-14 text-center">
          <Icon name="lucide:search-x" class="mx-auto size-10 text-brand-300" />
          <p class="mt-4 text-lg font-semibold">{{ t('search.empty', { q }) }}</p>
          <p class="mt-1 text-muted">{{ t('search.emptyHint') }}</p>
        </div>

        <AppPagination :page="page" :total-pages="totalPages" class="mt-8" />
      </template>

      <div class="mt-8 rounded-[22px] bg-brand-50 p-6">
        <p class="font-semibold">{{ t('search.notFound') }}</p>
        <p class="mt-1.5 text-[15px] text-muted">
          {{ t('search.popular') }}
          <NuxtLink :to="localePath('/qabul-20262027')" class="font-semibold text-brand-700 hover:underline">{{ t('admission.title') }}</NuxtLink> ·
          <NuxtLink :to="localePath('/bakalavriat')" class="font-semibold text-brand-700 hover:underline">{{ t('programs.bachelor.name') }}</NuxtLink> ·
          <NuxtLink :to="localePath('/stipendiyalar')" class="font-semibold text-brand-700 hover:underline">{{ t('search.scholarships') }}</NuxtLink> ·
          <NuxtLink :to="localePath('/aloqa') + '#appeal'" class="font-semibold text-brand-700 hover:underline">{{ t('contact.form.title') }}</NuxtLink>
        </p>
      </div>
    </section>
  </div>
</template>
