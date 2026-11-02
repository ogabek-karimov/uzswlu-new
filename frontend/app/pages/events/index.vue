<script setup lang="ts">
import type { EventItem, EventMonth } from '#shared/types/api'

// Tadbirlar taqvimi (canvas: "Tadbirlar taqvimi"): oylik taqvim + tanlangan kun + yaqin tadbirlar
const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const formatDate = useFormatDate()

// Toshkent vaqti bo'yicha bugun: YYYY-MM-DD
const today = new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString().slice(0, 10)
const month = computed(() => {
  const m = route.query.month
  return typeof m === 'string' && /^\d{4}-(0[1-9]|1[0-2])$/.test(m) ? m : today.slice(0, 7)
})

const { data } = await useFetch<EventMonth>('/api/events', { key: 'events-month', query: { lang: locale, month } })

const dayOf = (e: EventItem) => new Date(new Date(e.startsAt).getTime() + 5 * 60 * 60 * 1000).toISOString().slice(0, 10)

const byDay = computed(() => {
  const map = new Map<string, EventItem[]>()
  for (const e of data.value?.items ?? []) {
    const key = dayOf(e)
    map.set(key, [...(map.get(key) ?? []), e])
  }
  return map
})

// Tanlangan kun: bugun (shu oyda bo'lsa) → birinchi tadbirli kun → 1-kun
const selected = ref('')
watch([month, byDay], () => {
  if (selected.value.startsWith(month.value)) return
  selected.value = today.startsWith(month.value) ? today : [...byDay.value.keys()].sort()[0] ?? `${month.value}-01`
}, { immediate: true })

// Taqvim katakchalari (dushanbadan boshlanadi)
const cells = computed(() => {
  const [y, m] = month.value.split('-').map(Number) as [number, number]
  const first = new Date(Date.UTC(y, m - 1, 1))
  const offset = (first.getUTCDay() + 6) % 7
  const days = new Date(Date.UTC(y, m, 0)).getUTCDate()
  const total = Math.ceil((offset + days) / 7) * 7
  return Array.from({ length: total }, (_, i) => {
    const date = new Date(Date.UTC(y, m - 1, i - offset + 1))
    const iso = date.toISOString().slice(0, 10)
    return { iso, day: date.getUTCDate(), inMonth: iso.startsWith(month.value), has: byDay.value.has(iso) }
  })
})

const shiftMonth = (delta: number) => {
  const [y, m] = month.value.split('-').map(Number) as [number, number]
  const d = new Date(Date.UTC(y, m - 1 + delta, 1))
  router.replace({ query: { month: d.toISOString().slice(0, 7) } })
}

const monthTitle = computed(() => {
  const name = formatDate(`${month.value}-15T12:00:00+05:00`, 'month')
  return `${name.charAt(0).toUpperCase()}${name.slice(1)}`
})
const dayEvents = computed(() => byDay.value.get(selected.value) ?? [])
const selectedLabel = computed(() => formatDate(`${selected.value}T12:00:00+05:00`) + (selected.value === today ? ` · ${t('calendar.today')}` : ''))

// Yaqin tadbirlar — toifa bo'yicha filtr
const filter = ref('')
const upcoming = computed(() => data.value?.upcoming ?? [])
const categories = computed(() => [...new Set(upcoming.value.map(e => e.category))])
const shown = computed(() => upcoming.value.filter(e => !filter.value || e.category === filter.value))

// Oy tadbirlarini taqvim fayli (.ics) sifatida yuklab olish
function downloadIcs() {
  const stamp = (iso: string) => new Date(iso).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
  const esc = (v: string) => v.replace(/[\\,;]/g, m => `\\${m}`).replace(/\n/g, '\\n')
  const events = (data.value?.items ?? []).map(e => [
    'BEGIN:VEVENT',
    `UID:${e.id}@uzswlu.uz`,
    `DTSTAMP:${stamp(new Date().toISOString())}`,
    `DTSTART:${stamp(e.startsAt)}`,
    `DTEND:${stamp(e.endsAt ?? new Date(new Date(e.startsAt).getTime() + 2 * 60 * 60 * 1000).toISOString())}`,
    `SUMMARY:${esc(e.title)}`,
    e.location ? `LOCATION:${esc(e.location)}` : '',
    `URL:${window.location.origin}${localePath(`/events/${e.slug}`)}`,
    'END:VEVENT',
  ].filter(Boolean).join('\r\n'))
  const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//UzSWLU//Events//UZ', ...events, 'END:VCALENDAR'].join('\r\n')
  const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: `uzswlu-events-${month.value}.ics` })
  a.click()
  URL.revokeObjectURL(url)
}

useSeoMeta({ title: () => t('calendar.title'), description: () => t('calendar.lead') })
</script>

<template>
  <div>
    <PageIntro :crumbs="[{ label: t('posts.tabs.news'), to: '/yangiliklar' }, { label: t('posts.tabs.events') }]" :title="t('calendar.title')" :lead="t('calendar.lead')">
      <button type="button" class="inline-flex h-12 items-center gap-2 rounded-full border border-ink/20 px-5 text-sm font-semibold text-ink transition-colors hover:bg-ink hover:text-white" :disabled="!data?.items.length" @click="downloadIcs">
        <Icon name="lucide:calendar-plus" class="size-[18px]" />
        {{ t('calendar.subscribe') }}
      </button>
    </PageIntro>

    <section class="mx-auto flex max-w-7xl flex-col gap-7 px-4 pt-9 sm:px-6 lg:flex-row lg:items-start lg:px-8">
      <!-- Oylik taqvim -->
      <div class="min-w-0 rounded-[28px] border border-line bg-white p-4 sm:p-7 lg:flex-[1.3]">
        <div class="flex items-center justify-between">
          <h2 class="font-display text-[30px] font-semibold">{{ monthTitle }} <span class="font-medium text-muted">{{ month.slice(0, 4) }}</span></h2>
          <span class="flex gap-2">
            <button type="button" :aria-label="t('calendar.prevMonth')" class="grid size-11 place-items-center rounded-full border border-line bg-white transition-colors hover:border-accent-500" @click="shiftMonth(-1)">
              <Icon name="lucide:chevron-left" class="size-5" />
            </button>
            <button type="button" :aria-label="t('calendar.nextMonth')" class="grid size-11 place-items-center rounded-full border border-line bg-white transition-colors hover:border-accent-500" @click="shiftMonth(1)">
              <Icon name="lucide:chevron-right" class="size-5" />
            </button>
          </span>
        </div>
        <div class="mt-5 grid grid-cols-7 gap-1.5 text-center text-xs font-semibold tracking-[0.08em] text-muted uppercase" aria-hidden="true">
          <span v-for="(d, i) in t('calendar.weekdays').split(',')" :key="i">{{ d }}</span>
        </div>
        <div role="group" :aria-label="`${monthTitle} ${month.slice(0, 4)}`" class="mt-2 grid grid-cols-7 gap-1.5">
          <button
            v-for="cell in cells"
            :key="cell.iso"
            type="button"
            :disabled="!cell.inMonth"
            :aria-pressed="cell.iso === selected"
            :aria-label="cell.inMonth ? `${formatDate(`${cell.iso}T12:00:00+05:00`)}${cell.has ? ` — ${t('calendar.hasEvents')}` : ''}` : undefined"
            class="flex h-12 flex-col items-center justify-center gap-1.5 rounded-[14px] text-[15px] font-semibold transition-colors sm:h-16 sm:text-base"
            :class="[
              !cell.inMonth ? 'cursor-default text-[#c9c5d6]' : cell.iso === selected ? 'bg-ink text-white' : 'bg-paper text-ink hover:bg-brand-50',
              cell.iso === today && cell.iso !== selected && 'shadow-[inset_0_0_0_2px_var(--color-brand-800)]',
            ]"
            @click="selected = cell.iso"
          >
            <span>{{ cell.day }}</span>
            <span class="size-1.5 rounded-full" :class="cell.has && cell.inMonth ? (cell.iso === selected ? 'bg-accent-400' : 'bg-accent-600') : 'bg-transparent'" />
          </button>
        </div>
        <p class="mt-[18px] flex flex-wrap gap-[18px] text-[13px] text-muted">
          <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-accent-600" />{{ t('calendar.hasEvents') }}</span>
          <span class="flex items-center gap-1.5"><span class="size-3.5 rounded shadow-[inset_0_0_0_2px_var(--color-brand-800)]" />{{ t('calendar.today') }}</span>
        </p>
      </div>

      <!-- Tanlangan kun -->
      <div class="min-w-0 lg:flex-1" aria-live="polite">
        <p class="text-xs font-semibold tracking-[0.18em] text-brand-700 uppercase">{{ t('calendar.selected') }}</p>
        <h2 class="mt-2 font-display text-[34px] font-semibold first-letter:uppercase">{{ selectedLabel }}</h2>
        <ul v-if="dayEvents.length" class="mt-5 flex flex-col gap-3">
          <li v-for="e in dayEvents" :key="e.id" class="group relative rounded-[20px] border border-line bg-white px-5 py-[18px] transition-colors hover:border-accent-500">
            <span class="rounded-full bg-accent-100 px-2.5 py-1 text-xs font-semibold text-accent-700">{{ e.category }}</span>
            <NuxtLink :to="localePath(`/events/${e.slug}`)" class="mt-2.5 block text-[17px] leading-snug font-semibold text-ink">
              <span class="absolute inset-0" aria-hidden="true" />
              {{ e.title }}
            </NuxtLink>
            <p class="mt-2 text-[13px] text-muted">{{ formatDate(e.startsAt, 'time') }}<template v-if="e.location"> · {{ e.location }}</template></p>
          </li>
        </ul>
        <p v-else class="mt-5 rounded-[20px] border border-dashed border-brand-200 p-6 text-center text-muted">{{ t('calendar.none') }}</p>
      </div>
    </section>

    <!-- Yaqin tadbirlar -->
    <section class="mx-auto max-w-7xl px-4 pt-18 pb-24 sm:px-6 lg:px-8">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <h2 class="font-display text-4xl font-semibold sm:text-[40px]">{{ t('calendar.upcoming') }}</h2>
        <div v-if="categories.length > 1" role="group" :aria-label="t('calendar.filter')" class="flex flex-wrap gap-2 text-sm font-semibold">
          <button
            v-for="c in ['', ...categories]"
            :key="c"
            type="button"
            :aria-pressed="filter === c"
            class="rounded-full border px-4 py-2.5 transition-colors"
            :class="filter === c ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
            @click="filter = c"
          >
            {{ c || t('calendar.all') }}
          </button>
        </div>
      </div>
      <div class="mt-7 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        <article v-for="e in shown" :key="e.id" class="group relative rounded-3xl border border-line bg-white p-[26px] transition-colors hover:border-accent-500">
          <div class="flex items-end gap-3">
            <span class="font-display text-[56px] leading-[0.85] font-semibold text-brand-200">{{ formatDate(e.startsAt, 'day') }}</span>
            <span class="text-sm text-muted">{{ formatDate(e.startsAt, 'month') }}, {{ formatDate(e.startsAt, 'weekday') }}</span>
          </div>
          <NuxtLink :to="localePath(`/events/${e.slug}`)" class="mt-5 block text-lg leading-snug font-semibold text-ink">
            <span class="absolute inset-0" aria-hidden="true" />
            {{ e.title }}
          </NuxtLink>
          <p class="mt-3 border-t border-line pt-3.5 text-sm text-muted">{{ formatDate(e.startsAt, 'time') }}<template v-if="e.location"> · {{ e.location }}</template></p>
        </article>
        <article v-if="!shown.length" class="rounded-3xl border border-dashed border-brand-200 p-[26px] text-muted">{{ t('events.empty') }}</article>
        <article class="flex flex-col justify-between gap-4 rounded-3xl bg-brand-900 p-[26px] text-white">
          <p class="font-display text-[26px] font-semibold">{{ t('calendar.plan.title') }}</p>
          <p class="text-[15px] leading-relaxed text-white/70">{{ t('calendar.plan.text') }}</p>
        </article>
      </div>
    </section>
  </div>
</template>
