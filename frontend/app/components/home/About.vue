<script setup lang="ts">
import type { Stat } from '#shared/types/api'

defineProps<{ stats: Stat[]; updatedAt?: string }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()
</script>

<template>
  <section class="relative overflow-hidden bg-brand-950 text-white">
    <span
      class="decor pointer-events-none absolute -bottom-12 -left-6 font-display text-[12rem] leading-none font-semibold text-white/[0.03] select-none lg:text-[16rem]"
      aria-hidden="true"
    >1949</span>

    <div class="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-14">
      <div class="grid gap-6 lg:grid-cols-12 lg:items-end lg:gap-10">
        <div class="lg:col-span-6">
          <SectionHeading :eyebrow="t('about.eyebrow')" :title="t('about.title')" dark />
        </div>
        <div class="lg:col-span-6">
          <p class="text-base leading-relaxed text-white/65 sm:text-lg">{{ t('about.text') }}</p>
          <NuxtLink :to="localePath('/universitet-tarixi')" class="group mt-4 inline-flex items-center gap-2 font-semibold text-accent-400">
            {{ t('about.link') }}
            <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
          </NuxtLink>
        </div>
      </div>

      <!-- Ixcham statistika tasmasi -->
      <dl class="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 lg:grid-cols-4">
        <div v-for="stat in stats" :key="stat.key" class="flex flex-col-reverse gap-1.5 bg-brand-950 px-5 py-5 lg:px-7 lg:py-6">
          <dt class="text-sm text-white/60">{{ t(`stats.${stat.key}`) }}</dt>
          <dd class="font-display text-4xl leading-none font-semibold lg:text-5xl">
            {{ formatStat(stat.value).number }}<span class="text-accent-400">{{ formatStat(stat.value).suffix }}</span>
          </dd>
        </div>
      </dl>
      <p class="mt-3 flex items-center gap-2 text-xs text-white/50">
        <span class="relative flex size-2">
          <span class="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-60" />
          <span class="relative inline-flex size-2 rounded-full bg-emerald-400" />
        </span>
        {{ t('stats.source') }}
        <template v-if="updatedAt">· {{ formatDate(updatedAt, 'datetime') }}</template>
      </p>
    </div>
  </section>
</template>
