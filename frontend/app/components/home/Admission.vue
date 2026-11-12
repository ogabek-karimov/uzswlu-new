<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()

const steps = ['s1', 's2', 's3', 's4'] as const
</script>

<template>
  <section class="px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
    <div class="mx-auto grid max-w-7xl gap-5 lg:grid-cols-12">
      <!-- Qabul — 4 qadamda -->
      <div class="rounded-[1.75rem] border border-line bg-white p-7 sm:p-9 lg:col-span-8">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">{{ t('admission.eyebrow') }}</p>
            <h2 class="mt-2 font-display text-3xl leading-tight font-semibold tracking-tight text-ink sm:text-4xl">{{ t('admission.title') }}</h2>
          </div>
          <NuxtLink :to="localePath('/qabul-20262027')" class="group inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-900">
            {{ t('admission.cta') }}
            <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-0.5" />
          </NuxtLink>
        </div>

        <ol class="relative mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <!-- Qadamlarni bog'lovchi chiziq -->
          <span class="decor pointer-events-none absolute top-5 right-10 left-10 hidden h-px bg-line lg:block" aria-hidden="true" />
          <li v-for="(step, i) in steps" :key="step" class="relative">
            <span
              class="relative grid size-10 place-items-center rounded-full font-bold ring-4 ring-white"
              :class="i === steps.length - 1 ? 'bg-accent-400 text-ink' : 'bg-brand-700 text-white'"
            >{{ i + 1 }}</span>
            <p class="mt-4 font-semibold text-ink">{{ t(`admission.steps.${step}.title`) }}</p>
            <p class="mt-1 text-sm leading-relaxed text-muted">{{ t(`admission.steps.${step}.text`) }}</p>
          </li>
        </ol>
      </div>

      <!-- Harakat kartasi -->
      <div class="relative flex flex-col justify-between gap-6 overflow-hidden rounded-[1.75rem] bg-accent-400 p-7 text-ink sm:p-9 lg:col-span-4">
        <span class="decor pointer-events-none absolute -right-10 -bottom-12 size-48 rounded-full border-[2.5rem] border-white/25" aria-hidden="true" />
        <div class="relative">
          <p class="text-xs font-bold tracking-[0.16em] uppercase">{{ t('admission.eyebrow') }}</p>
          <p class="mt-2 font-display text-3xl leading-tight font-semibold">{{ t('admission.title') }}</p>
          <p class="mt-3 text-[15px] leading-relaxed text-ink/75">{{ t('admission.text') }}</p>
        </div>
        <div class="relative flex flex-wrap gap-3">
          <NuxtLink
            :to="localePath('/qabul-20262027')"
            class="group inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3 font-semibold text-white transition-colors hover:bg-brand-800"
          >
            {{ t('admission.cta') }}
            <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-0.5" />
          </NuxtLink>
          <NuxtLink
            :to="localePath('/tolov-kontrakt-miqdori')"
            class="inline-flex items-center rounded-full border border-ink/30 px-6 py-3 font-semibold text-ink transition-colors hover:bg-white/40"
          >
            {{ t('admission.ctaSecondary') }}
          </NuxtLink>
        </div>
      </div>
    </div>
  </section>
</template>
