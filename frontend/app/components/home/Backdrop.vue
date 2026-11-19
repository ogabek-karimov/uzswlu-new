<script setup lang="ts">
// Bo'lim orqasidagi mavzuli fon. Kontentni bosmaydi: juda xira, bosilmaydi (pointer-events yo'q), ekran o'quvchilardan yashirin.
//   glyphs    — turli tillardagi harflar buluti (til universiteti uchun): «Universitet haqida» va tezkor havolalar ortida
//   reel      — universitet hayoti suratlari «plyonkasi» (qarama-qarshi yo'nalishda sekin suriladi): yangiliklar ortida;
//               pastki chetda qiya kesim va yorug'lik chizig'i — keyingi bo'limga o'tish
defineProps<{ variant: 'glyphs' | 'reel' | 'ornament' | 'mint' }>()

// Plyonka qatorlari: har qatorda suratlar ketma-ketligi (ikki marta takrorlanadi — uzluksiz aylanish uchun)
const reels = [
  { top: '3%', rev: false, imgs: ['conference', 'graduation', 'library', 'world', 'festival', 'graduation'] },
  { top: '27%', rev: true, imgs: ['world', 'festival', 'conference', 'library', 'graduation', 'festival'] },
  { top: '51%', rev: false, imgs: ['library', 'world', 'graduation', 'festival', 'conference', 'world'] },
  { top: '75%', rev: true, imgs: ['festival', 'conference', 'world', 'graduation', 'library', 'conference'] },
] as const

// [belgi, chap, tepa, o'lcham, burilish]: chekkalarga joylashtirilgan, qat'iy qiymatlar (server va brauzerda bir xil)
const glyphs = [
  ['A', '3%', '4%', '9rem', -12], ['Ж', '88%', '2%', '8rem', 10], ['你', '1%', '48%', '8rem', 8], ['あ', '91%', '44%', '9rem', -8],
  ['ع', '6%', '84%', '7rem', 6], ['ß', '82%', '80%', '8rem', -10], ['한', '47%', '-3%', '7rem', 5], ['Ñ', '58%', '88%', '7rem', -6],
] as const
</script>

<template>
  <div class="relative isolate overflow-hidden">
    <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <template v-if="variant === 'mint'">
        <span class="absolute inset-0 bg-[linear-gradient(160deg,#effcf6_0%,#e2f9ef_50%,#d7f6ea_100%)]" />
        <span class="absolute -top-32 -right-24 size-[30rem] rounded-full bg-white/75 blur-3xl" />
        <span class="absolute -bottom-32 -left-24 size-[28rem] rounded-full bg-accent-300/25 blur-3xl" />
        <span class="absolute inset-0 text-accent-700/[0.10]"><HomeOrnament kind="suzani" /></span>
      </template>
      <template v-else-if="variant === 'ornament'">
        <span class="absolute inset-0 bg-[linear-gradient(160deg,var(--color-paper)_0%,var(--color-brand-50)_45%,#ebe7fb_100%)]" />
        <span class="absolute -top-32 -left-24 size-[30rem] rounded-full bg-brand-200/45 blur-3xl" />
        <span class="absolute -right-24 bottom-0 size-[28rem] rounded-full bg-accent-100/70 blur-3xl" />
        <span class="absolute top-1/3 left-1/2 size-[22rem] -translate-x-1/2 rounded-full bg-white/70 blur-3xl" />
        <span class="absolute inset-0 text-brand-600/[0.09] [mask-image:radial-gradient(85%_75%_at_50%_45%,transparent_30%,#000_85%)]"><HomeOrnament /></span>
      </template>
      <template v-else-if="variant === 'glyphs'">
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
        <div class="absolute inset-0 scale-[1.2] -rotate-[4deg] overflow-hidden">
          <div
            v-for="(row, ri) in reels"
            :key="ri"
            class="bg-reel absolute -inset-x-32 flex w-max gap-4"
            :class="{ 'bg-reel-rev': row.rev }"
            :style="{ top: row.top }"
          >
            <template v-for="copy in 2" :key="copy">
              <img
                v-for="(name, ii) in row.imgs"
                :key="`${copy}-${ii}`"
                :src="`/images/bg/${name}.webp`"
                alt=""
                width="256"
                height="160"
                loading="lazy"
                decoding="async"
                class="h-32 w-52 shrink-0 rounded-2xl object-cover sm:h-40 sm:w-64"
              >
            </template>
          </div>
        </div>
        <span class="absolute inset-0 bg-brand-800/20 mix-blend-multiply" />
        <span class="absolute inset-0 bg-[linear-gradient(180deg,rgb(250_248_244/0.9)_0%,rgb(250_248_244/0.7)_14%,rgb(250_248_244/0.18)_32%,rgb(250_248_244/0.12)_80%,rgb(250_248_244/0.55)_100%)]" />
        <!-- O'tish: qiya kesim (keyingi bo'lim rangida) va ustida yugurib o'tuvchi yorug'lik -->
        <span class="absolute inset-x-0 bottom-0 h-16 bg-[color-mix(in_srgb,var(--color-brand-50)_70%,var(--color-paper))] [clip-path:polygon(0_56%,100%_0,100%_100%,0_100%)] lg:h-24" />
        <span class="bg-shine absolute inset-x-0 bottom-0 h-16 [clip-path:polygon(0_52%,100%_0,100%_6%,0_58%)] lg:h-24" />
      </template>
    </div>
    <slot />
  </div>
</template>
