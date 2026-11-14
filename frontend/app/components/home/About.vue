<script setup lang="ts">
import type { Stat } from '#shared/types/api'

// «Universitet haqida»: raqamlar tasmasi (fakultet, akademik xodim, kafedra, talaba — HEMIS'dan)
// va ikkita karta — universitet haqida va video tur
const props = defineProps<{ stats: Stat[] }>()

const { t } = useI18n()
const localePath = useLocalePath()

// Tartib: fakultet → akademik xodim → kafedra → talaba. Ikonkalar ma'nosi original saytdagidek (qalam, kurs, sertifikat, bitiruvchi);
// kartalar bir xil emas: shaxmat tartibida rang beriladi, o'ng ustun pastroqda turadi.
const FACTS = [
  { key: 'faculties', icon: 'lucide:pencil-ruler', card: 'bg-white/[0.07] text-white ring-1 ring-white/10', label: 'text-white/70', tile: 'bg-accent-400 text-brand-950', ghost: 'text-white/[0.06]', suffixColor: 'text-accent-400' },
  { key: 'staff', icon: 'lucide:book-open', card: 'bg-accent-400 text-brand-950', label: 'text-brand-950/70', tile: 'bg-brand-950 text-accent-400', ghost: 'text-brand-950/[0.08]', suffixColor: 'text-brand-700' },
  { key: 'departments', icon: 'lucide:award', card: 'bg-brand-600 text-white', label: 'text-white/75', tile: 'bg-white text-brand-700', ghost: 'text-white/[0.09]', suffixColor: 'text-accent-300' },
  { key: 'students', icon: 'lucide:graduation-cap', card: 'bg-white text-brand-950', label: 'text-muted', tile: 'bg-brand-950 text-accent-400', ghost: 'text-brand-600/[0.07]', suffixColor: 'text-brand-600' },
] as const

const facts = computed(() => FACTS.flatMap((fact) => {
  const value = props.stats.find(stat => stat.key === fact.key)?.value
  return value === undefined ? [] : [{ ...fact, ...formatStat(value) }]
}))
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :aria-label="t('about.eyebrow')">
    <!-- Raqamlar: chapda sarlavha, o'ngda 2×2 kartalar (o'ng ustun pastroqda — bir qatordagi «tasma» emas) -->
    <div v-if="facts.length" class="grid gap-8 rounded-[28px] bg-brand-950 p-5 sm:p-8 lg:grid-cols-12 lg:items-center lg:gap-10 lg:p-12">
      <div class="lg:col-span-4">
        <p class="text-[13px] font-semibold tracking-[0.12em] text-accent-400 uppercase">{{ t('about.numbers.eyebrow') }}</p>
        <h2 class="mt-4 font-display text-4xl leading-[1.1] font-semibold text-white sm:text-[2.6rem]">{{ t('about.numbers.title') }}</h2>
        <p class="mt-4 max-w-sm text-[17px] leading-relaxed text-white/70">{{ t('about.numbers.text') }}</p>
      </div>
      <dl class="grid grid-cols-2 gap-3 sm:gap-4 lg:col-span-8 lg:items-start">
        <div
          v-for="fact in facts"
          :key="fact.key"
          class="group relative overflow-hidden rounded-3xl p-5 sm:p-7 lg:even:mt-10"
          :class="fact.card"
        >
          <!-- katta xira ikonka (bezak) -->
          <Icon :name="fact.icon" class="pointer-events-none absolute -right-4 -bottom-6 size-36 transition-transform duration-500 group-hover:scale-110 group-hover:-rotate-6 motion-reduce:transition-none" :class="fact.ghost" aria-hidden="true" />
          <div class="relative flex flex-col gap-6 sm:gap-8">
            <span class="grid size-12 -rotate-6 place-items-center rounded-2xl shadow-[0_12px_28px_-12px_rgb(0_0_0/0.55)] transition-transform duration-300 group-hover:rotate-0 group-hover:scale-110 sm:size-14 motion-reduce:transition-none" :class="fact.tile" aria-hidden="true">
              <Icon :name="fact.icon" class="size-6 sm:size-7" />
            </span>
            <div class="flex flex-col-reverse gap-2">
              <dt class="text-[15px] sm:text-base lg:min-h-[2lh]" :class="fact.label">{{ t(`about.facts.${fact.key}`) }}</dt>
              <dd class="font-display text-5xl leading-none sm:text-6xl lg:text-7xl">{{ fact.number }}<span :class="fact.suffixColor">{{ fact.suffix }}</span></dd>
            </div>
          </div>
        </div>
      </dl>
    </div>

    <div class="mt-8 grid gap-6 lg:auto-rows-[minmax(25rem,auto)] lg:grid-cols-12">
      <!-- Universitet haqida -->
      <article class="flex flex-col rounded-[28px] border border-line bg-white p-8 sm:p-9 lg:col-span-5">
        <p class="text-[13px] font-semibold tracking-[0.12em] text-brand-600 uppercase">{{ t('about.eyebrow') }}</p>
        <h2 class="mt-4 font-display text-4xl leading-[1.1] font-semibold text-ink sm:text-[2.6rem]">{{ t('about.title') }}</h2>
        <p class="mt-4 text-[17px] leading-relaxed text-muted">{{ t('about.text') }}</p>
        <NuxtLink :to="localePath('/universitet-haqida')" class="group mt-6 inline-flex items-center gap-1.5 self-start font-semibold text-brand-600 hover:text-brand-800">
          {{ t('about.link') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
        </NuxtLink>
      </article>

      <!-- Video tur -->
      <NuxtLink :to="localePath('/video-darsliklar')" class="oz-stripes group relative flex min-h-[300px] flex-col justify-between overflow-hidden rounded-[28px] bg-brand-600 p-6 text-white lg:col-span-7">
        <span class="text-sm text-white/80">{{ t('about.videoLabel') }}</span>
        <span class="grid size-[70px] place-self-center place-items-center rounded-full bg-white text-brand-600 shadow-[0_18px_40px_-16px_rgba(17,12,46,0.7)] transition-transform group-hover:scale-110 motion-reduce:transition-none" aria-hidden="true">
          <Icon name="lucide:play" class="ml-0.5 size-6 fill-current" />
        </span>
        <span class="text-[17px] leading-snug font-semibold">{{ t('about.videoTitle') }}</span>
      </NuxtLink>
    </div>
  </section>
</template>

<style scoped>
/* Rasmdagi kabi diagonal chiziqlar (surat yoki video muqovasi o'rniga) */
.oz-stripes {
  background-image: repeating-linear-gradient(135deg, rgb(255 255 255 / 0.07) 0 22px, transparent 22px 44px);
}
</style>
