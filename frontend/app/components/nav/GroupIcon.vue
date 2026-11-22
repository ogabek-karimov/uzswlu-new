<script setup lang="ts">
// Menyu bo'limi belgisi: BRM uchun — 17 rangli BMT halqasi (sahifadagi BRM g'ildiragi bilan bir xil ranglar), qolganlari — lucide ikonka
// label — halqa o'rtasidagi yozuv (faqat katta belgida, masalan «17»)
defineProps<{ id: string; label?: string }>()

// 24×24 da halqa: 17 segment, orasida kichik bo'shliq, 1-maqsad tepada, soat yo'nalishida
const C = 12
const RO = 11.5
const RI = 7
const GAP = 2.2   // daraja
const STEP = 360 / 17
const RAD = Math.PI / 180
const pt = (r: number, a: number) => `${(C + r * Math.sin(a * RAD)).toFixed(3)} ${(C - r * Math.cos(a * RAD)).toFixed(3)}`
const segments = Array.from({ length: 17 }, (_, i) => {
  const a0 = i * STEP + GAP / 2
  const a1 = (i + 1) * STEP - GAP / 2
  return {
    color: sdgColor(i + 1),
    d: `M${pt(RO, a0)}A${RO} ${RO} 0 0 1 ${pt(RO, a1)}L${pt(RI, a1)}A${RI} ${RI} 0 0 0 ${pt(RI, a0)}Z`,
  }
})
</script>

<template>
  <svg v-if="id === 'sdg'" viewBox="0 0 24 24" aria-hidden="true" class="shrink-0">
    <!-- Faqat segmentlar aylanadi (katta menyuda hover), raqam joyida qoladi -->
    <g class="transition-transform duration-500 [transform-box:view-box] [transform-origin:center] group-hover/ov:rotate-[21deg] motion-reduce:transition-none">
      <path v-for="(s, i) in segments" :key="i" :d="s.d" :fill="s.color" />
    </g>
    <text v-if="label" x="12" y="12.4" text-anchor="middle" dominant-baseline="middle" font-size="8.6" font-weight="800" fill="#1c1548" style="font-family: var(--font-display, inherit); letter-spacing: -0.2px">{{ label }}</text>
  </svg>
  <Icon v-else :name="groupIcon(id)" />
</template>
