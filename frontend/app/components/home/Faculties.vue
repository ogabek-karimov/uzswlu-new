<script setup lang="ts">
import type { Faculty } from '#shared/types/api'

defineProps<{ faculties: Faculty[] }>()

const { t } = useI18n()
const localePath = useLocalePath()

</script>

<template>
  <!-- Fon: kampus surati (sekin yaqinlashadi, Ken Burns) + indigo qatlam; tepa va pastda to'lqin; kartalar — shisha -->
  <section class="relative isolate overflow-hidden bg-brand-950">
    <img
      src="/images/campus-aerial.webp"
      alt=""
      width="597"
      height="335"
      loading="lazy"
      decoding="async"
      class="decor bg-kb absolute -inset-6 -z-20 h-[calc(100%+3rem)] w-[calc(100%+3rem)] max-w-none object-cover saturate-[1.1]"
    >
    <div aria-hidden="true" class="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgb(17_12_46/0.8)_0%,rgb(17_12_46/0.45)_45%,rgb(17_12_46/0.8)_100%)]" />

    <HomeWave flip class="text-paper" />
    <HomeWave class="text-paper" />

    <div class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <SectionHeading
        :eyebrow="t('faculties.eyebrow')"
        :title="t('faculties.title')"
        :text="t('faculties.text')"
        dark
      />

      <!-- Ixcham kartalar: kichik logo, nomi to'liq ko'rinadi; «Barcha fakultetlar» ham shu shaklda -->
      <ul class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <li v-for="(faculty, i) in faculties" :key="faculty.id" data-reveal-item class="group/li">
          <NuxtLink :to="localePath(`/faculty/${faculty.slug}`)" data-spot class="group relative flex h-full min-h-[13.5rem] flex-col items-center overflow-hidden rounded-3xl border border-white/18 bg-white/9 px-5 pt-7 pb-6 text-center text-white transition duration-300 group-hover/li:-translate-y-1 hover:border-accent-400/60 hover:bg-white/16 hover:shadow-[0_24px_48px_-28px_rgb(0_0_0/0.7)] motion-reduce:transition-none motion-reduce:group-hover/li:translate-y-0">
            <span class="absolute top-4 left-5 font-display text-base font-semibold text-accent-400 tabular-nums">{{ String(i + 1).padStart(2, '0') }}</span>
            <Icon name="lucide:arrow-up-right" class="absolute top-4 right-4 text-[1.1rem] text-white/60 transition duration-300 group-hover:rotate-45 group-hover:text-accent-400" />

            <!-- Logo: hover'da tanga kabi bir marta aylanadi (orqasida universitet logosi) -->
            <span class="relative size-20 shrink-0 rounded-full bg-gradient-to-br from-accent-300 via-white/80 to-brand-300 p-[3px] shadow-[0_12px_28px_-12px_rgba(0,0,0,0.7)] perspective-[600px]">
              <span class="relative block size-full transform-3d group-hover:animate-coin-flip group-focus-visible:animate-coin-flip">
                <span class="absolute inset-0 grid place-items-center overflow-hidden rounded-full bg-white backface-hidden">
                  <img v-if="faculty.logo" :src="faculty.logo" alt="" width="76" height="76" loading="lazy" class="size-full object-cover">
                  <Icon v-else name="lucide:building-2" class="text-[2rem] text-brand-700" />
                </span>
                <span class="absolute inset-0 grid rotate-y-180 place-items-center rounded-full bg-white backface-hidden">
                  <img src="/logos/uzswlu.png" alt="" width="60" height="60" loading="lazy" class="size-[78%] object-contain">
                </span>
              </span>
            </span>

            <span class="mx-auto mt-5 mb-3 block h-px w-8 bg-accent-400/70 transition-all duration-300 group-hover:w-16" aria-hidden="true" />
            <span class="text-[1.05rem] leading-snug font-semibold text-balance">{{ faculty.name }}</span>
          </NuxtLink>
        </li>

        <li data-reveal-item class="group/li">
          <NuxtLink :to="localePath('/fakultetlar-va-kafedralar')" data-spot class="group relative flex h-full min-h-[13.5rem] flex-col items-center overflow-hidden rounded-3xl border border-white/18 bg-white/9 px-5 pt-7 pb-6 text-center text-white transition duration-300 group-hover/li:-translate-y-1 hover:border-accent-400/60 hover:bg-white/16 hover:shadow-[0_24px_48px_-28px_rgb(0_0_0/0.7)] motion-reduce:transition-none motion-reduce:group-hover/li:translate-y-0">
            <Icon name="lucide:arrow-up-right" class="absolute top-4 right-4 text-[1.1rem] text-white/60 transition duration-300 group-hover:rotate-45 group-hover:text-accent-400" />
            <span class="grid size-20 shrink-0 place-items-center rounded-full bg-accent-400 font-display text-2xl font-semibold text-brand-950 shadow-[0_12px_28px_-12px_rgba(0,0,0,0.7)] transition-transform duration-300 group-hover:scale-105">
              {{ faculties.length }}+
            </span>
            <span class="mx-auto mt-5 mb-3 block h-px w-8 bg-accent-400/70 transition-all duration-300 group-hover:w-16" aria-hidden="true" />
            <span class="text-[1.05rem] leading-snug font-semibold text-balance text-accent-300">{{ t('faculties.all') }}</span>
          </NuxtLink>
        </li>
      </ul>
    </div>
  </section>
</template>
