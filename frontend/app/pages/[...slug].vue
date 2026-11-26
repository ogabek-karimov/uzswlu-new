<script setup lang="ts">
import type { ContentPage } from '#shared/types/api'
const NuxtLink = resolveComponent('NuxtLink')

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
// Menyuda yöq ichki sahifa — yon menyu va yöl ota sahifaniki (u faol körinadi)
// Ichki sahifada — menyudagi ajdod (trail[0]), bölmasa ota sahifa
const navPath = computed(() => page.value?.parent?.trail?.[0]?.url ?? page.value?.parent?.url ?? path.value)
const group = computed(() => site.value?.menu.find(g => g.links.some(l => l.url === navPath.value)))
const siblings = computed(() => group.value?.links ?? [])
const internal = computed(() => siblings.value.filter(l => !isExternal(l)))
const index = computed(() => page.value?.parent ? -2 : internal.value.findIndex(l => l.url === path.value))
const prev = computed(() => internal.value[index.value - 1])
const next = computed(() => internal.value[index.value + 1])

// Vaqt chizig'i matndagi <!-- timeline --> belgisi o'rniga qo'yiladi (bo'lmasa — oxiriga)
const parts = computed(() => {
  const [before = '', ...after] = (page.value?.body ?? '').split('<!-- timeline -->')
  return { before, after: after.join('') }
})

// Hujjatlar: «ichi ko'rinadi» PDF — ko'rgiçda; qolganlari — karta ko'rinişida
const embedDocs = computed(() => (page.value?.attachments ?? []).filter(f => f.kind === 'pdf' && f.display === 'embed'))
const listDocs = computed(() => (page.value?.attachments ?? []).filter(f => !(f.kind === 'pdf' && f.display === 'embed')))

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
    <section class="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
      <div class="page-hero px-5 py-6 sm:px-8 sm:py-7">
        <PageBreadcrumbs dark :items="[...(group ? [{ label: group.title }] : []), ...(page.parent ? (page.parent.trail?.length ? page.parent.trail : [page.parent]).map(x => ({ label: x.title, to: x.url })) : []), { label: page.title }]" />
        <div class="mt-4 flex flex-wrap items-end justify-between gap-5">
          <div class="max-w-[820px] min-w-0">
            <h1 class="font-display text-[2.25rem] leading-[1.06] font-semibold tracking-tight text-white sm:text-5xl lg:text-[52px]">{{ page.title }}</h1>
            <p v-if="page.lead" class="mt-3 text-base leading-relaxed text-white/75 sm:text-lg">{{ page.lead }}</p>
          </div>
          <div class="no-print flex gap-2">
            <button
              type="button"
              class="relative grid size-11 place-items-center hero-btn rounded-full"
              :aria-label="t('page.share')"
              @click="share(page.title)"
            >
              <Icon :name="copied ? 'lucide:check' : 'lucide:share-2'" class="size-[18px]" />
              <span v-if="copied" role="status" class="absolute top-1/2 right-full mr-2 -translate-y-1/2 rounded-lg bg-white px-2.5 py-1 text-xs font-medium whitespace-nowrap text-brand-900">{{ t('page.copied') }}</span>
            </button>
            <button type="button" class="grid size-11 place-items-center hero-btn rounded-full" :aria-label="t('page.print')" @click="printPage">
              <Icon name="lucide:printer" class="size-[18px]" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <div class="mx-auto flex max-w-7xl flex-col gap-14 px-4 pt-12 pb-24 sm:px-6 lg:flex-row lg:items-start lg:px-8">
      <!-- Bo'lim sahifalari: telefonda matndan keyin -->
      <aside v-if="siblings.length" class="order-2 min-w-0 lg:sticky lg:top-36 lg:order-1 lg:w-[320px] lg:shrink-0">
        <!-- Bo'lim sahifalari: oq karta; hover — ramka, biroz kattalashish va o'ngga siljish; faol — gradient va chap chiziq -->
        <nav class="side-nav" :aria-label="t('page.sectionPages')">
          <p class="side-nav-title"><Icon name="lucide:layers" class="text-[15px]" />{{ t('page.sectionPages') }}</p>
          <ul class="flex flex-col gap-1 text-[15px]">
            <li v-for="link in siblings" :key="link.url">
              <span v-if="link.url === path" aria-current="page" class="side-nav-item side-nav-active">
                <Icon v-if="link.icon" :name="`lucide:${link.icon}`" class="size-[18px] shrink-0 text-brand-600" aria-hidden="true" />
                <span v-else class="side-nav-dot" aria-hidden="true" />
                <span class="min-w-0 flex-1">{{ link.title }}</span>
              </span>
              <!-- Ichki sahifada ota sahifa faol körinadi, lekin bosilsa — ota sahifaga qaytadi -->
              <NavMenuLink v-else :link="link" class="side-nav-item group" :class="link.url === navPath && 'side-nav-active'" :aria-current="link.url === navPath ? 'true' : undefined">
                <Icon v-if="link.icon" :name="`lucide:${link.icon}`" class="size-[18px] shrink-0 text-brand-600" aria-hidden="true" />
                <span v-else class="side-nav-dot" aria-hidden="true" />
                <span class="min-w-0 flex-1">{{ link.title }}</span>
                <span v-if="link.file" class="self-center rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-bold text-red-700 uppercase">{{ link.file }}</span>
                <Icon v-else name="lucide:arrow-right" class="side-nav-arrow" />
              </NavMenuLink>
            </li>
          </ul>
        </nav>
      </aside>

      <article class="order-1 max-w-[820px] min-w-0 flex-1 lg:order-2">
        <dl v-if="page.facts.length" class="mb-10 grid grid-cols-2 gap-px overflow-hidden rounded-3xl border border-line bg-line sm:grid-cols-4">
          <div v-for="fact in page.facts" :key="fact.label" class="flex flex-col-reverse gap-1.5 bg-white p-5 sm:p-[22px]">
            <dt class="text-[13px] text-muted">{{ fact.label }}</dt>
            <dd class="font-display text-[32px] leading-none font-semibold text-brand-800 sm:text-4xl">{{ fact.value }}</dd>
          </div>
        </dl>

        <!-- Bo'lim xodimlari: HEMIS'dan avtomatik (admin → Sahifalar → «Bo'lim xodimlari»); rahbar birinchi -->
        <section v-if="page.staff?.length" class="mb-12" aria-labelledby="page-staff">
          <h2 id="page-staff" class="mb-5 font-display text-2xl font-semibold text-ink">{{ t('page.staffTitle') }}</h2>
          <ul class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
            <li v-for="person in page.staff" :key="person.id"><StaffPageCard :person="person" /></li>
          </ul>
        </section>

        <PageBodyHtml :html="parts.before" :doc-style="page.docStyle" :showcase="page.showcase" />

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

        <div v-if="parts.after" class="mt-12"><PageBodyHtml :html="parts.after" :doc-style="page.docStyle" :showcase="page.showcase" /></div>

        <!-- Ichki sahifalar kartalari (admin → Sahifalar → «Ichki sahifalar kartalari»), masalan Yoshlar ittifoqi tadbirlari -->
        <PageChildCards v-if="page.children?.length" :items="page.children" />

        <!-- Chaqiruv bloki (admin → Sahifalar → «Chaqiruv bloki»): matndan keyin, animatsiyali tugma -->
        <PageCta v-if="page.cta" :cta="page.cta" />

        <!-- Bo'limlar kartalari (admin → Bo'limlar): surat yoki belgi, F.I.Sh., lavozim, telefon; havolasi bo'lsa bosiladi -->
        <ul v-if="page.units?.length" class="mt-12 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <li v-for="(u, i) in page.units" :key="i">
            <component
              :is="u.url ? (u.url.startsWith('http') ? 'a' : NuxtLink) : 'div'"
              v-bind="u.url ? (u.url.startsWith('http') ? { href: u.url, target: '_blank', rel: 'noopener' } : { to: localePath(u.url) }) : {}"
              class="group flex h-full flex-col items-center rounded-3xl border border-line bg-white p-6 text-center transition duration-300"
              :class="u.url && 'hover:-translate-y-1 hover:border-brand-200 hover:shadow-[0_24px_44px_-30px_rgb(19_17_47/0.45)]'"
            >
              <span class="size-28 shrink-0 overflow-hidden rounded-full bg-paper ring-4 ring-white shadow-[0_10px_24px_-14px_rgb(19_17_47/0.45)]">
                <img v-if="u.photo" :src="u.photo" :alt="u.name || u.unit || ''" width="112" height="112" loading="lazy" class="size-full object-cover object-top transition-transform duration-500 group-hover:scale-105">
                <span v-else class="grid size-full place-items-center text-muted"><Icon name="lucide:user-round" class="text-5xl" /></span>
              </span>
              <span v-if="u.unit && u.name" class="mt-4 text-xs font-semibold tracking-wide text-brand-700 uppercase">{{ u.unit }}</span>
              <span class="font-semibold leading-snug text-ink" :class="u.unit && u.name ? 'mt-1.5' : 'mt-4'">{{ u.name || u.unit }}</span>
              <span v-if="u.position" class="mt-1.5 text-sm leading-snug text-muted">{{ u.position }}</span>
              <span v-if="u.count" class="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-muted"><Icon name="lucide:users" class="text-sm" />{{ t('page.unitStaff', { n: u.count }) }}</span>
              <span v-if="u.phone || u.ext" class="mt-3 inline-flex items-center gap-1.5 text-sm text-ink/80 tabular-nums">
                <Icon name="lucide:phone" class="text-base text-muted" />{{ u.phone }}<template v-if="u.ext"> · {{ t('contact.ext', { ext: u.ext }) }}</template>
              </span>
            </component>
          </li>
        </ul>

        <!-- Rektor kartasi (admin → Rahbariyat'dan; rektor almashsa o'zi yangilanadi) -->
        <NuxtLink v-if="page.rector" :to="localePath('/rektorat')" class="group mt-12 flex flex-col gap-6 overflow-hidden rounded-[28px] border border-line bg-[linear-gradient(150deg,#fff,#faf8f4)] p-6 shadow-[0_24px_50px_-36px_rgb(19_17_47/0.45)] transition duration-300 hover:-translate-y-1 hover:border-[#e7ddc8] hover:shadow-[0_34px_64px_-36px_rgb(19_17_47/0.5)] sm:flex-row sm:items-center sm:p-8">
          <span class="relative mx-auto size-40 shrink-0 overflow-hidden rounded-3xl bg-paper ring-1 ring-line sm:mx-0 sm:size-44">
            <img v-if="page.rector.photo" :src="page.rector.photo" :alt="page.rector.name" width="176" height="176" loading="lazy" class="size-full object-cover object-top transition-transform duration-500 group-hover:scale-105">
            <span v-else class="grid size-full place-items-center text-muted"><Icon name="lucide:user-round" class="text-6xl" /></span>
          </span>
          <span class="min-w-0 flex-1 text-center sm:text-left">
            <span class="text-xs font-semibold tracking-[0.18em] text-muted uppercase">{{ t('page.rectorNow') }}</span>
            <span class="mt-1.5 block font-display text-[26px] leading-tight font-semibold sm:text-3xl">{{ page.rector.name }}</span>
            <span class="mt-1 block text-[15px] text-muted">{{ page.rector.role }}</span>
            <span class="mt-4 flex flex-wrap justify-center gap-x-5 gap-y-1.5 text-sm text-ink/80 sm:justify-start">
              <span v-if="page.rector.hours" class="inline-flex items-center gap-1.5"><Icon name="lucide:calendar-clock" class="text-base text-muted" />{{ page.rector.hours }}</span>
              <span v-if="page.rector.phone" class="inline-flex items-center gap-1.5"><Icon name="lucide:phone" class="text-base text-muted" />{{ page.rector.phone }}</span>
              <span v-if="page.rector.email" class="inline-flex items-center gap-1.5"><Icon name="lucide:mail" class="text-base text-muted" />{{ page.rector.email }}</span>
            </span>
            <span class="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-ink">{{ t('page.rectorMore') }}<Icon name="lucide:arrow-right" class="transition-transform group-hover:translate-x-1" /></span>
          </span>
        </NuxtLink>

        <!-- Biriktirilgan hujjatlar -->
        <!-- Hujjat: belgi, nomi, hajmi; «Köriş» (yangi oynada) va «Yuklab oliş» -->
        <!-- «Ichi ko'rinadi» PDF — sahifada ochilib turadi, ostida varaqlar (1 2 3 …) -->
        <!-- Bitta PDF — to'g'ridan-to'g'ri ko'rgiçda; bir neçta — hujjat tanlagiç (röyxat + bitta ko'rgiç) -->
        <div v-if="embedDocs.length === 1" class="mt-12">
          <PdfPager :url="embedDocs[0]!.url" :title="embedDocs[0]!.title" />
        </div>
        <PdfDocs v-else-if="embedDocs.length > 1" :docs="embedDocs" class="mt-12" />
        <ul v-if="listDocs.length" class="mt-12 flex flex-col gap-3">
          <li v-for="file in listDocs" :key="file.url" class="group flex flex-col gap-4 rounded-3xl border border-line bg-white p-4 transition duration-300 hover:border-accent-500 hover:shadow-[0_20px_44px_-32px_rgb(28_21_72/0.5)] sm:flex-row sm:items-center sm:p-5">
            <span aria-hidden="true" class="relative grid size-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-red-50 to-red-100 text-red-600 transition-transform duration-300 group-hover:-rotate-6">
              <Icon :name="file.kind === 'pdf' ? 'lucide:file-text' : 'lucide:link'" class="size-7" />
              <span v-if="file.kind === 'pdf'" class="absolute -right-1.5 -bottom-1.5 rounded-md bg-red-600 px-1.5 py-0.5 text-[9px] font-extrabold tracking-wide text-white">PDF</span>
            </span>
            <span class="min-w-0 flex-1">
              <a :href="file.url" target="_blank" rel="noopener" class="block leading-snug font-semibold text-ink hover:text-brand-700">{{ file.title }}</a>
              <span v-if="file.meta" class="mt-1 block text-[13px] text-muted">{{ file.meta }}</span>
            </span>
            <span class="flex shrink-0 gap-2">
              <a :href="file.url" target="_blank" rel="noopener" class="inline-flex h-11 items-center gap-2 rounded-full border border-line bg-paper px-4 text-sm font-semibold text-ink transition-colors hover:border-brand-700">
                <Icon name="lucide:eye" class="size-4" />{{ t('page.view') }}
              </a>
              <a v-if="file.kind === 'pdf'" :href="file.url" download class="inline-flex h-11 items-center gap-2 rounded-full bg-brand-800 px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-700">
                <Icon name="lucide:download" class="size-4 transition-transform group-hover:translate-y-0.5" />{{ t('page.download') }}
              </a>
            </span>
          </li>
        </ul>

        <!-- Xorijiy abituriyent arizasi (Xalqaro talabalar → Ariza şakli): ariza admin panelga tuşadi -->
        <ApplicationForm v-if="page.slug === 'ariza-shakli'" class="mt-10" />

        <!-- Ota sahifaning boşqa kartalari (masalan, Magistrlik dasturlari → Qabul nizomi, Qabul kvotasi …) -->
        <PageShowcase v-if="page.parent?.cards.length" class="no-print" :data="{ n: 1, intro: null, stats: [], columns: [], outro: null, photos: [], cards: page.parent.cards }" />

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
