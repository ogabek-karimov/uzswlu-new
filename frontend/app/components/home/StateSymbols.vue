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

</script>

<template>
  <section aria-labelledby="symbols-title">
    <div class="mx-auto max-w-7xl px-4 pb-6 sm:px-6 lg:px-8">
      <h2 id="symbols-title" class="section-title font-display text-4xl leading-tight font-semibold tracking-tight sm:text-5xl">
        {{ t('symbols.title') }}
      </h2>
    </div>
  <div class="symbols relative isolate overflow-hidden">
    <!-- Fon: hilpirab turgan ipak bayroq surati (qotgan, animatsiyasiz); gerb — bayroq oldida -->
    <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <img src="/symbols/flag-wave.webp" alt="" width="1920" height="1280" loading="lazy" decoding="async" class="absolute inset-0 size-full object-fill">
      <img src="/symbols/emblem.webp" alt="" loading="lazy" class="symbols-emblem absolute top-[34%] left-1/2 h-[72%] max-w-none select-none">
    </div>

    <!-- Bayroqning yuqori qirrasi to'lqinli (sahifa fonidagi to'lqin) -->
    <svg class="decor pointer-events-none absolute inset-x-0 top-0 h-10 w-full sm:h-14" viewBox="0 0 1440 60" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 0 H1440 V18 C 1200 52 960 4 720 26 S 240 54 0 16 Z" fill="var(--color-paper)" />
    </svg>

    <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-20">

      <!-- Kartalar bir qatorda, bir xil balandlikda. Ko'tarilish li (qimirlamaydigan) ustiga olib borilganda ishlaydi —
           shunda karta sichqoncha ostidan chiqib ketib, «qaltirab» qolmaydi -->
      <ul class="mt-40 grid gap-5 pb-4 sm:mt-52 md:grid-cols-3 lg:mt-64">
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
  </div>
  </section>
</template>

<style scoped>
/* Katta gerb: o'rtada, sekin «suzadi» */
.symbols-emblem {
  opacity: 1;
  filter: drop-shadow(0 30px 40px rgb(0 20 40 / 0.35));
  transform: translate(-50%, -50%);
}
/* Bayroq tile ichida yengil hilpirash (faqat shu rasm; transform — GPU, atrofga ta'sir qilmaydi) */
.symbols-wave {
  transform: perspective(300px) rotateY(-8deg) skewY(-1deg); /* tile ichidagi bayroq ham qotgan hilpirash holatida */
}
</style>
