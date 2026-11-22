<script setup lang="ts">
import type { PageShowcase } from '#shared/types/api'

// Kartali blok (admin → Sahifalar → «Kartali bloklar»; matndagi [[kartalar-N]] joyida):
// kirish gapi, raqamlar (katta son + nom), ustunlar (raqamli yoki ✓ belgili bandlar; «Nom — izoh»), xulosa gapi.
const props = defineProps<{ data: PageShowcase }>()

// Ustunlar rangi navbat bilan: indigo, yaşil (mint), to'q sariq, ko'k
const TONES = [
  { head: 'bg-brand-800 text-white', num: 'border-brand-200 text-brand-700 group-hover:bg-brand-700 group-hover:text-white', bar: 'bg-brand-700', check: 'bg-brand-50 text-brand-700' },
  { head: 'bg-accent-600 text-white', num: 'border-accent-300 text-accent-700 group-hover:bg-accent-600 group-hover:text-white', bar: 'bg-accent-500', check: 'bg-accent-100 text-accent-700' },
  { head: 'bg-[#c2410c] text-white', num: 'border-orange-200 text-[#c2410c] group-hover:bg-[#c2410c] group-hover:text-white', bar: 'bg-[#c2410c]', check: 'bg-orange-50 text-[#c2410c]' },
  { head: 'bg-[#0369a1] text-white', num: 'border-sky-200 text-[#0369a1] group-hover:bg-[#0369a1] group-hover:text-white', bar: 'bg-[#0369a1]', check: 'bg-sky-50 text-[#0369a1]' },
]
const pad = (n: number) => String(n).padStart(2, '0')
// Bitta ustun bölsa — bandlar ikki ustunli to'r bölib çiqadi
const single = computed(() => props.data.columns.length === 1)
const tone = (ci: number) => TONES[(ci + (props.data.n - 1)) % TONES.length]!
</script>

<template>
  <section class="showcase my-10 rounded-[28px] border border-line bg-white p-3 sm:p-4">
    <p v-if="data.intro" class="flex gap-3 rounded-[20px] bg-gradient-to-br from-brand-50 to-[#f3f0ff] px-5 py-4 text-[17px] leading-relaxed font-semibold text-ink sm:px-6 sm:py-5">
      <Icon name="lucide:sparkles" class="mt-1 shrink-0 text-xl text-brand-600" aria-hidden="true" />
      <span>{{ data.intro }}</span>
    </p>

    <!-- Raqamlar -->
    <dl v-if="data.stats.length" class="mt-3 grid gap-3 sm:mt-4 sm:gap-4" :class="data.stats.length >= 3 ? 'sm:grid-cols-3' : 'sm:grid-cols-2'">
      <div v-for="(s, i) in data.stats" :key="i" class="showcase-item group relative overflow-hidden rounded-[20px] bg-brand-950 px-5 py-5 text-white" :style="{ '--i': i }">
        <span aria-hidden="true" class="absolute -top-10 -right-10 size-28 rounded-full bg-accent-400/25 blur-2xl transition-transform duration-500 group-hover:scale-150" />
        <dd class="relative font-display text-[44px] leading-none font-semibold text-accent-400 tabular-nums">{{ s.value }}</dd>
        <dt class="relative mt-2 text-[15px] leading-snug font-semibold text-white/85">{{ s.label }}</dt>
      </div>
    </dl>

    <div v-if="data.columns.length" class="mt-3 grid gap-3 sm:mt-4 sm:gap-4" :class="!single ? 'md:grid-cols-2' : ''">
      <div v-for="(col, ci) in data.columns" :key="ci" class="rounded-[20px] bg-paper p-3 sm:p-4">
        <h3 class="flex items-center gap-2.5 rounded-2xl px-4 py-3 font-bold" :class="tone(ci).head">
          <Icon :name="`lucide:${col.icon || 'circle-check'}`" class="shrink-0 text-xl" aria-hidden="true" />
          <span class="flex-1">{{ col.title }}</span>
          <span class="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-bold tabular-nums">{{ col.items.length }}</span>
        </h3>
        <ol class="mt-3 grid gap-2" :class="single && 'md:grid-cols-2'">
          <li
            v-for="(item, i) in col.items" :key="i"
            class="showcase-item group relative flex items-center gap-3 overflow-hidden rounded-2xl border border-line bg-white py-3 pr-4 pl-3 transition duration-300 hover:translate-x-1 hover:border-transparent hover:shadow-[0_14px_30px_-22px_rgb(28_21_72/0.55)]"
            :style="{ '--i': i + ci * 4 }"
          >
            <span aria-hidden="true" class="absolute inset-y-0 left-0 w-1 origin-top scale-y-0 transition-transform duration-300 group-hover:scale-y-100" :class="tone(ci).bar" />
            <span v-if="col.style === 'checks'" aria-hidden="true" class="grid size-9 shrink-0 place-items-center self-start rounded-xl transition-transform duration-300 group-hover:scale-110" :class="tone(ci).check">
              <Icon name="lucide:check" class="text-lg" />
            </span>
            <span v-else aria-hidden="true" class="grid size-9 shrink-0 place-items-center rounded-xl border text-[13px] font-extrabold tabular-nums transition-colors duration-300" :class="tone(ci).num">{{ pad(i + 1) }}</span>
            <span class="min-w-0 flex-1 leading-snug">
              <span class="block font-semibold text-ink" :class="col.style === 'checks' && 'text-[15px] font-medium'">{{ item.name }}</span>
              <span v-if="item.note" class="mt-0.5 block text-[13px] text-muted">{{ item.note }}</span>
            </span>
          </li>
        </ol>
      </div>
    </div>

    <p v-if="data.outro" class="mt-3 flex gap-3 rounded-[20px] border border-accent-300/60 bg-accent-100/50 px-5 py-4 leading-relaxed text-ink sm:mt-4 sm:px-6">
      <Icon name="lucide:award" class="mt-0.5 shrink-0 text-xl text-accent-700" aria-hidden="true" />
      <span>{{ data.outro }}</span>
    </p>
  </section>
</template>

<style scoped>
.showcase-item { animation: showcase-in 0.55s cubic-bezier(0.2, 0.8, 0.2, 1) both; animation-delay: calc(var(--i) * 60ms); }
@keyframes showcase-in { from { opacity: 0; transform: translateY(10px); } }
@media (prefers-reduced-motion: reduce) {
  .showcase-item { animation: none; }
}
</style>
