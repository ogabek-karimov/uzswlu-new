<script setup lang="ts">
import { computed, ref } from 'vue'

// Statistika → asosiy grafik: sahifa ko'rishlari, tashrifchilar va oldingi davr (shtrix). Silliq (monoton) egri chiziqlar —
// nolga tushmaydi va «o'ynab» ketmaydi; Y o'qida yaxlit qiymatlar; sichqoncha/barmoq bilan nuqta tanlanadi (tooltip + vertikal chiziq).
export type Point = { label: string; full: string; views: number; visitors: number; prev: number }
const props = defineProps<{ points: Point[]; prevLabel: string }>()

const W = 760
const H = 280
const PAD = { l: 44, r: 12, t: 16, b: 30 }
const show = ref({ views: true, visitors: true, prev: true })
const hover = ref<number | null>(null)

// Y o'qi: 1-2-5 qadamli yaxlit belgilar
const scale = computed(() => {
  const keys = (['views', 'visitors', 'prev'] as const).filter(k => show.value[k])
  const top = Math.max(1, ...props.points.flatMap(p => keys.map(k => p[k])))
  const raw = top / 4
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 5, 10].map(m => m * mag).find(s => s >= raw) ?? raw
  const max = Math.ceil((top * 1.08) / step) * step // tepada ozgina joy — eng yuqori nuqta yozuvi sig'sin
  return { max, ticks: Array.from({ length: Math.round(max / step) + 1 }, (_, i) => i * step) }
})
const n = computed(() => props.points.length)
const x = (i: number) => PAD.l + (n.value > 1 ? (i * (W - PAD.l - PAD.r)) / (n.value - 1) : (W - PAD.l - PAD.r) / 2)
const y = (v: number) => PAD.t + (H - PAD.t - PAD.b) * (1 - v / scale.value.max)

// Monoton kubik egri (Fritsch–Carlson): qiymatlar orasida chiqib ketmaydi
function smooth(vals: number[]) {
  const pts = vals.map((v, i) => [x(i), y(v)] as const)
  if (pts.length < 2) return pts.length ? `M${pts[0]![0]} ${pts[0]![1]}` : ''
  const d = pts.slice(1).map((p, i) => (p[1] - pts[i]![1]) / (p[0] - pts[i]![0]))
  const m = pts.map((_, i) => (i === 0 ? d[0]! : i === pts.length - 1 ? d[i - 1]! : d[i - 1]! * d[i]! <= 0 ? 0 : (d[i - 1]! + d[i]!) / 2))
  for (let i = 0; i < d.length; i++) {
    if (d[i] === 0) { m[i] = 0; m[i + 1] = 0; continue }
    const a = m[i]! / d[i]!, b = m[i + 1]! / d[i]!, s = a * a + b * b
    if (s > 9) { const t = 3 / Math.sqrt(s); m[i] = t * a * d[i]!; m[i + 1] = t * b * d[i]! }
  }
  let out = `M${pts[0]![0].toFixed(1)} ${pts[0]![1].toFixed(1)}`
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i]!, [x1, y1] = pts[i + 1]!, h = (x1 - x0) / 3
    out += ` C${(x0 + h).toFixed(1)} ${(y0 + m[i]! * h).toFixed(1)} ${(x1 - h).toFixed(1)} ${(y1 - m[i + 1]! * h).toFixed(1)} ${x1.toFixed(1)} ${y1.toFixed(1)}`
  }
  return out
}
const line = (k: 'views' | 'visitors' | 'prev') => smooth(props.points.map(p => p[k]))
const area = computed(() => (n.value ? `${line('views')} L${x(n.value - 1)} ${H - PAD.b} L${x(0)} ${H - PAD.b} Z` : ''))
const peak = computed(() => props.points.reduce((best, p, i) => (p.views > (props.points[best]?.views ?? -1) ? i : best), 0))
const xTicks = computed(() => {
  const step = Math.max(1, Math.ceil(n.value / 8))
  // oxirgi belgi doim; unga juda yaqin oldingisi tushiriladi (yozuvlar ustma-ust tushmasin)
  return props.points.map((p, i) => ({ i, label: p.label })).filter(t => t.i === n.value - 1 || (t.i % step === 0 && n.value - 1 - t.i >= step * 0.6))
})
const fmt = (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(v >= 10000 ? 0 : 1).replace('.', ',')}k` : String(v))

function pick(e: PointerEvent) {
  const box = (e.currentTarget as SVGElement).getBoundingClientRect()
  const px = ((e.clientX - box.left) / box.width) * W
  const i = Math.round(((px - PAD.l) / (W - PAD.l - PAD.r)) * (n.value - 1))
  hover.value = Math.min(n.value - 1, Math.max(0, i))
}
const tip = computed(() => {
  if (hover.value === null) return null
  const p = props.points[hover.value]!
  const diff = p.prev ? Math.round(((p.views - p.prev) / p.prev) * 100) : null
  return { p, diff, left: `${(x(hover.value) / W) * 100}%`, right: x(hover.value) > W * 0.62 }
})
const LEGEND = [
  { k: 'views', label: 'Sahifa körişlari', color: '#382B85' },
  { k: 'visitors', label: 'Taşrifçilar', color: '#00C48E' },
] as const
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="l in [...LEGEND, { k: 'prev', label: prevLabel, color: '#B7B2CC' }] as const" :key="l.k" type="button" :aria-pressed="show[l.k]"
        class="inline-flex h-8 items-center gap-2 rounded-full border px-3 text-xs font-semibold transition-colors"
        :class="show[l.k] ? 'border-line bg-white text-ink' : 'border-transparent bg-[#F4F3F8] text-subtle line-through'"
        @click="show[l.k] = !show[l.k]"
      >
        <span class="h-[3px] w-4 rounded-full" :style="{ background: l.k === 'prev' ? `repeating-linear-gradient(90deg, ${l.color} 0 4px, transparent 4px 7px)` : l.color, opacity: show[l.k] ? 1 : 0.4 }" />{{ l.label }}
      </button>
    </div>

    <div class="relative mt-3">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Taşriflar grafigi" class="block h-auto w-full touch-pan-y select-none" @pointermove="pick" @pointerdown="pick" @pointerleave="hover = null">
        <defs>
          <linearGradient id="tc-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#382B85" stop-opacity="0.22" /><stop offset="100%" stop-color="#382B85" stop-opacity="0" /></linearGradient>
        </defs>
        <g v-for="t in scale.ticks" :key="t">
          <line :x1="PAD.l" :x2="W - PAD.r" :y1="y(t)" :y2="y(t)" :stroke="t ? '#F0EEF6' : '#E2DFEC'" />
          <text :x="PAD.l - 8" :y="y(t) + 4" text-anchor="end" font-size="11" fill="#8C88A0">{{ fmt(t) }}</text>
        </g>
        <path v-if="show.views" :d="area" fill="url(#tc-fill)" />
        <path v-if="show.prev" :d="line('prev')" fill="none" stroke="#B7B2CC" stroke-width="2" stroke-dasharray="5 5" stroke-linecap="round" />
        <path v-if="show.visitors" :d="line('visitors')" fill="none" stroke="#00C48E" stroke-width="2.25" stroke-linecap="round" />
        <path v-if="show.views" :d="line('views')" fill="none" stroke="#382B85" stroke-width="2.75" stroke-linecap="round" />
        <g v-if="show.views && points[peak]?.views && hover === null">
          <circle :cx="x(peak)" :cy="y(points[peak]!.views)" r="4.5" fill="#fff" stroke="#382B85" stroke-width="2.5" />
          <text :x="x(peak)" :y="y(points[peak]!.views) - 11" text-anchor="middle" font-size="11" font-weight="700" fill="#382B85">{{ points[peak]!.views }}</text>
        </g>
        <g v-if="hover !== null">
          <line :x1="x(hover)" :x2="x(hover)" :y1="PAD.t" :y2="H - PAD.b" stroke="#382B85" stroke-opacity="0.25" stroke-dasharray="3 3" />
          <circle v-if="show.prev" :cx="x(hover)" :cy="y(points[hover]!.prev)" r="3.5" fill="#fff" stroke="#B7B2CC" stroke-width="2" />
          <circle v-if="show.visitors" :cx="x(hover)" :cy="y(points[hover]!.visitors)" r="4" fill="#fff" stroke="#00C48E" stroke-width="2.5" />
          <circle v-if="show.views" :cx="x(hover)" :cy="y(points[hover]!.views)" r="5" fill="#fff" stroke="#382B85" stroke-width="3" />
        </g>
        <text v-for="t in xTicks" :key="t.i" :x="x(t.i)" :y="H - 8" text-anchor="middle" font-size="11" :fill="hover === t.i ? '#13112F' : '#8C88A0'">{{ t.label }}</text>
      </svg>

      <div
        v-if="tip" class="pointer-events-none absolute top-2 z-10 w-[200px] rounded-xl bg-night px-3.5 py-3 text-xs text-white shadow-xl"
        :style="tip.right ? { right: `calc(100% - ${tip.left} + 12px)` } : { left: `calc(${tip.left} + 12px)` }"
      >
        <p class="font-bold">{{ tip.p.full }}</p>
        <p class="mt-2 flex justify-between gap-3"><span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-[#8B7FE0]" />Körişlar</span><b class="tabular-nums">{{ tip.p.views }}</b></p>
        <p class="mt-1 flex justify-between gap-3"><span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-mint" />Taşrifçilar</span><b class="tabular-nums">{{ tip.p.visitors }}</b></p>
        <p class="mt-1 flex justify-between gap-3 text-white/60"><span>{{ prevLabel }}</span><b class="tabular-nums">{{ tip.p.prev }}</b></p>
        <p v-if="tip.diff !== null" class="mt-2 border-t border-white/10 pt-2 font-semibold" :class="tip.diff >= 0 ? 'text-mint' : 'text-[#FDA29B]'">{{ tip.diff >= 0 ? '▲' : '▼' }} {{ Math.abs(tip.diff) }}% oldingi davrga</p>
      </div>
    </div>
  </div>
</template>
