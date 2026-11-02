<script setup lang="ts">
import type { TaughtLanguage } from '#shared/types/api'

defineProps<{ languages: TaughtLanguage[] }>()

const { t } = useI18n()
</script>

<template>
  <section class="overflow-hidden bg-accent-100/70 py-20 lg:py-24">
    <div class="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
      <p class="text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">{{ t('languages.eyebrow') }}</p>
      <h2 class="mt-3 font-display text-4xl font-semibold tracking-tight text-ink sm:text-5xl">{{ t('languages.title') }}</h2>
      <p class="mt-3 text-lg text-muted">{{ t('languages.text') }}</p>
      <ul class="sr-only">
        <li v-for="lang in languages" :key="lang.code" :lang="lang.code">{{ lang.native }}</li>
      </ul>
    </div>

    <div class="mt-12 space-y-4" aria-hidden="true">
      <div class="flex w-max animate-marquee gap-10 pr-10">
        <template v-for="copy in 2" :key="copy">
          <span v-for="lang in languages" :key="`${copy}-${lang.code}`" class="flex items-center gap-10 font-display text-5xl font-semibold whitespace-nowrap text-ink sm:text-7xl">
            {{ lang.native }}
            <span class="text-3xl text-accent-500">✦</span>
          </span>
        </template>
      </div>
      <div class="flex w-max animate-marquee gap-10 pr-10 [animation-direction:reverse] [animation-duration:55s]">
        <template v-for="copy in 2" :key="copy">
          <span
            v-for="lang in [...languages].reverse()"
            :key="`${copy}-${lang.code}`"
            class="flex items-center gap-10 font-display text-5xl font-semibold whitespace-nowrap text-transparent italic [-webkit-text-stroke:1.5px_var(--color-brand-700)] sm:text-7xl"
          >
            {{ lang.native }}
            <span class="text-3xl text-brand-300 not-italic [-webkit-text-stroke:0]">✦</span>
          </span>
        </template>
      </div>
    </div>
  </section>
</template>
