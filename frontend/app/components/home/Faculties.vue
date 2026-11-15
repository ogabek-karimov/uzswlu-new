<script setup lang="ts">
import type { Faculty } from '#shared/types/api'

const props = defineProps<{ faculties: Faculty[] }>()

const { t } = useI18n()
const localePath = useLocalePath()

// «Barça fakultetlar» kartasida ko'rsatiladigan dastlabki logolar (qoplanib turadi)
const preview = computed(() => props.faculties.slice(0, 4))
</script>

<template>
  <!-- Fon: kampus surati (biroz xira) + indigo qatlam; kartalar — shisha -->
  <section class="relative isolate overflow-hidden bg-brand-950">
    <img
      src="/images/campus-aerial.webp"
      alt=""
      width="597"
      height="335"
      loading="lazy"
      decoding="async"
      class="decor absolute -inset-6 -z-20 h-[calc(100%+3rem)] w-[calc(100%+3rem)] max-w-none object-cover blur-[5px] saturate-[1.1]"
    >
    <div aria-hidden="true" class="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgb(17_12_46/0.9)_0%,rgb(17_12_46/0.68)_45%,rgb(17_12_46/0.88)_100%)]" />

    <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
      <SectionHeading
        :eyebrow="t('faculties.eyebrow')"
        :title="t('faculties.title')"
        :text="t('faculties.text')"
        dark
      />

      <ul class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <li data-reveal-item v-for="(faculty, i) in faculties" :key="faculty.id">
          <NuxtLink
            :to="localePath(`/faculty/${faculty.slug}`)"
            class="group relative flex h-full min-h-80 flex-col items-center overflow-hidden rounded-3xl border border-white/18 bg-white/9 px-6 pt-8 pb-7 text-center text-white backdrop-blur-md backdrop-saturate-150 transition duration-300 hover:-translate-y-1.5 hover:border-accent-400/60 hover:bg-white/16 hover:shadow-[0_30px_60px_-30px_rgb(0_0_0/0.7)] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
          >
            <!-- Tartib raqami va strelka (burchaklarda) -->
            <span class="absolute top-5 left-6 font-display text-lg font-semibold text-accent-400 tabular-nums">{{ String(i + 1).padStart(2, '0') }}</span>
            <Icon name="lucide:arrow-up-right" class="absolute top-5 right-5 size-5 text-white/60 transition duration-300 group-hover:rotate-45 group-hover:text-accent-400" />
            <!-- Logo orqasidagi nur -->
            <span class="pointer-events-none absolute top-6 left-1/2 size-40 -translate-x-1/2 rounded-full bg-accent-400/0 blur-2xl transition-colors duration-500 group-hover:bg-accent-400/25" aria-hidden="true" />

            <!-- Markazdagi katta logo: hover'da tanga kabi bir marta aylanadi (orqasida universitet logosi) -->
            <span class="relative mt-4 size-32 rounded-full bg-gradient-to-br from-accent-300 via-white/80 to-brand-300 p-[3px] shadow-[0_16px_36px_-14px_rgba(0,0,0,0.7)] perspective-[700px]">
              <span class="relative block size-full transform-3d group-hover:animate-coin-flip group-focus-visible:animate-coin-flip">
                <span class="absolute inset-0 grid place-items-center overflow-hidden rounded-full bg-white backface-hidden">
                  <img v-if="faculty.logo" :src="faculty.logo" alt="" width="124" height="124" loading="lazy" class="size-full object-cover">
                  <Icon v-else name="lucide:building-2" class="size-12 text-brand-700" />
                </span>
                <span class="absolute inset-0 grid rotate-y-180 place-items-center rounded-full bg-white backface-hidden">
                  <img src="/logos/uzswlu.png" alt="" width="96" height="96" loading="lazy" class="size-[78%] object-contain">
                </span>
              </span>
            </span>

            <!-- Nom: katta, ijodiy (display) shrift, markazda -->
            <span class="mt-auto w-full pt-7">
              <span class="mx-auto mb-3 block h-px w-10 bg-accent-400/70 transition-all duration-300 group-hover:w-20" aria-hidden="true" />
              <span class="line-clamp-4 font-display text-[1.45rem] leading-snug font-semibold text-balance">
                {{ faculty.name }}
              </span>
            </span>
          </NuxtLink>
        </li>

        <!-- Barcha fakultetlar: mint gradient karta, logolar qoplanib turadi, katta strelka tugmasi -->
        <li>
          <NuxtLink
            :to="localePath('/fakultetlar-va-kafedralar')"
            class="group relative flex h-full min-h-80 flex-col justify-between overflow-hidden rounded-3xl bg-gradient-to-br from-accent-300 via-accent-400 to-accent-500 p-7 text-brand-950 transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_34px_70px_-30px_var(--color-accent-400)] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
          >
            <!-- Bezak: nuqtali to'r va katta xira bino -->
            <span class="pointer-events-none absolute inset-0 opacity-30 [background-image:radial-gradient(rgb(17_12_46/0.45)_1px,transparent_1.6px)] [background-size:16px_16px] [mask-image:linear-gradient(to_bottom_left,black,transparent_65%)]" aria-hidden="true" />
            <Icon name="lucide:building-2" class="pointer-events-none absolute -right-8 -bottom-10 size-56 -rotate-6 text-brand-950/10 transition-transform duration-500 group-hover:scale-110 group-hover:-rotate-12 motion-reduce:transition-none" aria-hidden="true" />

            <span class="relative flex items-center -space-x-3" aria-hidden="true">
              <span
                v-for="faculty in preview"
                :key="faculty.id"
                class="grid size-12 place-items-center overflow-hidden rounded-full bg-white shadow-[0_8px_18px_-8px_rgba(17,12,46,0.6)] ring-[3px] ring-accent-400 transition-transform duration-300 group-hover:translate-x-1"
              >
                <img v-if="faculty.logo" :src="faculty.logo" alt="" width="48" height="48" loading="lazy" class="size-full object-cover">
                <Icon v-else name="lucide:building-2" class="size-5 text-brand-700" />
              </span>
              <span class="relative z-10 grid size-12 place-items-center rounded-full bg-brand-950 text-sm font-semibold text-accent-400 ring-[3px] ring-accent-400">{{ faculties.length }}+</span>
            </span>

            <span class="relative">
              <span class="block font-display text-[1.9rem] leading-tight font-semibold text-balance">{{ t('faculties.all') }}</span>
              <span class="mt-5 grid size-14 place-items-center rounded-full bg-brand-950 text-accent-400 shadow-[0_14px_28px_-12px_rgba(17,12,46,0.8)] transition duration-300 group-hover:translate-x-2 group-hover:scale-110 motion-reduce:transition-none motion-reduce:group-hover:transform-none">
                <Icon name="lucide:arrow-right" class="size-6" />
              </span>
            </span>
          </NuxtLink>
        </li>
      </ul>
    </div>
  </section>
</template>
