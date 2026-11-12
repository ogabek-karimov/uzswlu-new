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
  <section class="relative overflow-hidden bg-paper" aria-labelledby="symbols-title">
    <!-- Bayroq ranglaridagi ingichka chiziq -->
    <div class="decor flex h-1.5" aria-hidden="true">
      <span class="flex-1 bg-[#0099B5]" />
      <span class="w-1 bg-[#CE1126]" />
      <span class="flex-1 bg-white" />
      <span class="w-1 bg-[#CE1126]" />
      <span class="flex-1 bg-[#1EB53A]" />
    </div>

    <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
      <p class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">
        <span class="h-px w-8 bg-accent-500" />
        {{ t('symbols.eyebrow') }}
      </p>
      <h2 id="symbols-title" class="mt-4 font-display text-4xl leading-tight font-semibold tracking-tight text-ink sm:text-5xl">
        {{ t('symbols.title') }}
      </h2>

      <ul class="mt-12 grid gap-5 md:grid-cols-3">
        <li v-for="symbol in symbols" :key="symbol.key">
          <a
            :href="symbol.href"
            target="_blank"
            rel="noopener"
            class="group flex h-full items-center gap-5 rounded-3xl md:flex-col md:items-start xl:flex-row xl:items-center border border-line bg-white p-5 text-ink transition duration-300 hover:-translate-y-1 hover:border-accent-500 hover:shadow-[0_24px_50px_-28px_var(--color-accent-600)] sm:p-6"
          >
            <span class="grid size-24 shrink-0 place-items-center overflow-hidden rounded-2xl bg-paper ring-1 ring-line sm:size-28">
              <img
                v-if="symbol.image"
                :src="symbol.image"
                alt=""
                loading="lazy"
                class="transition-transform duration-500 group-hover:scale-105"
                :class="symbol.key === 'flag' ? 'w-[86%] rounded-sm shadow-sm' : 'size-[86%] object-contain'"
              >
              <span v-else class="grid size-[62%] place-items-center rounded-full bg-brand-900 text-accent-400 shadow-[0_8px_20px_-8px_var(--color-brand-900)] transition-transform duration-500 group-hover:scale-105">
                <Icon name="lucide:music" class="size-7" />
              </span>
            </span>

            <span class="min-w-0 flex-1">
              <span class="block text-[17px] leading-snug font-semibold">{{ symbol.title }}</span>
              <span class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold whitespace-nowrap text-accent-600">
                <Icon :name="symbol.key === 'anthem' ? 'lucide:play' : 'lucide:arrow-up-right'" class="size-4" />
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
