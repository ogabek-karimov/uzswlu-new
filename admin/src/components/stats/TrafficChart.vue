<script setup lang="ts">
import { computed, ref } from 'vue'

// Statistika → asosiy grafik: har kun/soat/oy — HAQIQIY qiymat ustun bilan (silliqlaş yöq, nol kun — böş).
// Sahifa körişlari — keng ustun, taşrifçilar — uning içida tor ustun, oldingi davr — shtrix çiziq (töğri kesmalar).
// Ranglar validator bilan tekşirilgan (CVD ΔE 23, kontrast ≥ 3:1). Sichqoncha/barmoq bilan ustun tanlanadi (tooltip).
export type Point = { label: string; full: string; views: number; visitors: number; prev: number }
const props = defineProps<{ points: Point[]; prevLabel: string }>()

const W = 760
const H = 230
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
const slot = computed(() => (W - PAD.l - PAD.r) / Math.max(1, n.value))
const x = (i: number) => PAD.l + (i + 0.5) * slot.value
const y = (v: number) => PAD.t + (H - PAD.t - PAD.b) * (1 - v / scale.value.max)
const C = { views: '#5B4BC4', visitors: '#0E9A70', prev: '#A8A3BF' }
// Tepasi 3px yumaloq, pasti o'qqa tegib turadigan ustun; qiymat 0 bölsa — çizilmaydi
function bar(i: number, v: number, wf: number) {
  if (!v) return ''
  const w = Math.max(2, slot.value * wf), x0 = x(i) - w / 2, top = y(v), base = H - PAD.b, r = Math.min(3, w / 2, base - top)
  return `M${x0} ${base} V${top + r} Q${x0} ${top} ${x0 + r} ${top} H${x0 + w - r} Q${x0 + w} ${top} ${x0 + w} ${top + r} V${base} Z`
}
const prevLine = computed(() => props.points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(p.prev).toFixed(1)}`).join(' '))
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
  const i = Math.floor((px - PAD.l) / slot.value)
  hover.value = Math.min(n.value - 1, Math.max(0, i))
}
const tip = computed(() => {
  if (hover.value === null) return null
  const p = props.points[hover.value]!
  const diff = p.prev ? Math.round(((p.views - p.prev) / p.prev) * 100) : null
  return { p, diff, left: `${(x(hover.value) / W) * 100}%`, right: x(hover.value) > W * 0.62 }
})
const LEGEND = [
  { k: 'views', label: 'Sahifa körişlari', color: C.views },
  { k: 'visitors', label: 'Taşrifçilar', color: C.visitors },
] as const
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="l in [...LEGEND, { k: 'prev', label: prevLabel, color: C.prev }] as const" :key="l.k" type="button" :aria-pressed="show[l.k]"
        class="inline-flex h-8 items-center gap-2 rounded-full border px-3 text-xs font-semibold transition-colors"
        :class="show[l.k] ? 'border-line bg-white text-ink' : 'border-transparent bg-[#F4F3F8] text-subtle line-through'"
        @click="show[l.k] = !show[l.k]"
      >
        <span :class="l.k === 'prev' ? 'h-[3px] w-4 rounded-full' : 'size-2.5 rounded-[3px]'" :style="{ background: l.k === 'prev' ? `repeating-linear-gradient(90deg, ${l.color} 0 4px, transparent 4px 7px)` : l.color, opacity: show[l.k] ? 1 : 0.4 }" />{{ l.label }}
      </button>
    </div>

    <div class="relative mt-3">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Taşriflar grafigi" class="block h-auto w-full touch-pan-y select-none" @pointermove="pick" @pointerdown="pick" @pointerleave="hover = null">
        <g v-for="t in scale.ticks" :key="t">
          <line :x1="PAD.l" :x2="W - PAD.r" :y1="y(t)" :y2="y(t)" :stroke="t ? '#F0EEF6' : '#D9D5E6'" />
          <text :x="PAD.l - 8" :y="y(t) + 4" text-anchor="end" font-size="11" fill="#8C88A0">{{ fmt(t) }}</text>
        </g>
        <rect v-if="hover !== null" :x="x(hover) - slot / 2" :y="PAD.t" :width="slot" :height="H - PAD.t - PAD.b" fill="#5B4BC4" fill-opacity="0.07" rx="4" />
        <g v-for="(p, i) in points" :key="i">
          <path v-if="show.views" :d="bar(i, p.views, 0.68)" :fill="C.views" :fill-opacity="hover === null || hover === i ? 1 : 0.45" />
          <path v-if="show.visitors" :d="bar(i, p.visitors, show.views ? 0.3 : 0.68)" :fill="C.visitors" :fill-opacity="hover === null || hover === i ? 1 : 0.45" />
        </g>
        <path v-if="show.prev && n > 1" :d="prevLine" fill="none" :stroke="C.prev" stroke-width="2" stroke-dasharray="4 4" stroke-linejoin="round" />
        <text v-if="show.views && points[peak]?.views && hover === null" :x="x(peak)" :y="y(points[peak]!.views) - 7" text-anchor="middle" font-size="11" font-weight="700" fill="#13112F">{{ points[peak]!.views }}</text>
        <text v-for="t in xTicks" :key="t.i" :x="x(t.i)" :y="H - 8" text-anchor="middle" font-size="11" :fill="hover === t.i ? '#13112F' : '#8C88A0'">{{ t.label }}</text>
      </svg>

      <div
        v-if="tip" class="pointer-events-none absolute top-2 z-10 w-[200px] rounded-xl bg-night px-3.5 py-3 text-xs text-white shadow-xl"
        :style="tip.right ? { right: `calc(100% - ${tip.left} + 12px)` } : { left: `calc(${tip.left} + 12px)` }"
      >
        <p class="font-bold">{{ tip.p.full }}</p>
        <p class="mt-2 flex justify-between gap-3"><span class="flex items-center gap-1.5"><span class="size-2 rounded-sm bg-[#8B7FE0]" />Körişlar</span><b class="tabular-nums">{{ tip.p.views }}</b></p>
        <p class="mt-1 flex justify-between gap-3"><span class="flex items-center gap-1.5"><span class="size-2 rounded-sm bg-[#2FC08F]" />Taşrifçilar</span><b class="tabular-nums">{{ tip.p.visitors }}</b></p>
        <p class="mt-1 flex justify-between gap-3 text-white/60"><span>{{ prevLabel }}</span><b class="tabular-nums">{{ tip.p.prev }}</b></p>
        <p v-if="tip.diff !== null" class="mt-2 border-t border-white/10 pt-2 font-semibold" :class="tip.diff >= 0 ? 'text-mint' : 'text-[#FDA29B]'">{{ tip.diff >= 0 ? '▲' : '▼' }} {{ Math.abs(tip.diff) }}% oldingi davrga</p>
      </div>
    </div>
  </div>
</template>
