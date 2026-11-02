<script setup lang="ts">
import type { StaffGroup, StaffList } from '#shared/types/api'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

const GROUPS = ['all', 'lead', 'faculty', 'chair', 'unit'] as const
type GroupFilter = StaffGroup | 'all'

// Filtrlar URL'da saqlanadi: havolani ulashsa, xuddi shu natija ochiladi
const str = (v: unknown) => (typeof v === 'string' ? v : '')
const q = computed(() => str(route.query.q))
const department = computed(() => str(route.query.department))
const group = computed<GroupFilter>(() => (GROUPS as readonly string[]).includes(str(route.query.group)) ? str(route.query.group) as GroupFilter : 'all')
const page = computed(() => Math.max(1, Number.parseInt(str(route.query.page), 10) || 1))

const { data, status } = await useFetch<StaffList>('/api/staff', {
  key: 'staff-list',
  query: { lang: locale, q, department, group, page },
})

function setFilters(patch: { q?: string; department?: string; group?: GroupFilter }) {
  const next: Record<string, string> = {}
  const merged = { q: q.value, department: department.value, group: group.value, ...patch }
  if (merged.q) next.q = merged.q
  if (merged.department) next.department = merged.department
  if (merged.group !== 'all') next.group = merged.group
  // Filtr o'zgarsa — birinchi sahifaga qaytamiz
  router.replace({ query: next })
}

// Qidiruv yozib bo'lingach (300 ms) qo'llanadi
const search = ref(q.value)
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, (value) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    if (value.trim() !== q.value) setFilters({ q: value.trim() })
  }, 300)
})
watch(q, (value) => {
  if (value !== search.value.trim()) search.value = value
})

const totalPages = computed(() => (data.value ? Math.ceil(data.value.total / data.value.perPage) : 0))

// Sahifa almashganda ro'yxat boshiga qaytish
const results = ref<HTMLElement>()
watch(page, () => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  results.value?.scrollIntoView({ block: 'start', behavior: reduce ? 'auto' : 'smooth' })
})

const departmentGroups = computed(() => {
  const list = data.value?.departments ?? []
  return (['lead', 'faculty', 'chair', 'unit'] as const)
    .map(g => ({ group: g, items: list.filter(d => d.group === g) }))
    .filter(g => g.items.length)
})

useSeoMeta({
  title: () => t('staff.title'),
  description: () => t('staff.lead'),
})
</script>

<template>
  <div>
    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
      <PageBreadcrumbs :items="[{ label: t('staff.university') }, { label: t('staff.title') }]" />

      <div class="mt-7 flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 class="font-display text-5xl leading-none font-semibold tracking-tight text-ink sm:text-6xl">{{ t('staff.title') }}</h1>
          <p class="mt-4 max-w-2xl text-lg leading-relaxed text-muted sm:text-xl">{{ t('staff.lead') }}</p>
        </div>
        <dl v-if="data" class="flex gap-8">
          <div class="flex flex-col-reverse gap-1">
            <dt class="text-sm text-muted">{{ t('staff.statPeople') }}</dt>
            <dd class="font-display text-4xl leading-none font-semibold text-ink sm:text-[44px]">{{ data.summary.staff.toLocaleString('ru-RU') }}</dd>
          </div>
          <div class="flex flex-col-reverse gap-1">
            <dt class="text-sm text-muted">{{ t('staff.statDepartments') }}</dt>
            <dd class="font-display text-4xl leading-none font-semibold text-ink sm:text-[44px]">{{ data.summary.departments }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <!-- Qidiruv va filtrlar -->
    <section class="mx-auto max-w-7xl px-4 pt-9 sm:px-6 lg:px-8">
      <div role="search" class="flex flex-wrap gap-3 rounded-[28px] border border-line bg-white p-4 sm:p-5">
        <label class="flex h-14 min-w-0 flex-[2_1_320px] items-center gap-3 rounded-2xl border border-line bg-paper px-4 focus-within:border-accent-600">
          <Icon name="lucide:search" class="size-5 shrink-0 text-muted" />
          <span class="sr-only">{{ t('staff.searchLabel') }}</span>
          <input
            v-model="search"
            type="search"
            :placeholder="t('staff.searchPlaceholder')"
            autocomplete="off"
            class="h-full min-w-0 flex-1 bg-transparent text-base text-ink outline-none placeholder:text-muted"
          >
        </label>

        <label class="relative flex h-14 min-w-0 flex-[1_1_260px] items-center rounded-2xl border border-line bg-paper focus-within:border-accent-600">
          <Icon name="lucide:building-2" class="pointer-events-none absolute left-4 size-5 text-muted" />
          <span class="sr-only">{{ t('staff.departmentLabel') }}</span>
          <select
            :value="department"
            class="h-full w-full min-w-0 cursor-pointer appearance-none truncate bg-transparent pr-11 pl-12 text-base text-ink outline-none"
            @change="setFilters({ department: ($event.target as HTMLSelectElement).value })"
          >
            <option value="">{{ t('staff.allDepartments') }}</option>
            <optgroup v-for="g in departmentGroups" :key="g.group" :label="t(`staff.groups.${g.group}`)">
              <option v-for="d in g.items" :key="d.id" :value="d.id">{{ d.name }} ({{ d.count }})</option>
            </optgroup>
          </select>
          <Icon name="lucide:chevron-down" class="pointer-events-none absolute right-4 size-5 text-muted" />
        </label>

        <div role="group" :aria-label="t('staff.groupsLabel')" class="flex basis-full flex-wrap gap-2">
          <button
            v-for="g in GROUPS"
            :key="g"
            type="button"
            :aria-pressed="group === g"
            class="h-10.5 rounded-full border px-4 text-sm font-semibold transition-colors"
            :class="group === g ? 'border-brand-900 bg-brand-900 text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
            @click="setFilters({ group: g })"
          >
            {{ t(`staff.groups.${g}`) }}
            <span :class="group === g ? 'text-accent-400' : 'text-muted'">{{ data?.groups[g] ?? '' }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Natijalar -->
    <section ref="results" class="mx-auto max-w-7xl scroll-mt-32 px-4 pt-6 pb-24 sm:px-6 lg:px-8" :aria-busy="status === 'pending'">
      <p class="text-[15px] text-muted" aria-live="polite">
        <template v-if="data">{{ t('staff.results', { n: data.total }) }}</template>
      </p>

      <ul
        v-if="data?.items.length"
        class="mt-5 grid gap-4 transition-opacity sm:grid-cols-2 lg:grid-cols-3"
        :class="status === 'pending' && 'opacity-60'"
      >
        <li v-for="person in data.items" :key="person.id">
          <StaffCard :person="person" />
        </li>
      </ul>

      <div v-else-if="data" class="mt-5 flex flex-col items-center rounded-[28px] border border-dashed border-line bg-white px-6 py-16 text-center">
        <span class="grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-700">
          <Icon name="lucide:user-round-search" class="size-6" />
        </span>
        <p class="mt-5 text-lg font-semibold text-ink">{{ t('staff.empty') }}</p>
        <p class="mt-1 text-muted">{{ t('staff.emptyHint') }}</p>
        <button type="button" class="mt-6 rounded-full bg-brand-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-800" @click="search = ''; router.replace({ query: {} })">
          {{ t('staff.reset') }}
        </button>
      </div>

      <AppPagination v-if="data" class="mt-10" :page="data.page" :total-pages="totalPages" />
    </section>
  </div>
</template>
