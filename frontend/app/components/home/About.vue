<script setup lang="ts">
import type { HomeVideoTour, Stat } from '#shared/types/api'

// «Universitet haqida»: raqamlar tasmasi (fakultet, akademik xodim, kafedra, talaba — HEMIS'dan)
// va ikkita karta — universitet haqida va video tur
const props = defineProps<{ stats: Stat[]; videoTour?: HomeVideoTour | null }>()

const { t } = useI18n()
const localePath = useLocalePath()
const playing = ref(false)

// Tartib: fakultet → akademik xodim → kafedra → talaba. Ikonkalar ma'nosi original saytdagidek (qalam, kurs, sertifikat, bitiruvchi).
const FACTS = [
  { key: 'faculties', icon: 'lucide:pencil-ruler', tile: 'bg-accent-400 text-brand-950', glow: 'bg-accent-400/25' },
  { key: 'staff', icon: 'lucide:book-open', tile: 'bg-brand-300 text-brand-950', glow: 'bg-brand-300/25' },
  { key: 'departments', icon: 'lucide:award', tile: 'bg-white text-brand-700', glow: 'bg-white/20' },
  { key: 'students', icon: 'lucide:graduation-cap', tile: 'bg-accent-300 text-brand-950', glow: 'bg-accent-300/25' },
] as const

const facts = computed(() => FACTS.flatMap((fact) => {
  const value = props.stats.find(stat => stat.key === fact.key)?.value
  return value === undefined ? [] : [{ ...fact, ...formatStat(value) }]
}))
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :aria-label="t('about.eyebrow')">
    <!-- Raqamlar: bitta qator (telefonda 2×2). Katakchalar ingichka chiziq bilan ajratilgan, hoverda yorishadi -->
    <dl v-if="facts.length" class="grid grid-cols-2 gap-px overflow-hidden rounded-[28px] bg-white/12 lg:grid-cols-4">
      <div
        v-for="fact in facts"
        :key="fact.key"
        class="group relative flex items-center gap-4 overflow-hidden bg-brand-950 px-5 py-6 transition-colors duration-300 hover:bg-brand-900 sm:gap-5 sm:px-7 sm:py-8"
      >
        <span class="pointer-events-none absolute -top-10 -left-10 size-32 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100" :class="fact.glow" aria-hidden="true" />
        <span class="relative grid size-12 shrink-0 -rotate-6 place-items-center rounded-2xl shadow-[0_12px_28px_-12px_rgb(0_0_0/0.6)] transition-transform duration-300 group-hover:rotate-0 group-hover:scale-110 sm:size-14 motion-reduce:transition-none" :class="fact.tile" aria-hidden="true">
          <Icon :name="fact.icon" class="size-6 sm:size-7" />
        </span>
        <div class="relative flex min-w-0 flex-col-reverse">
          <dt class="text-sm leading-snug text-white/70 sm:text-[15px]">{{ t(`about.facts.${fact.key}`) }}</dt>
          <dd class="font-display text-4xl leading-none text-white sm:text-5xl"><CountUp :value="fact.number" /><span class="text-accent-400">{{ fact.suffix }}</span></dd>
        </div>
      </div>
    </dl>

    <div class="mt-8 grid gap-6 lg:auto-rows-[minmax(25rem,auto)] lg:grid-cols-12">
      <!-- Universitet haqida -->
      <article class="group/about relative flex flex-col overflow-hidden rounded-[28px] border border-line bg-white p-8 transition duration-300 hover:border-brand-300 hover:shadow-[0_30px_60px_-34px_var(--color-brand-700)] sm:p-9 lg:col-span-5 motion-reduce:transition-none motion-reduce:hover:translate-y-0">
        <span class="pointer-events-none absolute -top-16 -right-16 size-48 rounded-full bg-brand-100 opacity-0 blur-2xl transition-opacity duration-500 group-hover/about:opacity-100" aria-hidden="true" />
        <h2 class="font-display text-4xl leading-[1.1] font-semibold text-ink sm:text-[2.6rem]">{{ t('about.title') }}</h2>
        <p class="mt-4 text-[17px] leading-relaxed text-muted">{{ t('about.text') }}</p>
        <NuxtLink :to="localePath('/universitet-haqida')" class="group mt-6 inline-flex items-center gap-1.5 self-start font-semibold text-brand-600 hover:text-brand-800">
          {{ t('about.link') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
        </NuxtLink>
      </article>

      <!-- Video tur: admin panelda («Universitet haqida» bo'limi) havola kiritilsa — shu yerning o'zida ochiladi, aks holda video sahifasiga olib boradi -->
      <template v-if="videoTour">
        <button
          type="button"
          class="oz-stripes group relative flex min-h-[300px] flex-col justify-between overflow-hidden rounded-[28px] bg-brand-600 p-6 text-left text-white transition duration-300 hover:shadow-[0_30px_60px_-30px_var(--color-brand-700)] lg:col-span-7 motion-reduce:transition-none"
          :aria-label="`${t('about.videoLabel')}: ${videoTour.title || t('about.videoTitle')}`"
          @click="playing = true"
        >
          <img v-if="videoTour.poster" :src="videoTour.poster" alt="" class="absolute inset-0 size-full object-cover transition-transform duration-700 group-hover:scale-105 motion-reduce:transition-none" loading="lazy">
          <span class="absolute inset-0 bg-gradient-to-t from-brand-950/85 via-brand-950/25 to-brand-950/30" aria-hidden="true" />
          <span class="relative text-sm text-white/85">{{ t('about.videoLabel') }}</span>
          <span class="relative grid size-[70px] place-self-center place-items-center rounded-full bg-white text-brand-600 shadow-[0_18px_40px_-16px_rgba(17,12,46,0.7)] transition-transform group-hover:scale-110 motion-reduce:transition-none" aria-hidden="true">
            <Icon name="lucide:play" class="ml-0.5 size-6 fill-current" />
          </span>
          <span class="relative">
            <span class="block text-[17px] leading-snug font-semibold">{{ videoTour.title || t('about.videoTitle') }}</span>
            <span v-if="videoTour.text" class="mt-1 line-clamp-2 block text-sm text-white/80">{{ videoTour.text }}</span>
          </span>
        </button>
        <AppDialog v-model:open="playing" class="max-w-4xl" :title="videoTour.title || t('about.videoTitle')" body-class="p-0">
          <div v-if="playing" class="aspect-video w-full bg-black">
            <video v-if="videoTour.kind === 'file'" :src="videoTour.url" :poster="videoTour.poster || undefined" class="size-full" controls autoplay playsinline />
            <iframe v-else :src="videoTour.url" :title="videoTour.title || t('about.videoTitle')" class="size-full" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" />
          </div>
        </AppDialog>
      </template>
      <!-- Video tur hali kiritilmagan: «Video darsliklar» ga olib bormaydi — admin panelda havola kiritilgach ochiladi -->
      <div v-else class="oz-stripes relative flex min-h-[300px] flex-col justify-between overflow-hidden rounded-[28px] bg-brand-600 p-6 text-white lg:col-span-7">
        <span class="text-sm text-white/80">{{ t('about.videoLabel') }}</span>
        <span class="grid size-[70px] place-self-center place-items-center rounded-full bg-white/25 text-white" aria-hidden="true">
          <Icon name="lucide:play" class="ml-0.5 size-6 fill-current" />
        </span>
        <span>
          <span class="block text-[17px] leading-snug font-semibold">{{ t('about.videoTitle') }}</span>
          <span class="mt-1 block text-sm text-white/75">{{ t('about.videoSoon') }}</span>
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Rasmdagi kabi diagonal chiziqlar (surat yoki video muqovasi o'rniga) */
.oz-stripes {
  background-image: repeating-linear-gradient(135deg, rgb(255 255 255 / 0.07) 0 22px, transparent 22px 44px);
}
</style>
