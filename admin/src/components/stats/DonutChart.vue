<script setup lang="ts">
import { computed, ref } from 'vue'

// Halqa diagramma (manbalar ulushi): bo'lak ustiga kelinsa — markazda nomi va foizi, yonidagi ro'yxat bilan bog'langan
const props = defineProps<{ rows: { k: string; v: number }[]; empty: string }>()
const COLORS = ['#382B85', '#00C48E', '#FDB022', '#7A6FD6', '#F97066', '#B7B2CC']
const active = ref<number | null>(null)
const total = computed(() => props.rows.reduce((s, r) => s + r.v, 0))
const R = 52
const C = 2 * Math.PI * R
const arcs = computed(() => {
  let acc = 0
  return props.rows.map((r, i) => {
    const len = total.value ? (r.v / total.value) * C : 0
    const a = { ...r, i, color: COLORS[i % COLORS.length]!, dash: `${Math.max(0, len - 2)} ${C}`, offset: -acc, pct: total.value ? Math.round((r.v / total.value) * 100) : 0 }
    acc += len
    return a
  })
})
const center = computed(() => (active.value === null ? { top: total.value.toLocaleString('ru-RU'), sub: 'jami' } : { top: `${arcs.value[active.value]!.pct}%`, sub: arcs.value[active.value]!.k }))
</script>

<template>
  <p v-if="!rows.length" class="mt-3 text-[13px] text-muted">{{ empty }}</p>
  <div v-else class="mt-3 flex flex-wrap items-center gap-5">
    <svg viewBox="0 0 140 140" class="size-[140px] shrink-0 -rotate-90" role="img" aria-label="Manbalar ulushi">
      <circle cx="70" cy="70" :r="R" fill="none" stroke="#F0EEF6" stroke-width="18" />
      <circle
        v-for="a in arcs" :key="a.k" cx="70" cy="70" :r="R" fill="none" :stroke="a.color" stroke-linecap="butt"
        :stroke-width="active === a.i ? 22 : 18" :stroke-dasharray="a.dash" :stroke-dashoffset="a.offset" class="cursor-pointer transition-[stroke-width] duration-150"
        @pointerenter="active = a.i" @pointerleave="active = null"
      ><title>{{ a.k }}: {{ a.pct }}%</title></circle>
      <g class="rotate-90" style="transform-origin: 70px 70px">
        <text x="70" y="68" text-anchor="middle" font-size="18" font-weight="700" fill="#13112F">{{ center.top }}</text>
        <text x="70" y="86" text-anchor="middle" font-size="10" fill="#8C88A0">{{ center.sub.length > 16 ? `${center.sub.slice(0, 15)}…` : center.sub }}</text>
      </g>
    </svg>
    <ul class="flex min-w-[150px] flex-1 flex-col gap-1.5">
      <li
        v-for="a in arcs" :key="a.k" class="flex items-center gap-2 rounded-lg px-2 py-1 text-[13px] transition-colors" :class="active === a.i && 'bg-canvas'"
        @pointerenter="active = a.i" @pointerleave="active = null"
      >
        <span class="size-2.5 shrink-0 rounded-full" :style="{ background: a.color }" />
        <span class="min-w-0 flex-1 truncate">{{ a.k }}</span><b class="tabular-nums">{{ a.pct }}%</b>
      </li>
    </ul>
  </div>
</template>
