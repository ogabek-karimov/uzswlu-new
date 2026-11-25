<script setup lang="ts">
import type { ProgramList, StudyForm } from '#shared/types/api'

// Ta'lim yo'nalishlari (canvas: "Ta'lim yo'nalishlari — Bakalavriat"); /bakalavriat va /magistratura
const props = defineProps<{ level: 'bachelor' | 'master' }>()

const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = await useFetch<ProgramList>('/api/programs', { key: `programs-${props.level}`, query: { lang: locale, level: props.level } })

const group = ref('all')

// Ta'lim şakli: Barçasi / Kunduzgi / Keçki / Sirtqi — guruh filtri bilan birga işlaydi; tanlov manzilda (?shakl=kechki),
// havola yuborilsa ham şu körinişda oçiladi
const FORMS: { id: StudyForm; slug: string }[] = [
  { id: 'day', slug: 'kunduzgi' },
  { id: 'evening', slug: 'kechki' },
  { id: 'distance', slug: 'sirtqi' },
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
  { id: 'all' as const, title: t('programs.all'), count: inGroup.value.length },
  ...FORMS.map(f => ({ id: f.id, title: t(`programs.forms.${f.id}`), count: inGroup.value.filter(p => p.formId === f.id).length })),
])

// Surilaviçi fon: tanlangan tugmaning örni va eni ölçanadi (til almaşsa / oyna özgarsa qayta). Ölçanmaguncha (SSR) — oddiy fon
const formBar = ref<HTMLElement>()
const pill = ref<{ left: number; width: number } | null>(null)
function placePill() {
  const btn = formBar.value?.querySelector<HTMLElement>(`[data-form="${form.value}"]`)
  pill.value = btn ? { left: btn.offsetLeft, width: btn.offsetWidth } : null
}
watch([form, forms], () => nextTick(placePill))
onMounted(() => {
  placePill()
  document.fonts?.ready.then(placePill)
  window.addEventListener('resize', placePill, { passive: true })
})
onBeforeUnmount(() => window.removeEventListener('resize', placePill))
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
    <!-- Boşqa içki sahifalar bilan bir xil karta: assets/css/main.css → .page-hero -->
    <section class="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
      <div class="page-hero px-5 py-6 sm:px-8 sm:py-7">
        <PageBreadcrumbs dark :items="[{ label: t('programs.section') }, { label: t(`programs.${level}.name`) }]" />
        <h1 class="mt-4 font-display text-[2.25rem] leading-[1.06] font-semibold tracking-tight sm:text-5xl lg:text-[52px]">
          {{ t(`programs.${level}.name`) }} <span class="text-accent-400 italic">{{ t('programs.accent') }}</span>
        </h1>
        <p class="mt-3 max-w-2xl text-base leading-relaxed text-white/75 sm:text-lg">{{ t(`programs.${level}.lead`) }}</p>
        <nav :aria-label="t('programs.levels')" class="mt-5 flex flex-wrap gap-2">
          <template v-for="l in levels" :key="l.id">
            <span v-if="l.id === level" aria-current="page" class="inline-flex h-11 items-center rounded-full bg-white px-5 font-semibold text-ink">{{ t(`programs.tabs.${l.id}`) }}</span>
            <NuxtLink v-else :to="localePath(l.to)" class="inline-flex h-11 items-center rounded-full border border-white/30 bg-white/10 px-5 font-semibold text-white transition-colors hover:bg-white/20">{{ t(`programs.tabs.${l.id}`) }}</NuxtLink>
          </template>
        </nav>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 pt-10 pb-24 sm:px-6 lg:px-8">
      <!-- Ta'lim şakli: segmentli tanlagiç — tanlangan tugma ostida töq «pill» silliq suriladi; son yozuv yonida kiçik indeks -->
      <span class="mb-2 block text-xs font-semibold tracking-[0.08em] text-muted uppercase" aria-hidden="true">{{ t('programs.forms.label') }}</span>
      <div ref="formBar" role="group" :aria-label="t('programs.forms.label')" class="relative isolate mb-6 flex max-w-full gap-1 overflow-x-auto rounded-full border border-line bg-white p-1.5 shadow-[0_18px_40px_-30px_rgb(56_43_133/0.45)] sm:inline-flex">
        <span
          v-if="pill"
          class="absolute inset-y-1.5 -z-10 rounded-full bg-[linear-gradient(135deg,#382b85,#13112f)] shadow-[0_10px_24px_-10px_rgb(56_43_133/0.9)] transition-[left,width] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none"
          :style="{ left: `${pill.left}px`, width: `${pill.width}px` }"
          aria-hidden="true"
        />
        <button
          v-for="f in forms"
          :key="f.id"
          type="button"
          :data-form="f.id"
          :aria-pressed="form === f.id"
          class="inline-flex h-11 shrink-0 items-center rounded-full px-5 text-[15px] font-semibold tracking-[-0.01em] whitespace-nowrap transition-colors duration-300"
          :class="form === f.id ? ['text-white', !pill && 'bg-brand-900'] : 'text-ink/70 hover:text-ink'"
          @click="form = f.id"
        >
          <span>{{ f.title }}<sup class="relative -top-[0.35em] ml-1 align-baseline text-[11px] font-bold tabular-nums transition-colors" :class="form === f.id ? 'text-accent-400' : 'text-brand-600/70'">{{ f.count }}</sup></span>
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
    <SectionNav />
  </div>
</template>
