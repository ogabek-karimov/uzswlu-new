<script setup lang="ts">
const { t } = useI18n()
const { data: site } = await useSiteData()

// Admin paneldagi "Ramzlar" bo'limidan; CMS ulanmagan bo'lsa — standart havolalar
const symbols = computed(() => stateSymbols.map((base) => {
  const cms = site.value?.symbols?.find(s => s.key === base.key)
  return {
    key: base.key,
    title: cms?.title || t(`symbols.${base.key}`),
    image: cms ? cms.image ?? null : base.image,
    href: cms?.href || cms?.audio || base.href,
    source: cms ? cms.source ?? '' : base.source,
  }
}))

// 12 yulduz (bayroqdagidek 3 + 4 + 5): har biri biroz boshqa vaqtda miltillaydi
function star(cx: number, cy: number, outer = 9, inner = 3.7): string {
  return Array.from({ length: 10 }, (_, i) => {
    const r = i % 2 === 0 ? outer : inner
    const angle = (Math.PI / 5) * i - Math.PI / 2
    return `${(cx + r * Math.cos(angle)).toFixed(2)},${(cy + r * Math.sin(angle)).toFixed(2)}`
  }).join(' ')
}
const stars = [
  ...[190, 226, 262].map(x => [x, 28]),
  ...[172, 208, 244, 280].map(x => [x, 64]),
  ...[154, 190, 226, 262, 298].map(x => [x, 100]),
].map(([x, y], i) => ({ points: star(x!, y!), delay: `${((i * 0.37) % 2.4).toFixed(2)}s` }))

// Pastga-tepaga ko'tarilib yo'qoladigan oltin «chang» zarralari (qat'iy qiymatlar — server va brauzerda bir xil chiqsin)
const dust = Array.from({ length: 16 }, (_, i) => ({
  left: `${(i * 37 + 7) % 97}%`,
  size: `${3 + (i * 5) % 5}px`,
  delay: `${((i * 1.7) % 9).toFixed(1)}s`,
  duration: `${9 + (i * 3) % 7}s`,
}))
</script>

<template>
  <section class="symbols relative isolate overflow-hidden" aria-labelledby="symbols-title">
    <!-- Fon: bayroq (ko'k / oq / yashil, qizil chiziqlar), ipak yaltirashi, to'lqinlar, gerb va yarim oy bilan yulduzlar -->
    <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <div class="symbols-flag absolute inset-0" />
      <div class="symbols-silk absolute inset-0" />
      <div class="symbols-rays" />
      <svg class="absolute inset-x-0 bottom-0 h-44 w-full" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path d="M0 120 C 240 40 480 200 720 120 S 1200 40 1440 130 V200 H0Z" fill="rgb(255 255 255 / 0.08)" />
        <path d="M0 150 C 300 80 520 210 780 140 S 1220 90 1440 160 V200 H0Z" fill="rgb(0 60 20 / 0.18)" />
      </svg>
      <img src="/symbols/emblem.webp" alt="" loading="lazy" class="symbols-emblem absolute top-1/2 left-1/2 h-[118%] max-w-none select-none">
      <span v-for="(d, i) in dust" :key="i" class="symbols-dust" :style="{ left: d.left, width: d.size, height: d.size, animationDelay: d.delay, animationDuration: d.duration }" />
      <!-- Pastki chekkada: naqshli romblar tasmasi -->
      <svg class="absolute inset-x-0 bottom-3 h-3.5 w-full opacity-60" fill="none">
        <defs>
          <pattern id="sym-diamonds" width="30" height="14" patternUnits="userSpaceOnUse">
            <path d="M15 1 L22 7 L15 13 L8 7 Z" stroke="#fff6d6" stroke-width="1.2" />
          </pattern>
        </defs>
        <rect width="100%" height="14" fill="url(#sym-diamonds)" />
      </svg>
      <svg class="absolute top-6 left-[8%] hidden w-[22rem] sm:block lg:left-[14%]" viewBox="0 0 320 130" fill="none">
        <defs>
          <linearGradient id="sym-gold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#fff6d6" />
            <stop offset="1" stop-color="#d9b85a" />
          </linearGradient>
          <mask id="sym-moon">
            <rect width="320" height="130" fill="#fff" />
            <circle cx="98" cy="62" r="44" fill="#000" />
          </mask>
        </defs>
        <circle cx="76" cy="66" r="52" fill="url(#sym-gold)" mask="url(#sym-moon)" />
        <polygon v-for="(star, i) in stars" :key="i" :points="star.points" fill="url(#sym-gold)" class="symbols-star" :style="{ animationDelay: star.delay }" />
      </svg>
    </div>

    <!-- Bayroq ranglaridagi ingichka chiziq -->
    <div class="decor flex h-1.5" aria-hidden="true">
      <span class="flex-1 bg-[#0099B5]" />
      <span class="w-1 bg-[#CE1126]" />
      <span class="flex-1 bg-white" />
      <span class="w-1 bg-[#CE1126]" />
      <span class="flex-1 bg-[#1EB53A]" />
    </div>

    <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
      <p class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-white/90 uppercase">
        <span class="h-px w-8 bg-accent-300" />
        {{ t('symbols.eyebrow') }}
      </p>
      <h2 id="symbols-title" class="mt-4 font-display text-4xl leading-tight font-semibold tracking-tight text-white drop-shadow-[0_2px_18px_rgb(0_35_70/0.5)] sm:text-5xl lg:text-6xl">
        {{ t('symbols.title') }}
      </h2>
      <span class="mt-5 block h-1 w-24 rounded-full bg-gradient-to-r from-[#fff6d6] to-[#d9b85a]" aria-hidden="true" />

      <ul class="mt-24 grid gap-5 pb-8 md:mt-36 md:grid-cols-3 lg:mt-44">
        <!-- o'rtadagi karta yuqoriroq turadi -->
        <li v-for="(symbol, index) in symbols" :key="symbol.key" class="md:even:-translate-y-8">
          <a
            :href="symbol.href"
            target="_blank"
            rel="noopener"
            class="group relative flex h-full items-center gap-5 overflow-hidden rounded-3xl border border-white/70 bg-white/70 p-5 text-ink shadow-[0_34px_60px_-32px_rgb(5_35_70/0.7)] backdrop-blur-xl transition duration-500 hover:bg-white/90 hover:shadow-[0_44px_70px_-28px_rgb(5_35_70/0.85)] hover:[transform:perspective(900px)_rotateX(3deg)_rotateY(-5deg)_translateY(-6px)] sm:p-6 md:flex-col md:items-start xl:flex-row xl:items-center motion-reduce:transition-none motion-reduce:hover:transform-none"
          >
            <!-- Tartib raqami (bezak) va ustidan o'tadigan yaltirash -->
            <span class="pointer-events-none absolute top-2 right-4 font-display text-6xl leading-none font-semibold text-[#b98f2f]/20 select-none" aria-hidden="true">0{{ index + 1 }}</span>
            <span class="pointer-events-none absolute inset-y-0 -left-1/2 w-1/3 -skew-x-12 bg-gradient-to-r from-transparent via-white/70 to-transparent opacity-0 transition-all duration-700 group-hover:left-[130%] group-hover:opacity-100 motion-reduce:hidden" aria-hidden="true" />

            <!-- Oltin ramkali tile + aylanuvchi chiziqli halqa -->
            <span class="relative shrink-0">
              <span class="symbols-ring absolute -inset-2 rounded-[28px] border border-dashed border-[#b98f2f]/60 transition-opacity duration-300 group-hover:opacity-100 md:opacity-60" aria-hidden="true" />
              <span class="relative block rounded-[22px] bg-gradient-to-br from-[#f3e3a8] via-[#b98f2f] to-[#f3e3a8] p-[3px] shadow-[0_10px_24px_-12px_rgb(120_90_20/0.8)] transition-transform duration-500 group-hover:rotate-3 group-hover:scale-105 motion-reduce:transition-none">
                <span class="grid size-24 place-items-center overflow-hidden rounded-[19px] bg-[#fbf6e8] sm:size-28">
                  <img
                    v-if="symbol.image"
                    :src="symbol.image"
                    alt=""
                    loading="lazy"
                    :class="symbol.key === 'flag' ? 'symbols-wave w-[86%] rounded-sm shadow-sm' : 'size-[86%] object-contain'"
                  >
                  <span v-else class="grid size-[62%] place-items-center rounded-full bg-brand-900 text-accent-400 shadow-[0_8px_20px_-8px_var(--color-brand-900)]">
                    <Icon name="lucide:music" class="size-7" />
                  </span>
                </span>
              </span>
            </span>

            <span class="relative min-w-0 flex-1">
              <span class="mb-2 inline-block rounded-full bg-[#b98f2f]/15 px-2.5 py-0.5 text-[11px] font-semibold tracking-[0.14em] text-[#7d5f17] uppercase">{{ t(`symbols.kind.${symbol.key}`) }}</span>
              <span class="block text-[17px] leading-snug font-semibold">{{ symbol.title }}</span>
              <span class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold whitespace-nowrap text-accent-600">
                <Icon :name="symbol.key === 'anthem' ? 'lucide:play' : 'lucide:arrow-up-right'" class="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                {{ symbol.key === 'anthem' ? t('symbols.listen') : t('symbols.view') }}
                <span v-if="symbol.source" class="font-normal opacity-70">· {{ symbol.source }}</span>
                <!-- madhiya: ovoz tebranishi (ustiga olib borilganda harakatlanadi) -->
                <span v-if="symbol.key === 'anthem'" class="symbols-eq ml-1" aria-hidden="true"><i /><i /><i /><i /></span>
              </span>
              <span class="sr-only">({{ t('symbols.newTab') }})</span>
            </span>
          </a>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
/* Bayroq: ko'k — qizil chiziq — oq — qizil chiziq — yashil */
.symbols-flag {
  background: linear-gradient(to bottom, #0a5f86 0%, #0099b5 48%, #ce1126 48%, #ce1126 49.4%, #ffffff 49.4%, #e9f2ef 70%, #ce1126 70%, #ce1126 71.4%, #1eb53a 71.4%, #0c7a2d 100%);
}
/* Ipak mato yaltirashi */
.symbols-silk {
  background:
    radial-gradient(55% 45% at 18% 28%, rgb(255 255 255 / 0.2), transparent 70%),
    radial-gradient(50% 55% at 82% 72%, rgb(255 255 255 / 0.14), transparent 70%),
    radial-gradient(40% 35% at 60% 12%, rgb(255 255 255 / 0.1), transparent 70%);
}
/* Katta gerb: o'rtada, sekin «suzadi» */
.symbols-emblem {
  opacity: 0.4;
  filter: drop-shadow(0 30px 40px rgb(0 20 40 / 0.35));
  transform: translate(-50%, -50%);
  animation: symbols-float 14s ease-in-out infinite;
}
.symbols-star {
  transform-box: fill-box;
  transform-origin: center;
  animation: symbols-twinkle 2.8s ease-in-out infinite;
}
/* Gerb orqasida sekin aylanadigan oltin nurlar */
.symbols-rays {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 110rem;
  height: 110rem;
  margin: -55rem 0 0 -55rem;
  background: repeating-conic-gradient(from 0deg, rgb(255 246 214 / 0.14) 0deg 4deg, transparent 4deg 14deg);
  mask-image: radial-gradient(circle, #000 0, transparent 48%);
  animation: symbols-spin 140s linear infinite;
}
/* Oltin «chang» */
.symbols-dust {
  position: absolute;
  bottom: -8px;
  border-radius: 9999px;
  background: #fff6d6;
  box-shadow: 0 0 10px 2px rgb(255 246 214 / 0.7);
  opacity: 0;
  animation: symbols-rise 12s linear infinite;
}
/* Tile atrofidagi chiziqli halqa sekin aylanadi */
.symbols-ring {
  animation: symbols-spin 24s linear infinite;
}
/* Bayroq tile ichida sekin «hilpiraydi» */
.symbols-wave {
  transform-origin: left center;
  animation: symbols-wave 4.5s ease-in-out infinite;
}
/* Madhiya: ovoz tebranishi */
.symbols-eq {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 14px;
}
.symbols-eq i {
  width: 3px;
  height: 100%;
  border-radius: 2px;
  background: currentColor;
  transform: scaleY(0.3);
  transform-origin: bottom;
  opacity: 0.8;
}
a:hover .symbols-eq i {
  animation: symbols-eq 0.9s ease-in-out infinite;
}
a:hover .symbols-eq i:nth-child(2) { animation-delay: 0.15s; }
a:hover .symbols-eq i:nth-child(3) { animation-delay: 0.3s; }
a:hover .symbols-eq i:nth-child(4) { animation-delay: 0.45s; }
@keyframes symbols-spin {
  to { transform: rotate(360deg); }
}
@keyframes symbols-rise {
  0% { transform: translateY(0); opacity: 0; }
  12% { opacity: 0.9; }
  100% { transform: translateY(-34rem); opacity: 0; }
}
@keyframes symbols-wave {
  0%, 100% { transform: perspective(300px) rotateY(0deg) skewY(0deg); }
  50% { transform: perspective(300px) rotateY(-14deg) skewY(-2deg); }
}
@keyframes symbols-eq {
  0%, 100% { transform: scaleY(0.3); }
  50% { transform: scaleY(1); }
}
@keyframes symbols-float {
  50% { transform: translate(-50%, -52%); }
}
@keyframes symbols-twinkle {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.55; transform: scale(0.85); }
}
@media (prefers-reduced-motion: reduce) {
  .symbols-emblem, .symbols-star, .symbols-rays, .symbols-ring, .symbols-wave, .symbols-eq i { animation: none; }
  .symbols-dust { display: none; }
}
</style>
