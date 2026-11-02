<script setup lang="ts">
import type { SdgGoalSummary } from '#shared/types/api'

// BRM aylanasi: 17 segment (BMT rasmiy ranglari), 1-maqsad tepada, soat yo'nalishida.
// Yozuvlar sayt tili bilan almashadi; segmentga sichqoncha/fokus kelsa — chiqib turadi va markazda tafsilot chiqadi.
const props = defineProps<{ goals: SdgGoalSummary[]; impactYear: number }>()

const { t } = useI18n()
const localePath = useLocalePath()

const ICONS = [
  'users', 'soup', 'heart-pulse', 'book-open', 'venus-and-mars', 'glass-water', 'sun', 'trending-up', 'boxes',
  'equal', 'building-2', 'infinity', 'earth', 'fish', 'trees', 'bird', 'flower',
]

// Geometriya: 600 birlikli kvadrat, markaz 300; segmentlar orasida bir xil 5 birlik bo'shliq
const S = 600
const C = 300
const RI = 136
const RO = 294
const GAP = 5
const STEP = 360 / 17
const RAD = Math.PI / 180

const pc = (v: number) => `${((v / S) * 100).toFixed(2)}%`
function arc(r: number, a0: number, a1: number, steps: number) {
  const d = Math.asin(GAP / 2 / r) / RAD
  return Array.from({ length: steps + 1 }, (_, k) => {
    const a = (a0 + d + ((a1 - a0 - 2 * d) * k) / steps) * RAD
    return `${pc(C + r * Math.cos(a))} ${pc(C + r * Math.sin(a))}`
  })
}

const segments = Array.from({ length: 17 }, (_, i) => {
  const a0 = -90 + i * STEP
  const a1 = a0 + STEP
  const mid = (a0 + a1) / 2
  const cos = Math.cos(mid * RAD)
  const sin = Math.sin(mid * RAD)
  const left = cos < -0.001
  return {
    n: i + 1,
    icon: `lucide:${ICONS[i]}`,
    clip: `polygon(${[...arc(RO, a0, a1, 14), ...arc(RI, a0, a1, 6).reverse()].join(', ')})`,
    lift: `translate(${(cos * 2).toFixed(2)}cqw, ${(sin * 2).toFixed(2)}cqw)`,
    rot: `rotate(${mid.toFixed(2)}deg)`,
    left,
  }
})

const active = ref(0)
const goal = computed(() => props.goals.find(g => g.n === active.value))
const urlOf = (n: number) => props.goals.find(g => g.n === n)?.url ?? '/brm'
const rankText = computed(() => {
  const rank = goal.value?.rank
  if (!rank) return t('sdg.notRanked')
  return /[–+-]/.test(rank) ? rank : `#${rank}`
})
const gradient = `linear-gradient(90deg, ${Array.from({ length: 17 }, (_, i) => sdgColor(i + 1)).join(', ')})`
</script>

<template>
  <div data-a11y-keep class="sdg-wheel relative mx-auto aspect-square w-full max-w-[600px]">
    <span class="pointer-events-none absolute -inset-[10%] rounded-full bg-[radial-gradient(closest-side,rgba(0,252,180,0.14),rgba(0,252,180,0)_72%)]" aria-hidden="true" />
    <span class="pointer-events-none absolute -inset-[2.6cqw] rounded-full border border-dashed border-white/15" aria-hidden="true" />

    <NuxtLink
      v-for="s in segments"
      :key="s.n"
      :to="localePath(urlOf(s.n))"
      class="sdg-seg absolute inset-0"
      :aria-label="`${s.n}. ${t(`sdg.short.${s.n}`)}`"
      :style="{
        background: sdgColor(s.n),
        color: sdgInk(s.n),
        clipPath: s.clip,
        '--lift': s.lift,
        transform: active === s.n ? s.lift : 'none',
        opacity: active && active !== s.n ? 0.45 : 1,
      }"
      @mouseenter="active = s.n"
      @mouseleave="active = 0"
      @focus="active = s.n"
      @blur="active = 0"
    >
      <span class="absolute top-1/2 left-1/2 size-0" :style="{ transform: s.rot }" aria-hidden="true">
        <span
          class="absolute flex items-center gap-[0.9cqw]"
          :class="s.left ? 'flex-row-reverse text-right' : 'text-left'"
          :style="{ left: '24.4cqw', top: '-5.4cqw', width: '23.2cqw', height: '10.8cqw', transform: s.left ? 'rotate(180deg)' : 'none' }"
        >
          <span class="sdg-num shrink-0 font-display leading-none font-bold">{{ s.n }}</span>
          <Icon :name="s.icon" class="sdg-icon shrink-0" />
          <span class="sdg-label min-w-0 flex-1 leading-[1.12] font-bold text-balance hyphens-auto">{{ t(`sdg.short.${s.n}`) }}</span>
        </span>
      </span>
    </NuxtLink>

    <!-- Markaz -->
    <div class="sdg-center pointer-events-none absolute top-1/2 left-1/2 flex -translate-1/2 flex-col items-center justify-center rounded-full bg-white text-center text-ink" aria-live="polite">
      <!-- Raqam faqat maqsad tanlanganda; bo'sh holatda — rangli chiziq va sarlavha -->
      <span v-if="active" class="sdg-big font-display leading-none font-semibold">{{ active }}</span>
      <span class="sdg-bar rounded-full" :style="{ background: active ? sdgColor(active) : gradient }" />
      <span class="sdg-title font-bold text-balance" :class="!active && 'sdg-title-idle'">{{ active ? t(`sdg.short.${active}`) : t('sdg.wheel.caption') }}</span>
      <span class="sdg-meta text-muted">{{ active ? `THE Impact ${impactYear} · ${rankText}` : t('sdg.wheel.hint') }}</span>
      <span v-if="active" class="sdg-more inline-flex items-center font-bold text-accent-600">{{ t('sdg.wheel.more') }} →</span>
    </div>
  </div>
</template>

<style scoped>
.sdg-wheel { container-type: inline-size; }

.sdg-seg {
  outline: none;
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.3s, filter 0.3s;
}

.sdg-seg:hover,
.sdg-seg:focus-visible {
  transform: var(--lift) !important;
  opacity: 1 !important;
  filter: brightness(1.06);
}

.sdg-num { font-size: 4.4cqw; }
.sdg-icon { font-size: 3.2cqw; }
.sdg-label { font-size: 1.75cqw; }

.sdg-center {
  width: 42cqw;
  height: 42cqw;
  padding: 0 5cqw;
  box-shadow: 0 0 0 1.2cqw rgb(255 255 255 / 0.07), 0 2cqw 6cqw -2cqw rgb(0 0 0 / 0.55);
}

.sdg-big { font-size: 11cqw; }
.sdg-bar { margin-top: 1.4cqw; width: 7cqw; height: 0.7cqw; }
.sdg-title { margin-top: 1.6cqw; font-size: 2.4cqw; line-height: 1.25; }
.sdg-title-idle { font-size: 3.2cqw; }
.sdg-meta { margin-top: 1cqw; font-size: 1.8cqw; line-height: 1.3; }
.sdg-more { margin-top: 1.4cqw; gap: 0.6cqw; font-size: 1.9cqw; }

/* Tor ekranda segment yozuvlari o'qib bo'lmaydigan darajada kichrayadi — faqat raqam va belgi qoladi */
@container (max-width: 460px) {
  .sdg-label { display: none; }
  .sdg-num { font-size: 6cqw; }
  .sdg-icon { font-size: 4.6cqw; }
  .sdg-title, .sdg-title-idle { font-size: 3.4cqw; }
  .sdg-meta { font-size: 2.8cqw; }
  .sdg-more { font-size: 2.8cqw; }
}
</style>
