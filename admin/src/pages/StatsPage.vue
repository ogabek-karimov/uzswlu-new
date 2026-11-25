<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import DonutChart from '@/components/stats/DonutChart.vue'
import TrafficChart, { type Point } from '@/components/stats/TrafficChart.vue'
import { api } from '@/lib/api'

// Sayt statistikasi — o'zimizning backend'da, cookie'siz va shaxsiy ma'lumotsiz
type Summary = { visitors: number; visits: number; pageviews: number; duration: number; bounce: number }
type Row = { k: string; v: number }
type Stats = { range: string; current: Summary; previous: Summary; unit: 'hour' | 'day' | 'month'; series: { t: string; views: number; visitors: number }[]; prevSeries?: { t: string; views: number; visitors: number }[]; sources: Row[]; countries: Row[]; langs: Row[]; pages: Row[]; searches: Row[]; events: Row[] }

const RANGES = [['1', 'Bugun'], ['7', '7 kun'], ['30', '30 kun'], ['365', '12 oy']] as const
const range = ref<(typeof RANGES)[number][0]>('30')
const data = ref<Stats | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    data.value = await api.get<Stats>('/panel/stats', { range: range.value })
  }
  finally {
    loading.value = false
  }
}
onMounted(load)
watch(range, load)

const num = (n: number) => (n >= 1e6 ? `${(n / 1e6).toFixed(1).replace('.', ',')} mln` : Math.round(n).toLocaleString('ru-RU'))
const dur = (s: number) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`
function trend(cur: number, prev: number, lowerIsBetter = false) {
  if (!prev) return { text: cur ? 'yangi davr' : '—', good: true }
  const d = Math.round(((cur - prev) / prev) * 100)
  const up = d >= 0
  return { text: `${up ? '▲' : '▼'} ${Math.abs(d)}% oldingi davrga`, good: lowerIsBetter ? !up : up }
}
const kpis = computed(() => {
  const c = data.value?.current
  const p = data.value?.previous
  if (!c || !p) return []
  return [
    { label: 'Taşrifçilar', value: num(c.visitors), ...trend(c.visitors, p.visitors) },
    { label: 'Taşriflar', value: num(c.visits), ...trend(c.visits, p.visits) },
    { label: 'Sahifa körişlari', value: num(c.pageviews), ...trend(c.pageviews, p.pageviews) },
    { label: 'Örtaça vaqt', value: dur(c.duration), ...trend(c.duration, p.duration) },
    { label: 'Bitta sahifada çiqqan', value: `${Math.round(c.bounce * 100)}%`, ...trend(c.bounce, p.bounce, true) },
  ]
})

// Grafik: bo'sh kunlar ham nol bilan chiziladi; har nuqtaga oldingi davrdagi xuddi shu o'rindagi qiymat (taqqoslash chizig'i)
const MONTHS = ['yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun', 'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr']
const points = computed<Point[]>(() => {
  const d = data.value
  if (!d) return []
  const cut = d.unit === 'hour' ? 13 : d.unit === 'day' ? 10 : 7
  const map = new Map(d.series.map(s => [s.t.slice(0, cut), s]))
  const prevMap = new Map((d.prevSeries ?? []).map(s => [s.t.slice(0, cut), s]))
  const out: Point[] = []
  const now = new Date(Date.now() + 5 * 3600 * 1000)
  const n = d.unit === 'hour' ? 24 : d.unit === 'day' ? Number(d.range) : 12
  for (let i = n - 1; i >= 0; i--) {
    const t = new Date(now)
    const p = new Date(now)
    if (d.unit === 'hour') { t.setUTCHours(t.getUTCHours() - i); p.setUTCHours(p.getUTCHours() - i - 24) }
    else if (d.unit === 'day') { t.setUTCDate(t.getUTCDate() - i); p.setUTCDate(p.getUTCDate() - i - n) }
    else { t.setUTCMonth(t.getUTCMonth() - i, 1); p.setUTCMonth(p.getUTCMonth() - i - 12, 1) }
    const iso = t.toISOString()
    const s = map.get(iso.slice(0, cut))
    const day = `${Number(iso.slice(8, 10))}-${MONTHS[Number(iso.slice(5, 7)) - 1]}`
    out.push({
      label: d.unit === 'hour' ? `${iso.slice(11, 13)}:00` : d.unit === 'day' ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}` : `${iso.slice(5, 7)}.${iso.slice(2, 4)}`,
      full: d.unit === 'hour' ? `${day}, ${iso.slice(11, 13)}:00` : d.unit === 'day' ? `${day}, ${iso.slice(0, 4)}` : `${MONTHS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`,
      views: s?.views ?? 0, visitors: s?.visitors ?? 0, prev: prevMap.get(p.toISOString().slice(0, cut))?.views ?? 0,
    })
  }
  return out
})
const prevLabel = computed(() => ({ '1': 'Kecha', '7': 'Oldingi 7 kun', '30': 'Oldingi 30 kun', '365': 'Oldingi 12 oy' })[range.value])

const LANG_NAMES: Record<string, string> = { uz: 'Özbekça', ru: 'Rusça', en: 'Inglizça', zh: 'Xitoyça' }
const COUNTRY: Record<string, string> = { UZ: 'Özbekiston', RU: 'Rossiya', KZ: 'Qozoğiston', CN: 'Xitoy', TR: 'Turkiya', KG: 'Qirğiziston', TJ: 'Tojikiston', US: 'AQŞ', KR: 'Koreya', DE: 'Germaniya' }
function pct(rows: Row[], name: (k: string) => string = k => k) {
  const total = rows.reduce((s, r) => s + r.v, 0) || 1
  const top = rows[0]?.v || 1
  return rows.map(r => ({ k: name(r.k), v: `${Math.round((r.v / total) * 100)}%`, w: `${Math.round((r.v / top) * 100)}%` }))
}
const lists = computed(() => data.value
  ? [
      { title: 'Davlatlar', sub: 'Taşrifçilar uluşi', color: '#00C48E', rows: pct(data.value.countries, k => COUNTRY[k] ?? k), empty: 'Serverda GeoIP (Cloudflare yoki nginx) ulanganda körinadi — IP manzillar saqlanmaydi' },
      { title: 'Sayt tili', sub: 'Qaysi tilda öqilmoqda', color: '#FDB022', rows: pct(data.value.langs, k => LANG_NAMES[k] ?? k), empty: 'Hali ma’lumot yöq' },
    ]
  : [])
const lists2 = computed(() => data.value
  ? [
      { title: 'Köp öqilgan sahifalar', sub: 'Körişlar soni', rows: data.value.pages },
      { title: 'Saytdan qidirilgan sözlar', sub: 'Qidiruv maydoni', rows: data.value.searches },
      { title: 'Muhim harakatlar', sub: 'Tugma va yuklab olişlar', rows: data.value.events },
    ]
  : [])
const empty = computed(() => !!data.value && !data.value.current.pageviews)
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Statistika</h1>
        <p class="mt-1.5 text-[15px] text-muted">Bepul va cookie’siz — şaxsiy ma’lumot yiğilmaydi, banner kerak emas.</p>
      </div>
      <div role="tablist" aria-label="Davr" class="flex gap-0.5 rounded-xl border border-line bg-white p-1">
        <button v-for="r in RANGES" :key="r[0]" type="button" role="tab" :aria-selected="range === r[0]" class="h-[34px] rounded-[9px] px-3.5 text-[13px] font-semibold" :class="range === r[0] ? 'bg-ink text-white' : 'text-muted'" @click="range = r[0]">{{ r[1] }}</button>
      </div>
    </div>

    <p v-if="empty" class="rounded-2xl bg-[#FEF3DC] px-4 py-3 text-sm text-[#8A5A00]">Bu davrda hali taşrif yöq. Statistika sayt ochilgan paytdan boşlab yiğiladi (hozir — localhost’dagi sinov taşriflari).</p>

    <div class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5" :class="loading && 'opacity-60'">
      <div v-for="k in kpis" :key="k.label" class="card px-4 py-3.5">
        <p class="text-[13px] text-muted">{{ k.label }}</p>
        <p class="mt-1.5 text-[26px] font-bold">{{ k.value }}</p>
        <p class="mt-0.5 text-xs font-semibold" :class="k.good ? 'text-[#0B5A43]' : 'text-[#B42318]'">{{ k.text }}</p>
      </div>
    </div>

    <section class="card px-5 py-[18px]">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="text-base font-bold">Taşriflar va sahifa körişlari</h2>
        <span class="text-xs text-muted">Ustun ustiga keling — batafsil</span>
      </div>
      <TrafficChart class="mt-3" :points="points" :prev-label="prevLabel" />
    </section>

    <div class="grid gap-[18px] lg:grid-cols-3">
      <section class="card px-5 py-[18px]">
        <h3 class="text-base font-bold">Qayerdan kelişdi</h3>
        <p class="text-xs text-subtle">Manbalar uluşi</p>
        <DonutChart :rows="data?.sources ?? []" empty="Hali ma’lumot yöq" />
      </section>
      <section v-for="L in lists" :key="L.title" class="card px-5 py-[18px]">
        <h3 class="text-base font-bold">{{ L.title }}</h3>
        <p class="text-xs text-subtle">{{ L.sub }}</p>
        <p v-if="!L.rows.length" class="mt-3 text-[13px] leading-normal text-muted">{{ L.empty }}</p>
        <ul class="mt-3 flex flex-col gap-2.5">
          <li v-for="r in L.rows" :key="r.k">
            <span class="flex justify-between text-[13px]"><span>{{ r.k }}</span><b>{{ r.v }}</b></span>
            <span class="mt-1 block h-1.5 overflow-hidden rounded-full bg-[#F0EEF6]"><span class="block h-full rounded-full" :style="{ width: r.w, background: L.color }" /></span>
          </li>
        </ul>
      </section>
    </div>

    <div class="grid gap-[18px] lg:grid-cols-3">
      <section v-for="L in lists2" :key="L.title" class="card px-5 py-[18px]">
        <h3 class="text-base font-bold">{{ L.title }}</h3>
        <p class="text-xs text-subtle">{{ L.sub }}</p>
        <p v-if="!L.rows.length" class="mt-3 text-[13px] text-muted">Hali ma’lumot yöq</p>
        <ol class="mt-3 flex flex-col">
          <li v-for="r in L.rows" :key="r.k" class="flex justify-between gap-3 border-t border-[#F0EEF6] py-2 text-[13px] first:border-0"><span class="min-w-0 truncate">{{ r.k }}</span><b class="tabular-nums">{{ r.v.toLocaleString('ru-RU') }}</b></li>
        </ol>
      </section>
    </div>
  </div>
</template>
