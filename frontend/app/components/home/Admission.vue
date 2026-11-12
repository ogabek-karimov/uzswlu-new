<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()

const steps = ['s1', 's2', 's3', 's4'] as const
</script>

<template>
  <section class="px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
    <div class="relative mx-auto max-w-7xl overflow-hidden rounded-[2rem] bg-brand-900 px-6 py-12 text-white sm:px-12 lg:px-14 lg:py-14">
      <div class="decor pointer-events-none absolute inset-0" aria-hidden="true">
        <span class="absolute -top-32 -right-32 size-[30rem] rounded-full border-[3rem] border-white/[0.04]" />
        <span class="absolute -bottom-40 left-1/3 size-80 rounded-full bg-brand-600/30 blur-3xl" />
      </div>

      <div class="relative grid gap-12 lg:grid-cols-12 lg:gap-10">
        <div class="lg:col-span-5">
          <SectionHeading :eyebrow="t('admission.eyebrow')" :title="t('admission.title')" :text="t('admission.text')" dark />
          <div class="mt-8 flex flex-wrap gap-3">
            <NuxtLink
              :to="localePath('/qabul-20262027')"
              class="group inline-flex items-center gap-2 rounded-full bg-accent-400 px-6 py-3.5 font-semibold text-ink transition-colors hover:bg-accent-300"
            >
              {{ t('admission.cta') }}
              <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-0.5" />
            </NuxtLink>
            <NuxtLink
              :to="localePath('/tolov-kontrakt-miqdori')"
              class="inline-flex items-center gap-2 rounded-full border border-white/20 px-6 py-3.5 font-semibold text-white transition-colors hover:bg-white/10"
            >
              {{ t('admission.ctaSecondary') }}
            </NuxtLink>
          </div>
        </div>

        <ol class="grid gap-4 sm:grid-cols-2 lg:col-span-7">
          <li
            v-for="(step, i) in steps"
            :key="step"
            class="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-sm transition-colors hover:bg-white/[0.08]"
          >
            <span class="font-display text-4xl font-semibold text-accent-400">{{ String(i + 1).padStart(2, '0') }}</span>
            <p class="mt-4 text-lg font-semibold">{{ t(`admission.steps.${step}.title`) }}</p>
            <p class="mt-1.5 text-sm leading-relaxed text-white/60">{{ t(`admission.steps.${step}.text`) }}</p>
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>
