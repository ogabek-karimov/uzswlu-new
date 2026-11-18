<script setup lang="ts">
// Bo'lim orqasidagi mavzuli fon. Kontentni bosmaydi: juda xira, bosilmaydi (pointer-events yo'q), ekran o'quvchilardan yashirin.
//   glyphs    — turli tillardagi harflar buluti (til universiteti uchun): «Universitet haqida» va tezkor havolalar ortida
//   newsprint — gazeta yarim-tonli nuqtalari va halqalar: yangiliklar ortida
defineProps<{ variant: 'glyphs' | 'newsprint' }>()

// [belgi, chap, tepa, o'lcham, burilish]: chekkalarga joylashtirilgan, qat'iy qiymatlar (server va brauzerda bir xil)
const glyphs = [
  ['A', '3%', '4%', '9rem', -12], ['Ж', '88%', '2%', '8rem', 10], ['你', '1%', '48%', '8rem', 8], ['あ', '91%', '44%', '9rem', -8],
  ['ع', '6%', '84%', '7rem', 6], ['ß', '82%', '80%', '8rem', -10], ['한', '47%', '-3%', '7rem', 5], ['Ñ', '58%', '88%', '7rem', -6],
] as const
</script>

<template>
  <div class="relative isolate overflow-hidden">
    <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <template v-if="variant === 'glyphs'">
        <span class="absolute -top-28 -left-24 size-[26rem] rounded-full bg-accent-100/60 blur-3xl" />
        <span class="absolute top-1/3 -right-28 size-[28rem] rounded-full bg-brand-100/70 blur-3xl" />
        <span
          v-for="g in glyphs"
          :key="g[0]"
          class="absolute font-display leading-none font-semibold text-brand-600/[0.055] select-none"
          :style="{ left: g[1], top: g[2], fontSize: g[3], transform: `rotate(${g[4]}deg)` }"
        >{{ g[0] }}</span>
      </template>

      <template v-else>
        <span class="absolute -top-20 -right-20 size-[26rem] rounded-full bg-brand-100/70 blur-3xl" />
        <span class="backdrop-dots absolute inset-0" />
        <svg class="absolute -top-24 -right-24 size-[30rem] text-brand-300/35" viewBox="0 0 400 400" fill="none" stroke="currentColor" stroke-width="1">
          <circle cx="200" cy="200" r="60" /><circle cx="200" cy="200" r="100" /><circle cx="200" cy="200" r="140" /><circle cx="200" cy="200" r="180" />
        </svg>
        <span class="backdrop-rules absolute bottom-0 left-0 h-2/5 w-1/3" />
      </template>
    </div>
    <slot />
  </div>
</template>

<style scoped>
/* Gazeta yarim-toni: nuqtalar o'ng-tepadan chap-pastga so'nadi */
.backdrop-dots {
  background-image: radial-gradient(circle, rgb(70 55 163 / 0.2) 1.2px, transparent 1.7px);
  background-size: 20px 20px;
  mask-image: linear-gradient(205deg, #000 0%, transparent 52%);
}
/* Matn qatorlarini eslatuvchi ingichka chiziqlar, chap-pastda */
.backdrop-rules {
  background-image: repeating-linear-gradient(to bottom, transparent 0 21px, rgb(70 55 163 / 0.07) 21px 22px);
  mask-image: linear-gradient(to top right, #000 0%, transparent 85%);
}
</style>
