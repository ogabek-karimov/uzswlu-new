<script setup lang="ts">
import type { ContentPage } from '#shared/types/api'

// Matnli sahifa (canvas: "Matnli sahifa — Universitet haqida"). Menyudagi har bir oddiy sahifa shu shablonda.
// Yon menyu va "Oldingi/Keyingi" — sayt menyusidan; menyuda yo'q manzil — 404.
const { t, locale } = useI18n()
const route = useRoute()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const slug = computed(() => {
  const value = route.params.slug
  return Array.isArray(value) ? value.join('/') : String(value ?? '')
})

if (!/^[a-z0-9-]{1,120}$/.test(slug.value)) {
  throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true })
}

const { data: page, error } = await useFetch<ContentPage>(() => `/api/pages/${slug.value}`, { query: { lang: locale } })
if (error.value || !page.value) {
  throw createError({ statusCode: error.value?.statusCode ?? 404, statusMessage: 'Page not found', fatal: true })
}

const { data: site } = await useSiteData()

const path = computed(() => `/${slug.value}`)
const group = computed(() => site.value?.menu.find(g => g.links.some(l => l.url === path.value)))
const siblings = computed(() => group.value?.links ?? [])
const internal = computed(() => siblings.value.filter(l => !isExternal(l)))
const index = computed(() => internal.value.findIndex(l => l.url === path.value))
const prev = computed(() => internal.value[index.value - 1])
const next = computed(() => internal.value[index.value + 1])

// Vaqt chizig'i matndagi <!-- timeline --> belgisi o'rniga qo'yiladi (bo'lmasa — oxiriga)
const parts = computed(() => {
  const [before = '', ...after] = (page.value?.body ?? '').split('<!-- timeline -->')
  return { before, after: after.join('') }
})

const { copied, share } = useShare()
const feedback = ref<'yes' | 'no' | null>(null)
const printPage = () => window.print()

useSeo({
  title: () => page.value?.title ?? '',
  description: () => page.value?.lead ?? undefined,
})
</script>

<template>
  <div v-if="page">
    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
      <PageBreadcrumbs :items="[...(group ? [{ label: group.title }] : []), { label: page.title }]" />
      <div class="mt-7 flex flex-wrap items-end justify-between gap-6 border-b border-line pb-9">
        <div class="max-w-[820px] min-w-0">
          <p v-if="group" class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">
            <span class="h-px w-8 bg-accent-500" />
            {{ group.title }}
          </p>
          <h1 class="mt-3.5 font-display text-[2.75rem] leading-[1.04] font-semibold tracking-tight text-ink sm:text-6xl lg:text-[64px]">{{ page.title }}</h1>
          <p v-if="page.lead" class="mt-5 text-lg leading-relaxed text-muted sm:text-xl">{{ page.lead }}</p>
        </div>
        <div class="no-print flex gap-2">
          <button
            type="button"
            class="relative grid size-11 place-items-center rounded-full border border-line bg-white text-ink transition-colors hover:border-accent-500"
            :aria-label="t('page.share')"
            @click="share(page.title)"
          >
            <Icon :name="copied ? 'lucide:check' : 'lucide:share-2'" class="size-[18px]" />
            <span v-if="copied" role="status" class="absolute top-full right-0 mt-2 rounded-lg bg-ink px-2.5 py-1 text-xs whitespace-nowrap text-white">{{ t('page.copied') }}</span>
          </button>
          <button type="button" class="grid size-11 place-items-center rounded-full border border-line bg-white text-ink transition-colors hover:border-accent-500" :aria-label="t('page.print')" @click="printPage">
            <Icon name="lucide:printer" class="size-[18px]" />
          </button>
        </div>
      </div>
    </section>

    <div class="mx-auto flex max-w-7xl flex-col gap-14 px-4 pt-12 pb-24 sm:px-6 lg:flex-row lg:items-start lg:px-8">
      <!-- Bo'lim sahifalari: telefonda matndan keyin -->
      <aside v-if="siblings.length" class="order-2 min-w-0 lg:sticky lg:top-36 lg:order-1 lg:w-[280px] lg:shrink-0">
        <p class="mb-3 text-xs font-semibold tracking-[0.16em] text-muted uppercase">{{ t('page.sectionPages') }}</p>
        <ul class="border-l-2 border-line text-[15px]">
          <li v-for="link in siblings" :key="link.url">
            <span v-if="link.url === path" aria-current="page" class="-ml-0.5 block rounded-r-[10px] border-l-2 border-brand-800 bg-brand-50 px-4 py-2.5 font-semibold text-brand-800">{{ link.title }}</span>
            <NavMenuLink v-else :link="link" class="flex justify-between gap-2 px-4 py-2.5 text-muted transition-colors hover:text-ink">
              <span>{{ link.title }}</span>
              <span v-if="link.file" class="self-center text-[10px] font-bold text-red-700 uppercase">{{ link.file }}</span>
            </NavMenuLink>
          </li>
        </ul>
      </aside>

      <article class="order-1 max-w-[820px] min-w-0 flex-1 lg:order-2">
        <dl v-if="page.facts.length" class="mb-10 grid grid-cols-2 gap-px overflow-hidden rounded-3xl border border-line bg-line sm:grid-cols-4">
          <div v-for="fact in page.facts" :key="fact.label" class="flex flex-col-reverse gap-1.5 bg-white p-5 sm:p-[22px]">
            <dt class="text-[13px] text-muted">{{ fact.label }}</dt>
            <dd class="font-display text-[32px] leading-none font-semibold text-brand-800 sm:text-4xl">{{ fact.value }}</dd>
          </div>
        </dl>

        <ProseHtml :html="parts.before" />

        <ol v-if="page.timeline.length" class="mt-7 grid gap-4 sm:grid-cols-3">
          <li
            v-for="item in page.timeline"
            :key="item.label"
            class="rounded-[20px] border p-5"
            :class="item.highlight ? 'border-brand-900 bg-brand-900 text-white' : 'border-line bg-white'"
          >
            <span class="font-display text-[30px] font-semibold" :class="item.highlight ? 'text-accent-400' : 'text-brand-700'">{{ item.label }}</span>
            <p class="mt-1.5 text-sm leading-normal" :class="item.highlight ? 'text-white/70' : 'text-muted'">{{ item.text }}</p>
          </li>
        </ol>

        <ProseHtml v-if="parts.after" :html="parts.after" class="mt-12" />

        <!-- Biriktirilgan hujjatlar -->
        <ul v-if="page.attachments.length" class="mt-12 flex flex-col gap-3">
          <li v-for="file in page.attachments" :key="file.url">
            <a :href="file.url" target="_blank" rel="noopener" class="group flex items-center gap-4 rounded-[20px] border border-line bg-white px-5 py-[18px] text-ink transition-colors hover:border-accent-500">
              <span class="grid h-14 w-12 shrink-0 place-items-center rounded-[10px] bg-red-50 text-[11px] font-bold text-red-700">{{ file.kind === 'pdf' ? 'PDF' : 'URL' }}</span>
              <span class="min-w-0 flex-1">
                <span class="block font-semibold">{{ file.title }}</span>
                <span v-if="file.meta" class="mt-0.5 block text-[13px] text-muted">{{ file.meta }}</span>
              </span>
              <span class="hidden shrink-0 text-sm font-semibold text-brand-700 sm:inline">{{ t('page.download') }} ↓</span>
            </a>
          </li>
        </ul>

        <!-- Fikr bildirish -->
        <div class="no-print mt-10 flex flex-wrap items-center justify-between gap-4 rounded-[20px] border border-line bg-white px-6 py-[22px]">
          <span class="font-semibold">{{ t('page.helpful') }}</span>
          <span v-if="!feedback" class="flex gap-2">
            <button type="button" class="h-11 rounded-full border border-line bg-paper px-5 text-sm font-semibold transition-colors hover:border-accent-500" @click="feedback = 'yes'">{{ t('page.yes') }}</button>
            <button type="button" class="h-11 rounded-full border border-line bg-paper px-5 text-sm font-semibold transition-colors hover:border-accent-500" @click="feedback = 'no'">{{ t('page.no') }}</button>
          </span>
          <span v-else role="status" class="flex items-center gap-2 text-sm font-semibold text-accent-700">
            <Icon name="lucide:heart-handshake" class="size-4" />
            {{ t('page.thanks') }}
          </span>
          <span class="w-full text-[13px] text-muted">{{ t('page.updated', { date: formatDate(page.updatedAt) }) }}</span>
        </div>

        <!-- Oldingi / keyingi -->
        <nav v-if="prev || next" :aria-label="t('page.sectionNav')" class="no-print mt-6 grid gap-4 sm:grid-cols-2">
          <NuxtLink v-if="prev" :to="localePath(prev.url)" class="rounded-[20px] border border-line bg-white p-5 text-ink transition-colors hover:border-accent-500">
            <span class="block text-[13px] text-muted">{{ t('page.prev') }}</span>
            <span class="mt-1 block text-lg font-semibold">← {{ prev.title }}</span>
          </NuxtLink>
          <span v-else class="rounded-[20px] border border-dashed border-line p-5 text-sm text-muted">{{ t('page.first') }}</span>
          <NuxtLink v-if="next" :to="localePath(next.url)" class="rounded-[20px] border border-line bg-white p-5 text-right text-ink transition-colors hover:border-accent-500">
            <span class="block text-[13px] text-muted">{{ t('page.next') }}</span>
            <span class="mt-1 block text-lg font-semibold">{{ next.title }} →</span>
          </NuxtLink>
          <span v-else class="rounded-[20px] border border-dashed border-line p-5 text-right text-sm text-muted">{{ t('page.last') }}</span>
        </nav>
      </article>
    </div>
  </div>
</template>
