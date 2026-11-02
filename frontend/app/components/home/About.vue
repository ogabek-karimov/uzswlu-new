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
      class="decor pointer-events-none absolute -bottom-16 -left-6 font-display text-[16rem] leading-none font-semibold text-white/[0.03] select-none lg:text-[22rem]"
      aria-hidden="true"
    >1949</span>

    <div class="relative mx-auto grid max-w-7xl gap-14 px-4 py-20 sm:px-6 lg:grid-cols-12 lg:gap-10 lg:px-8 lg:py-28">
      <div class="lg:col-span-5">
        <SectionHeading :eyebrow="t('about.eyebrow')" :title="t('about.title')" dark />
        <p class="mt-6 text-lg leading-relaxed text-white/65">{{ t('about.text') }}</p>
        <NuxtLink :to="localePath('/universitet-tarixi')" class="group mt-8 inline-flex items-center gap-2 font-semibold text-accent-400">
          {{ t('about.link') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
        </NuxtLink>
      </div>

      <div class="lg:col-span-7 lg:pl-8">
        <dl class="grid grid-cols-2 gap-px overflow-hidden rounded-3xl border border-white/10 bg-white/10">
          <div v-for="stat in stats" :key="stat.key" class="flex flex-col-reverse gap-2 bg-brand-950 p-6 sm:p-10">
            <dt class="text-sm text-white/60 sm:text-base">{{ t(`stats.${stat.key}`) }}</dt>
            <dd class="font-display text-5xl leading-none font-semibold sm:text-7xl">
              {{ formatStat(stat.value).number }}<span class="text-accent-400">{{ formatStat(stat.value).suffix }}</span>
            </dd>
          </div>
        </dl>
        <p class="mt-4 flex items-center gap-2 text-xs text-white/50">
          <span class="relative flex size-2">
            <span class="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span class="relative inline-flex size-2 rounded-full bg-emerald-400" />
          </span>
          {{ t('stats.source') }}
          <template v-if="updatedAt">· {{ formatDate(updatedAt, 'datetime') }}</template>
        </p>
      </div>
    </div>
  </section>
</template>
