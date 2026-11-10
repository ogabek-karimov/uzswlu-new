<script setup lang="ts">
import type { Faculty } from '#shared/types/api'

defineProps<{ faculties: Faculty[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
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

    <div class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <SectionHeading
        :eyebrow="t('faculties.eyebrow')"
        :title="t('faculties.title')"
        :text="t('faculties.text')"
        dark
      />

      <ul class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <li v-for="(faculty, i) in faculties" :key="faculty.id">
          <NuxtLink
            :to="localePath(`/faculty/${faculty.slug}`)"
            class="group flex h-full min-h-56 flex-col rounded-2xl border border-white/18 bg-white/9 p-6 text-white backdrop-blur-md backdrop-saturate-150 transition duration-300 hover:-translate-y-1 hover:border-accent-400/60 hover:bg-white/16"
          >
            <span class="flex items-start justify-between">
              <!-- Hover'da logo tanga kabi bir marta aylanadi: orqa tomonida universitet logosi -->
              <span class="size-20 rounded-full shadow-[0_10px_26px_-10px_rgba(0,0,0,0.6)] perspective-[600px]">
                <span class="relative block size-full transform-3d group-hover:animate-coin-flip group-focus-visible:animate-coin-flip">
                  <span class="absolute inset-0 grid place-items-center overflow-hidden rounded-full bg-white backface-hidden">
                    <img v-if="faculty.logo" :src="faculty.logo" alt="" width="80" height="80" loading="lazy" class="size-full object-cover">
                    <Icon v-else name="lucide:building-2" class="size-8 text-brand-700" />
                  </span>
                  <span class="absolute inset-0 grid rotate-y-180 place-items-center rounded-full bg-white backface-hidden">
                    <img src="/logos/uzswlu.png" alt="" width="62" height="62" loading="lazy" class="size-[78%] object-contain">
                  </span>
                </span>
              </span>
              <Icon name="lucide:arrow-up-right" class="size-5 text-white/70 transition duration-300 group-hover:rotate-45 group-hover:text-accent-400" />
            </span>

            <span class="mt-auto pt-8">
              <span class="block text-xs font-semibold text-accent-400 tabular-nums">
                {{ String(i + 1).padStart(2, '0') }}
              </span>
              <span class="mt-1 block text-lg leading-snug font-semibold">
                {{ faculty.name }}
              </span>
            </span>
          </NuxtLink>
        </li>
        <li>
          <NuxtLink
            :to="localePath('/fakultetlar-va-kafedralar')"
            class="group flex h-full min-h-56 flex-col justify-between rounded-2xl bg-accent-400 p-6 text-ink transition-colors hover:bg-accent-300"
          >
            <Icon name="lucide:building-2" class="size-7" />
            <span class="flex items-center justify-between gap-3 text-lg font-semibold">
              {{ t('faculties.all') }}
              <Icon name="lucide:arrow-right" class="size-5 transition-transform group-hover:translate-x-1" />
            </span>
          </NuxtLink>
        </li>
      </ul>
    </div>
  </section>
</template>
