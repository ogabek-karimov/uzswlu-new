<script setup lang="ts">
import type { PostList, PostType, SdgGoal, SdgOverview } from '#shared/types/api'

// BRM maqsad sahifasi (canvas: "BRM maqsad sahifasi — BRM 6"). Manzillar saytdagidek: /brm-6-toza-suv-va-sanitariya
const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const n = computed(() => Number.parseInt(String(route.params.slug ?? ''), 10))
if (!(n.value >= 1 && n.value <= 17)) {
  throw createError({ statusCode: 404, statusMessage: 'Goal not found', fatal: true })
}

const [{ data: goal, error }, { data: overview }] = await Promise.all([
  useFetch<SdgGoal>(() => `/api/sdg/${n.value}`, { query: { lang: locale } }),
  useFetch<SdgOverview>('/api/sdg', { key: 'sdg', query: { lang: locale } }),
])
if (error.value || !goal.value) {
  throw createError({ statusCode: error.value?.statusCode ?? 404, statusMessage: 'Goal not found', fatal: true })
}

// Eski yoki noto'g'ri slug — asosiy manzilga
if (route.path !== localePath(goal.value.url)) {
  await navigateTo({ path: localePath(goal.value.url), query: route.query }, { redirectCode: 301, replace: true })
}

const goals = computed(() => overview.value?.goals ?? [])
const prev = computed(() => goals.value.find(g => g.n === n.value - 1))
const next = computed(() => goals.value.find(g => g.n === n.value + 1))
const reportLinks = computed(() => (overview.value?.reports ?? []).filter((r, i, all) => r.url.startsWith('/') && all.findIndex(x => x.url === r.url) === i))

const tab = ref(0)
const section = computed(() => goal.value?.sections[tab.value])

// Faoliyat: shu maqsadga bog'langan yangiliklar / tadbirlar / e'lonlar (10 tadan, sahifalab)
const TYPES: PostType[] = ['news', 'events', 'announcements']
const str = (v: unknown) => (typeof v === 'string' ? v : '')
const type = computed<PostType>(() => (TYPES as string[]).includes(str(route.query.type)) ? str(route.query.type) as PostType : 'news')
const page = computed(() => Math.max(1, Number.parseInt(str(route.query.page), 10) || 1))
const { data: posts } = await useFetch<PostList>('/api/posts', {
  key: `sdg-posts-${n.value}`,
  query: { lang: locale, sdg: n, type, page, perPage: 10 },
})
const totalPages = computed(() => (posts.value ? Math.ceil(posts.value.total / posts.value.perPage) : 0))
const setType = (value: PostType) => router.replace({ query: value === 'news' ? {} : { type: value } })

useSeoMeta({
  title: () => (goal.value ? `${t('sdg.goal.short', { n: goal.value.n })}. ${goal.value.title}` : ''),
  description: () => goal.value?.subtitle,
})
</script>

<template>
  <div v-if="goal">
    <!-- Maqsad boshi: BMT rangida -->
    <section data-a11y-keep class="relative overflow-hidden" :style="{ background: sdgColor(goal.n), color: sdgInk(goal.n) }">
      <span class="decor pointer-events-none absolute right-10 -bottom-28 font-display text-[clamp(16rem,40vw,28rem)] leading-none font-bold opacity-20" aria-hidden="true">{{ goal.n }}</span>
      <div class="relative mx-auto max-w-7xl px-4 pt-8 pb-14 sm:px-6 lg:px-8">
        <nav :aria-label="t('nav.breadcrumb')" class="text-sm">
          <ol class="flex flex-wrap items-center gap-2">
            <li><NuxtLink :to="localePath('/')" class="opacity-80 hover:opacity-100">{{ t('nav.home') }}</NuxtLink></li>
            <li aria-hidden="true" class="opacity-50">/</li>
            <li><NuxtLink :to="localePath('/brm')" class="opacity-80 hover:opacity-100">{{ t('sdg.crumb') }}</NuxtLink></li>
            <li aria-hidden="true" class="opacity-50">/</li>
            <li aria-current="page" class="font-semibold">{{ t('sdg.goal.short', { n: goal.n }) }}</li>
          </ol>
        </nav>
        <div class="mt-9 flex flex-wrap items-end gap-10">
          <div class="min-w-0 flex-[1_1_520px]">
            <p class="text-[13px] font-bold tracking-[0.18em] uppercase">{{ t('sdg.goal.eyebrow', { n: goal.n }) }}</p>
            <h1 class="mt-3 font-display text-5xl leading-none font-semibold sm:text-[68px]">{{ goal.title }}</h1>
            <p class="mt-[18px] max-w-xl text-[19px] leading-normal">{{ goal.subtitle }}</p>
          </div>
          <dl class="grid w-full flex-[0_1_520px] gap-3 sm:grid-cols-2">
            <div v-if="goal.highlight" class="flex flex-col-reverse gap-1.5 rounded-[22px] bg-brand-950 p-5 text-white">
              <dt class="text-[13px] text-white/70">{{ goal.highlight.label }}</dt>
              <dd class="font-display text-[26px] leading-tight font-semibold [overflow-wrap:anywhere] text-accent-400 lg:text-[30px]">{{ goal.highlight.value }}</dd>
            </div>
            <div class="flex flex-col-reverse gap-1.5 rounded-[22px] bg-white/55 p-5 text-ink">
              <dt class="text-[13px]">THE Impact {{ overview?.impactYear }}<template v-if="goal.score"> · {{ t('sdg.goal.points', { n: goal.score }) }}</template></dt>
              <dd class="font-display text-[26px] leading-tight font-semibold lg:text-[30px]">{{ goal.rank ?? t('sdg.notRanked') }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>

    <div class="mx-auto flex max-w-7xl flex-col gap-12 px-4 pt-12 pb-24 sm:px-6 lg:flex-row lg:items-start lg:px-8">
      <!-- BRM 1–17 menyusi -->
      <aside class="order-2 lg:sticky lg:top-36 lg:order-1 lg:w-[280px] lg:shrink-0">
        <p class="mb-2.5 text-xs font-semibold tracking-[0.16em] text-muted uppercase">{{ t('sdg.goal.goals') }}</p>
        <ul class="grid gap-0.5 sm:grid-cols-2 lg:grid-cols-1">
          <li v-for="g in goals" :key="g.n">
            <NuxtLink
              :to="localePath(g.url)"
              :aria-current="g.n === goal.n ? 'page' : undefined"
              class="flex items-center gap-2.5 rounded-xl px-2.5 py-[7px] text-sm transition-colors"
              :class="g.n === goal.n ? 'bg-white font-bold text-ink shadow-[0_6px_18px_-10px_rgba(19,17,47,0.35)]' : 'text-muted hover:bg-white hover:text-ink'"
            >
              <span class="grid size-7 shrink-0 place-items-center rounded-lg text-[13px] font-extrabold" :style="{ background: sdgColor(g.n), color: sdgInk(g.n) }">{{ g.n }}</span>
              <span class="min-w-0 truncate">{{ g.title }}</span>
            </NuxtLink>
          </li>
        </ul>
        <template v-if="reportLinks.length">
          <p class="mt-[22px] mb-2.5 text-xs font-semibold tracking-[0.16em] text-muted uppercase">{{ t('sdg.reports') }}</p>
          <ul class="flex flex-col gap-0.5 text-sm">
            <li v-for="r in reportLinks" :key="r.url"><NuxtLink :to="localePath(r.url)" class="block rounded-xl px-2.5 py-2 text-ink hover:bg-white">{{ r.title }}</NuxtLink></li>
          </ul>
        </template>
      </aside>

      <div class="order-1 min-w-0 flex-1 lg:order-2">
        <!-- Ichki bo'limlar -->
        <div v-if="goal.sections.length > 1" role="tablist" :aria-label="t('sdg.goal.sections', { n: goal.n })" class="flex flex-wrap gap-2">
          <button
            v-for="(s, i) in goal.sections"
            :id="`sdg-tab-${s.id}`"
            :key="s.id"
            type="button"
            role="tab"
            :aria-selected="tab === i"
            :aria-controls="`sdg-panel`"
            class="h-11 rounded-full border px-4 text-sm font-semibold transition-colors"
            :class="tab === i ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
            @click="tab = i"
          >
            {{ s.title }}
          </button>
        </div>
        <div v-if="section" id="sdg-panel" role="tabpanel" :aria-labelledby="goal.sections.length > 1 ? `sdg-tab-${section.id}` : undefined" class="mt-5 rounded-[26px] border border-line bg-white p-6 sm:p-7">
          <h2 class="font-display text-[32px] font-semibold">{{ section.title }}</h2>
          <ProseHtml :html="section.body" class="mt-3" />
          <div v-if="section.images.length" class="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <img v-for="src in section.images" :key="src" :src="src" alt="" loading="lazy" class="aspect-[4/3] w-full rounded-2xl object-cover">
          </div>
        </div>

        <!-- Hujjatlar -->
        <template v-if="goal.documents.length">
          <h2 class="mt-12 font-display text-[34px] font-semibold">{{ t('sdg.goal.documents') }}</h2>
          <ul class="mt-[18px] flex flex-col gap-2.5">
            <li v-for="(d, i) in goal.documents" :key="i" class="flex flex-wrap items-center gap-4 rounded-[18px] border border-line bg-white px-[18px] py-4">
              <span class="grid h-[52px] w-11 shrink-0 place-items-center rounded-[10px] bg-red-50 text-[10px] font-extrabold text-red-700">{{ d.kind === 'pdf' ? 'PDF' : 'URL' }}</span>
              <span class="min-w-0 flex-[1_1_240px]">
                <span class="block font-semibold">{{ d.title }}</span>
                <span v-if="d.meta" class="mt-0.5 block text-[13px] text-muted">{{ d.meta }}</span>
              </span>
              <a :href="d.url" target="_blank" rel="noopener" class="inline-flex h-10 items-center rounded-full bg-brand-800 px-4 text-[13px] font-semibold text-white transition-colors hover:bg-brand-700">{{ t('page.download') }} ↓</a>
            </li>
          </ul>
        </template>

        <!-- Faoliyat -->
        <div class="mt-12 flex flex-wrap items-end justify-between gap-4">
          <h2 class="font-display text-[34px] font-semibold">{{ t('sdg.goal.activity', { n: goal.n }) }}</h2>
          <div role="group" class="flex gap-1.5 text-sm font-semibold">
            <button
              v-for="ty in TYPES"
              :key="ty"
              type="button"
              :aria-pressed="type === ty"
              class="rounded-full border px-3.5 py-2 transition-colors"
              :class="type === ty ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
              @click="setType(ty)"
            >
              {{ t(`posts.tabs.${ty}`) }} <span class="opacity-60">{{ posts?.counts[ty] ?? '' }}</span>
            </button>
          </div>
        </div>
        <ul v-if="posts?.items.length" class="mt-[18px]">
          <li v-for="(item, i) in posts.items" :key="item.id" class="group relative flex items-center gap-4 border-t border-line py-4">
            <NewsCover :item="item" :tone="i" class="h-[76px] w-28 shrink-0 rounded-[14px] [&>span]:hidden" />
            <span class="min-w-0">
              <time :datetime="item.date" class="block text-[13px] text-muted">{{ formatDate(item.date) }}</time>
              <NuxtLink :to="localePath(`/${item.type}/${item.slug}`)" class="mt-1 block text-[17px] leading-snug font-semibold text-ink group-hover:text-brand-700">
                <span class="absolute inset-0" aria-hidden="true" />
                {{ item.title }}
              </NuxtLink>
            </span>
          </li>
        </ul>
        <p v-else class="mt-[18px] rounded-[18px] border border-dashed border-brand-200 p-6 text-center text-muted">{{ t('posts.empty') }}</p>
        <div class="mt-4 rounded-[18px] bg-brand-50 px-5 py-4">
          <AppPagination v-if="totalPages > 1" :page="page" :total-pages="totalPages" />
          <p v-else class="text-sm text-muted">{{ t('sdg.goal.perPage') }}</p>
        </div>

        <!-- Oldingi / keyingi maqsad -->
        <nav :aria-label="t('sdg.goal.goals')" class="mt-10 grid gap-3.5 sm:grid-cols-2">
          <NuxtLink v-if="prev" :to="localePath(prev.url)" class="flex items-center gap-3.5 rounded-[20px] border border-line bg-white p-[18px] text-ink transition-colors hover:border-accent-500">
            <span class="grid size-11 shrink-0 place-items-center rounded-xl font-extrabold" :style="{ background: sdgColor(prev.n), color: sdgInk(prev.n) }">{{ prev.n }}</span>
            <span class="min-w-0"><span class="block text-xs text-muted">← {{ t('sdg.goal.prev') }}</span><span class="block truncate font-bold">{{ prev.title }}</span></span>
          </NuxtLink>
          <span v-else />
          <NuxtLink v-if="next" :to="localePath(next.url)" class="flex items-center justify-end gap-3.5 rounded-[20px] border border-line bg-white p-[18px] text-right text-ink transition-colors hover:border-accent-500">
            <span class="min-w-0"><span class="block text-xs text-muted">{{ t('sdg.goal.next') }} →</span><span class="block truncate font-bold">{{ next.title }}</span></span>
            <span class="grid size-11 shrink-0 place-items-center rounded-xl font-extrabold" :style="{ background: sdgColor(next.n), color: sdgInk(next.n) }">{{ next.n }}</span>
          </NuxtLink>
        </nav>
      </div>
    </div>
  </div>
</template>
