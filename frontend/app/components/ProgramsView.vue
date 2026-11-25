<script setup lang="ts">
import type { ProgramList, StudyForm } from '#shared/types/api'

// Ta'lim yo'nalishlari (canvas: "Ta'lim yo'nalishlari — Bakalavriat"); /bakalavriat va /magistratura
const props = defineProps<{ level: 'bachelor' | 'master' }>()

const { data: site } = await useSiteData()
const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = await useFetch<ProgramList>('/api/programs', { key: `programs-${props.level}`, query: { lang: locale, level: props.level } })

const group = ref('all')

// Ta'lim şakli: Barçasi / Kunduzgi / Keçki / Sirtqi — guruh filtri bilan birga işlaydi; tanlov manzilda (?shakl=kechki),
// havola yuborilsa ham şu körinişda oçiladi
const FORMS: { id: StudyForm; slug: string; icon: string }[] = [
  { id: 'day', slug: 'kunduzgi', icon: 'lucide:sun' },
  { id: 'evening', slug: 'kechki', icon: 'lucide:moon-star' },
  { id: 'distance', slug: 'sirtqi', icon: 'lucide:book-open' },
]
const route = useRoute()
const router = useRouter()
const form = computed<StudyForm | 'all'>({
  get: () => FORMS.find(f => f.slug === route.query.shakl)?.id ?? 'all',
  set: (v) => {
    const shakl = FORMS.find(f => f.id === v)?.slug
    router.replace({ query: { ...route.query, shakl } })
  },
})
const inForm = computed(() => (data.value?.items ?? []).filter(p => form.value === 'all' || p.formId === form.value))
const inGroup = computed(() => (data.value?.items ?? []).filter(p => group.value === 'all' || p.group === group.value))
const forms = computed(() => [
  { id: 'all' as const, icon: 'lucide:layers', title: t('programs.all'), count: inGroup.value.length },
  ...FORMS.map(f => ({ id: f.id, icon: f.icon, title: t(`programs.forms.${f.id}`), count: inGroup.value.filter(p => p.formId === f.id).length })),
])
const groups = computed(() => [
  { id: 'all', title: t('programs.all'), count: inForm.value.length },
  ...(data.value?.groups ?? []).map(g => ({ ...g, count: inForm.value.filter(p => p.group === g.id).length })),
])
const items = computed(() => inForm.value.filter(p => group.value === 'all' || p.group === group.value))

const levels = [
  { id: 'bachelor', to: '/bakalavriat' },
  { id: 'master', to: '/magistratura' },
  { id: 'phd', to: '/phd-dasturlari' },
  { id: 'joint', to: '/qoshma-talim-dasturlari' },
] as const

useSeo({ title: () => t(`programs.${props.level}.title`), description: () => t(`programs.${props.level}.lead`) })
</script>

<template>
  <div>
    <section class="relative overflow-hidden bg-brand-950 text-white">
      <span class="decor pointer-events-none absolute top-8 right-10 hidden font-display text-[220px] leading-none text-white/[0.04] italic lg:block" aria-hidden="true">Aa 文 Я</span>
      <div class="relative mx-auto max-w-7xl px-4 pt-8 pb-14 sm:px-6 lg:px-8">
        <PageBreadcrumbs dark :items="[{ label: t('programs.section') }, { label: t(`programs.${level}.name`) }]" />
        <h1 class="mt-8 font-display text-5xl leading-none font-semibold sm:text-[68px]">
          {{ t(`programs.${level}.name`) }} <span class="text-accent-400 italic">{{ t('programs.accent') }}</span>
        </h1>
        <p class="mt-[18px] max-w-2xl text-[19px] leading-relaxed text-white/70">{{ t(`programs.${level}.lead`) }}</p>
        <nav :aria-label="t('programs.levels')" class="mt-8 flex flex-wrap gap-2">
          <template v-for="l in levels" :key="l.id">
            <span v-if="l.id === level" aria-current="page" class="inline-flex h-11 items-center rounded-full bg-white px-5 font-semibold text-ink">{{ t(`programs.tabs.${l.id}`) }}</span>
            <NuxtLink v-else :to="localePath(l.to)" class="inline-flex h-11 items-center rounded-full border border-white/25 px-5 font-semibold text-white transition-colors hover:bg-white/10">{{ t(`programs.tabs.${l.id}`) }}</NuxtLink>
          </template>
        </nav>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 pt-10 sm:px-6 lg:px-8">
      <!-- Ta'lim şakli: segmentli tanlagiç (har birida belgi va yönalişlar soni) -->
      <span class="mb-2 block text-xs font-semibold tracking-[0.08em] text-muted uppercase" aria-hidden="true">{{ t('programs.forms.label') }}</span>
      <div role="group" :aria-label="t('programs.forms.label')" class="mb-6 flex max-w-full gap-1 overflow-x-auto rounded-full border border-line bg-white p-1.5 shadow-[0_18px_40px_-30px_rgb(56_43_133/0.45)] sm:inline-flex">
        <button
          v-for="f in forms"
          :key="f.id"
          type="button"
          :aria-pressed="form === f.id"
          class="group/form inline-flex h-11 shrink-0 items-center gap-2 rounded-full px-4 text-sm font-semibold whitespace-nowrap transition duration-300"
          :class="form === f.id ? 'bg-brand-900 text-white shadow-[0_10px_24px_-10px_rgb(56_43_133/0.9)]' : 'text-ink hover:bg-brand-50'"
          @click="form = f.id"
        >
          <Icon :name="f.icon" class="size-4 transition-transform duration-300 group-hover/form:-rotate-12" :class="form === f.id ? 'text-accent-400' : 'text-brand-600'" aria-hidden="true" />
          {{ f.title }}
          <span class="min-w-6 rounded-full px-1.5 py-0.5 text-center text-xs tabular-nums" :class="form === f.id ? 'bg-white/15 text-white' : 'bg-brand-50 text-muted'">{{ f.count }}</span>
        </button>
      </div>
      <span class="mb-2 block text-xs font-semibold tracking-[0.08em] text-muted uppercase" aria-hidden="true">{{ t('programs.groups') }}</span>
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div role="group" :aria-label="t('programs.groups')" class="flex flex-wrap gap-2">
          <button
            v-for="g in groups"
            :key="g.id"
            type="button"
            :aria-pressed="group === g.id"
            class="h-11 rounded-full border px-4 text-sm font-semibold transition-colors"
            :class="group === g.id ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
            @click="group = g.id"
          >
            {{ g.title }} <span :class="group === g.id ? 'text-white/60' : 'text-muted'">{{ g.count }}</span>
          </button>
        </div>
        <span class="text-sm text-muted" aria-live="polite">{{ t('programs.shown', { n: items.length }) }}</span>
      </div>

      <ul v-reveal class="mt-7 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <li data-reveal-item v-for="p in items" :key="p.id" class="flex flex-col gap-3.5 rounded-[22px] border border-line bg-white p-6">
          <span class="flex items-center justify-between gap-3">
            <span class="text-[13px] font-semibold tracking-[0.06em] text-brand-600">{{ p.code }}</span>
            <span
              :lang="p.language?.code ?? 'uz'"
              class="rounded-full px-3 py-1 text-sm font-semibold"
              :class="p.language ? 'bg-brand-50 text-brand-800' : 'bg-accent-100 text-accent-700'"
            >{{ p.language?.native ?? 'Özbekça' }}</span>
          </span>
          <span class="text-[19px] leading-snug font-semibold">{{ p.title }}</span>
          <span class="mt-auto border-t border-line/70 pt-3.5 text-sm text-muted">{{ p.form }} · {{ t('programs.years', { n: p.years }) }}</span>
        </li>
      </ul>
      <p v-if="!items.length" class="mt-7 rounded-[22px] border border-dashed border-line bg-white px-6 py-10 text-center text-muted">{{ t('programs.forms.empty') }}</p>
    </section>

    <section class="mx-auto grid max-w-7xl gap-5 px-4 pt-14 pb-24 sm:px-6 md:grid-cols-2 lg:px-8">
      <div class="rounded-3xl bg-brand-50 p-7">
        <h2 class="text-xl font-semibold">{{ t('programs.evening.title') }}</h2>
        <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ t('programs.evening.text') }}</p>
        <NuxtLink :to="localePath('/faculty/distance-evening')" class="mt-3.5 inline-flex items-center gap-1.5 font-semibold text-brand-700">
          {{ t('programs.evening.cta') }}
          <Icon name="lucide:arrow-right" class="size-4" />
        </NuxtLink>
      </div>
      <NuxtLink :to="localePath(ADMISSION_PATH)" class="group flex flex-col gap-2 rounded-3xl bg-brand-900 p-7 text-white">
        <span class="font-display text-[26px] font-semibold">{{ t('admission.title', { year: admissionYear(site).full }) }}</span>
        <span class="text-[15px] text-white/70">{{ t('programs.admission') }}</span>
        <span class="mt-2 inline-flex items-center gap-1.5 font-semibold text-accent-400">
          {{ t('programs.admissionCta') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
        </span>
      </NuxtLink>
    </section>
    <SectionNav />
  </div>
</template>
