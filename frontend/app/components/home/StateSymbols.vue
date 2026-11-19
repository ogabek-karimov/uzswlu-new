<script setup lang="ts">
const { t } = useI18n()
const { data: site } = await useSiteData()
// Orqa fon (bayroq va gerb) — admin panelda yashirilsa faqat kartalar qoladi
const background = computed(() => site.value?.symbolsBackground !== false)

const GLASS = 'border border-white/50 bg-white/10 text-white [text-shadow:0_1px_10px_rgb(0_40_25/0.55)] shadow-[0_34px_60px_-32px_rgb(5_35_70/0.7)] backdrop-blur-[3px] group-hover/sym:border-accent-400/60 group-hover/sym:bg-white/20 group-hover/sym:shadow-[0_40px_70px_-30px_rgb(5_35_70/0.8)]'
const PLAIN = 'border border-line bg-white text-ink shadow-[0_1px_0_rgba(19,17,47,0.04)] group-hover/sym:border-brand-200 group-hover/sym:shadow-[0_30px_60px_-34px_rgba(19,17,47,0.45)]'

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
  ...[226, 262, 298].map(x => [x, 28]),
  ...[190, 226, 262, 298].map(x => [x, 64]),
  ...[154, 190, 226, 262, 298].map(x => [x, 100]),
].map(([x, y], i) => ({ points: star(x!, y!), delay: `${((i * 0.37) % 2.4).toFixed(2)}s` }))
</script>

<template>
  <section aria-labelledby="symbols-title">
    <div class="mx-auto max-w-7xl px-4 pb-6 sm:px-6 lg:px-8">
      <h2 id="symbols-title" class="section-title font-display text-4xl leading-tight font-semibold tracking-tight sm:text-5xl">
        {{ t('symbols.title') }}
      </h2>
    </div>
  <div class="symbols relative isolate" :class="background && 'section-wave overflow-hidden'">
    <!-- Fon: bayroq (ko'k / oq / yashil, qizil chiziqlar), ipak yaltirashi, to'lqinlar, gerb va yarim oy bilan yulduzlar -->
    <div v-if="background" class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <div class="symbols-flag absolute inset-0" />
      <div class="symbols-silk absolute inset-0" />
      <!-- Mato burmalari: namunadagi ipak bayroqdagidek yorug' va soya chiziqlari (qotgan, animatsiyasiz) -->
      <svg class="symbols-folds absolute inset-0 size-full" viewBox="0 0 1440 800" preserveAspectRatio="none">
        <defs>
          <filter id="sym-fold-blur" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="22" /></filter>
          <filter id="sym-fold-soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="9" /></filter>
        </defs>
        <g filter="url(#sym-fold-blur)" fill="none" stroke-linecap="round">
          <path d="M-40 250 C 260 330 520 420 760 560 S 1180 760 1500 820" stroke="rgb(255 255 255 / 0.55)" stroke-width="70" />
          <path d="M-40 330 C 240 420 500 520 740 650 S 1100 820 1400 900" stroke="rgb(0 30 50 / 0.35)" stroke-width="60" />
          <path d="M300 -40 C 520 120 700 260 980 420 S 1300 560 1500 600" stroke="rgb(255 255 255 / 0.4)" stroke-width="80" />
          <path d="M420 -40 C 640 140 820 300 1100 470 S 1380 600 1500 640" stroke="rgb(0 30 50 / 0.3)" stroke-width="55" />
          <path d="M1180 -40 C 1240 120 1300 260 1460 380" stroke="rgb(0 30 50 / 0.32)" stroke-width="70" />
          <path d="M1100 -40 C 1160 140 1230 300 1420 440" stroke="rgb(255 255 255 / 0.45)" stroke-width="50" />
        </g>
        <g filter="url(#sym-fold-soft)" fill="none" stroke-linecap="round">
          <path d="M60 300 C 300 380 560 470 800 600 S 1200 780 1480 840" stroke="rgb(255 255 255 / 0.5)" stroke-width="10" />
          <path d="M520 40 C 720 180 880 300 1140 450" stroke="rgb(255 255 255 / 0.45)" stroke-width="8" />
          <path d="M1240 60 C 1290 180 1340 280 1460 360" stroke="rgb(255 255 255 / 0.5)" stroke-width="8" />
        </g>
      </svg>
      <svg class="absolute inset-x-0 bottom-0 h-44 w-full" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path d="M0 120 C 240 40 480 200 720 120 S 1200 40 1440 130 V200 H0Z" fill="rgb(255 255 255 / 0.08)" />
        <path d="M0 150 C 300 80 520 210 780 140 S 1220 90 1440 160 V200 H0Z" fill="rgb(0 60 20 / 0.18)" />
      </svg>
      <img src="/symbols/emblem.webp" alt="" loading="lazy" class="symbols-emblem absolute top-1/2 left-1/2 h-[92%] max-w-none select-none">
      <svg class="absolute top-[5%] left-[6%] aspect-[320/130] h-[22%] max-w-[86%] lg:left-[14%]" viewBox="0 0 320 130" fill="none">
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


    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :class="background ? 'pt-14 pb-6 lg:pt-20 lg:pb-8' : 'pb-14 lg:pb-20'">

      <!-- Kartalar bir qatorda, bir xil balandlikda. Ko'tarilish li (qimirlamaydigan) ustiga olib borilganda ishlaydi —
           shunda karta sichqoncha ostidan chiqib ketib, «qaltirab» qolmaydi -->
      <ul class="grid gap-5 md:grid-cols-3" :class="background && 'mt-72 sm:mt-80 lg:mt-[26rem]'">
        <li v-for="symbol in symbols" :key="symbol.key" class="group/sym">
          <a
            :href="symbol.href"
            target="_blank"
            rel="noopener"
            :class="background ? GLASS : PLAIN"
            class="group flex h-full items-center gap-5 rounded-3xl p-5 transition duration-300 group-hover/sym:-translate-y-1.5 sm:p-6 md:flex-col md:items-start xl:flex-row xl:items-center motion-reduce:transition-none motion-reduce:group-hover/sym:translate-y-0"
          >
            <!-- Oltin ramkali tile -->
            <span class="shrink-0 rounded-[22px] bg-gradient-to-br from-[#f3e3a8] via-[#b98f2f] to-[#f3e3a8] p-[3px] shadow-[0_10px_24px_-12px_rgb(120_90_20/0.8)] transition-transform duration-500 group-hover/sym:scale-105 motion-reduce:transition-none">
              <span class="grid size-24 place-items-center overflow-hidden rounded-[19px] bg-[#fbf6e8] sm:size-28">
                <!-- Bayroq: chap tomondan mahkam, to'lqin o'ngga qarab yuguradi -->
                <span v-if="symbol.image && symbol.key === 'flag'" class="symbols-wave relative block w-[86%] overflow-hidden rounded-sm shadow-sm">
                  <img :src="symbol.image" alt="" loading="lazy" class="block w-full">
                </span>
                <img v-else-if="symbol.image" :src="symbol.image" alt="" loading="lazy" class="size-[86%] object-contain">
                <span v-else class="grid size-[62%] place-items-center rounded-full bg-brand-900 text-accent-400 shadow-[0_8px_20px_-8px_var(--color-brand-900)]">
                  <Icon name="lucide:music" class="size-7" />
                </span>
              </span>
            </span>

            <span class="min-w-0 flex-1">
              <span class="block text-[17px] leading-snug font-semibold">{{ symbol.title }}</span>
              <span class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold whitespace-nowrap" :class="background ? 'text-accent-300' : 'text-accent-600'">
                <Icon :name="symbol.key === 'anthem' ? 'lucide:play' : 'lucide:arrow-up-right'" class="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                {{ symbol.key === 'anthem' ? t('symbols.listen') : t('symbols.view') }}
                <span v-if="symbol.source" class="font-normal opacity-70">· {{ symbol.source }}</span>
              </span>
              <span class="sr-only">({{ t('symbols.newTab') }})</span>
            </span>
          </a>
        </li>
      </ul>
    </div>
  </div>
  </section>
</template>

<style scoped>
/* Bayroq: ko'k — qizil chiziq — oq — qizil chiziq — yashil */
.symbols-flag {
  /* Rasmiy bayroqdagidek: ko'k, oq, yashil — teng enli (har biri ≈32,5%), oq yo'l ikki tomonidan ingichka qizil hoshiya bilan */
  background: linear-gradient(to bottom, #0a5f86 0%, #0099b5 32.53%, #ce1126 32.53%, #ce1126 33.73%, #ffffff 33.73%, #e9f2ef 66.27%, #ce1126 66.27%, #ce1126 67.47%, #1eb53a 67.47%, #0c7a2d 100%);
}
/* Ipak mato yaltirashi */
.symbols-silk {
  background:
    radial-gradient(55% 45% at 18% 28%, rgb(255 255 255 / 0.2), transparent 70%),
    radial-gradient(50% 55% at 82% 72%, rgb(255 255 255 / 0.14), transparent 70%),
    radial-gradient(40% 35% at 60% 12%, rgb(255 255 255 / 0.1), transparent 70%);
}
/* Katta gerb: o'rtada, sekin «suzadi» */
.symbols-folds { mix-blend-mode: overlay; }
.symbols-emblem {
  opacity: 1;
  filter: drop-shadow(0 30px 40px rgb(0 20 40 / 0.35));
  transform: translate(-50%, -50%);
}
.symbols-star {
  transform-box: fill-box;
  transform-origin: center;
}
/* Bayroq tile ichida yengil hilpirash (faqat shu rasm; transform — GPU, atrofga ta'sir qilmaydi) */
/* Bayroq tile ichida yengil hilpirash (faqat shu rasm; transform — GPU, atrofga ta'sir qilmaydi) */
.symbols-wave {
  transform-origin: left center;
  will-change: transform;
  animation: symbols-wave 3.6s ease-in-out infinite;
}
/* Mato to'lqini: yorug'/soya yo'llari chapdan o'ngga yuguradi (ikki barobar keng qatlam bir davrga suriladi — uzluksiz) */
.symbols-wave::after {
  content: '';
  position: absolute;
  inset: 0 auto 0 -100%;
  width: 200%;
  background: linear-gradient(90deg, rgb(0 0 0 / 0) 0%, rgb(255 255 255 / 0.32) 18%, rgb(0 0 0 / 0) 34%, rgb(0 0 0 / 0.2) 52%, rgb(0 0 0 / 0) 70%, rgb(255 255 255 / 0.22) 86%, rgb(0 0 0 / 0) 100%) 0 0 / 50% 100% repeat-x;
  animation: symbols-ripple 1.8s linear infinite;
  pointer-events: none;
}
@keyframes symbols-wave {
  0%, 100% { transform: perspective(320px) rotateY(0deg) skewY(0deg) scaleX(1); }
  25% { transform: perspective(320px) rotateY(-9deg) skewY(-1.6deg) scaleX(0.98); }
  50% { transform: perspective(320px) rotateY(-3deg) skewY(1deg) scaleX(1); }
  75% { transform: perspective(320px) rotateY(-11deg) skewY(-1deg) scaleX(0.97); }
}
@keyframes symbols-ripple {
  from { transform: translateX(0); }
  to { transform: translateX(50%); }
}
@media (prefers-reduced-motion: reduce) {
  .symbols-wave, .symbols-wave::after { animation: none; }
}
</style>
