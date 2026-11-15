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
</script>

<template>
  <section class="symbols relative isolate overflow-hidden" aria-labelledby="symbols-title">
    <!-- Fon: bayroq (ko'k / oq / yashil, qizil chiziqlar), ipak yaltirashi, to'lqinlar, gerb va yarim oy bilan yulduzlar -->
    <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <div class="symbols-flag absolute inset-0" />
      <div class="symbols-silk absolute inset-0" />
      <div class="symbols-sheen" />
      <svg class="absolute inset-x-0 bottom-0 h-44 w-full" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path d="M0 120 C 240 40 480 200 720 120 S 1200 40 1440 130 V200 H0Z" fill="rgb(255 255 255 / 0.08)" />
        <path d="M0 150 C 300 80 520 210 780 140 S 1220 90 1440 160 V200 H0Z" fill="rgb(0 60 20 / 0.18)" />
      </svg>
      <img src="/symbols/emblem.webp" alt="" loading="lazy" class="symbols-emblem absolute top-1/2 left-1/2 h-[118%] max-w-none select-none">
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

      <!-- Kartalar bir qatorda, bir xil balandlikda. Ko'tarilish li (qimirlamaydigan) ustiga olib borilganda ishlaydi —
           shunda karta sichqoncha ostidan chiqib ketib, «qaltirab» qolmaydi -->
      <ul class="mt-24 grid gap-5 pb-4 md:mt-36 md:grid-cols-3 lg:mt-44">
        <li v-for="symbol in symbols" :key="symbol.key" class="group/sym">
          <a
            :href="symbol.href"
            target="_blank"
            rel="noopener"
            class="group flex h-full items-center gap-5 rounded-3xl border border-white/70 bg-white/70 p-5 text-ink shadow-[0_34px_60px_-32px_rgb(5_35_70/0.7)] backdrop-blur-xl transition duration-300 group-hover/sym:-translate-y-1.5 group-hover/sym:bg-white/90 group-hover/sym:shadow-[0_40px_70px_-30px_rgb(5_35_70/0.8)] sm:p-6 md:flex-col md:items-start xl:flex-row xl:items-center motion-reduce:transition-none motion-reduce:group-hover/sym:translate-y-0"
          >
            <!-- Oltin ramkali tile -->
            <span class="shrink-0 rounded-[22px] bg-gradient-to-br from-[#f3e3a8] via-[#b98f2f] to-[#f3e3a8] p-[3px] shadow-[0_10px_24px_-12px_rgb(120_90_20/0.8)] transition-transform duration-500 group-hover/sym:scale-105 motion-reduce:transition-none">
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

            <span class="min-w-0 flex-1">
              <span class="block text-[17px] leading-snug font-semibold">{{ symbol.title }}</span>
              <span class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold whitespace-nowrap text-accent-600">
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
}
.symbols-star {
  transform-box: fill-box;
  transform-origin: center;
}
/* Bayroqning ko'k qismida (kartalardan yuqorida) sekin o'tadigan yorug' chiziq — mato hilpiraganday.
   Kartalar ostiga tushmaydi: orqadagi harakat shisha (blur) kartalarni qayta chizdirib qaltiratadi. */
.symbols-sheen {
  position: absolute;
  inset: 0 0 auto 0;
  height: 30%;
  background: linear-gradient(100deg, transparent 0 32%, rgb(255 255 255 / 0.16) 48%, transparent 64% 100%);
  background-size: 260% 100%;
  mask-image: linear-gradient(to bottom, #000, transparent);
  animation: symbols-sheen 10s ease-in-out infinite alternate;
}
/* Bayroq tile ichida yengil hilpirash (faqat shu rasm; transform — GPU, atrofga ta'sir qilmaydi) */
.symbols-wave {
  transform-origin: left center;
  will-change: transform;
  animation: symbols-wave 5s ease-in-out infinite;
}
@keyframes symbols-sheen {
  from { background-position: 0% 0; }
  to { background-position: 100% 0; }
}
@keyframes symbols-wave {
  0%, 100% { transform: perspective(300px) rotateY(0deg) skewY(0deg); }
  50% { transform: perspective(300px) rotateY(-12deg) skewY(-1.5deg); }
}
@media (prefers-reduced-motion: reduce) {
  .symbols-sheen, .symbols-wave { animation: none; }
}
</style>
