<script setup lang="ts">
import type { Leadership, Stat } from '#shared/types/api'

// «Universitet haqida»: raqamlar tasmasi (fakultet, akademik xodim, kafedra, talaba — HEMIS'dan)
// va uchta karta — universitet haqida, rektor murojaati, video tur
const props = defineProps<{ stats: Stat[] }>()

const { t, locale } = useI18n()
const localePath = useLocalePath()

// Rektor ismi va surati — «Rektorat» sahifasi bilan bitta so'rov (kalit umumiy)
const { data: leadership } = useFetch<Leadership>('/api/leadership', { key: 'leadership', query: { lang: locale }, lazy: true })
const rector = computed(() => leadership.value?.rector ?? null)
const initials = (name: string) => name.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase()

// Tartib: fakultet → akademik xodim → kafedra → talaba. Har birining ikonkasi va rangi (tile) o'zgacha.
const FACTS = [
  { key: 'faculties', icon: 'lucide:building-2', tile: 'bg-accent-400 text-brand-950', glow: 'bg-accent-400/30' },
  { key: 'staff', icon: 'lucide:presentation', tile: 'bg-brand-300 text-brand-950', glow: 'bg-brand-300/30' },
  { key: 'departments', icon: 'lucide:library-big', tile: 'bg-white text-brand-700', glow: 'bg-white/25' },
  { key: 'students', icon: 'lucide:graduation-cap', tile: 'bg-accent-300 text-brand-950', glow: 'bg-accent-300/30' },
] as const

const facts = computed(() => FACTS.flatMap((fact) => {
  const value = props.stats.find(stat => stat.key === fact.key)?.value
  return value === undefined ? [] : [{ ...fact, ...formatStat(value) }]
}))
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :aria-label="t('about.eyebrow')">
    <!-- Raqamlar tasmasi: to'rtta karta, har birida o'zgacha ikonka -->
    <dl v-if="facts.length" class="grid grid-cols-2 gap-3 rounded-[28px] bg-brand-950 p-3 sm:gap-4 sm:p-4 lg:grid-cols-4">
      <div
        v-for="fact in facts"
        :key="fact.key"
        class="group relative overflow-hidden rounded-[20px] bg-white/[0.06] p-5 ring-1 ring-white/10 transition duration-300 hover:-translate-y-1 hover:bg-white/10 hover:ring-white/25 sm:p-6 motion-reduce:transition-none motion-reduce:hover:translate-y-0"
      >
        <!-- yumshoq nur va katta xira ikonka (bezak) -->
        <span class="pointer-events-none absolute -top-10 -right-10 size-32 rounded-full opacity-60 blur-2xl transition-opacity duration-300 group-hover:opacity-100" :class="fact.glow" aria-hidden="true" />
        <Icon :name="fact.icon" class="pointer-events-none absolute -right-3 -bottom-5 size-28 text-white/[0.05] transition-transform duration-500 group-hover:scale-110 group-hover:-rotate-6 motion-reduce:transition-none" aria-hidden="true" />
        <div class="relative flex flex-col gap-5">
          <span class="grid size-12 -rotate-6 place-items-center rounded-2xl shadow-[0_12px_28px_-10px_rgb(0_0_0/0.6)] transition-transform duration-300 group-hover:scale-110 group-hover:rotate-0 motion-reduce:transition-none" :class="fact.tile" aria-hidden="true">
            <Icon :name="fact.icon" class="size-6" />
          </span>
          <div class="flex flex-col-reverse gap-1.5">
            <dt class="text-[15px] text-white/70 lg:min-h-[2lh]">{{ t(`about.facts.${fact.key}`) }}</dt>
            <dd class="font-display text-[2.6rem] leading-none text-white sm:text-5xl">{{ fact.number }}<span class="text-accent-400">{{ fact.suffix }}</span></dd>
          </div>
        </div>
      </div>
    </dl>

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

      <!-- Rektor murojaati -->
      <NuxtLink :to="localePath('/rektorat')" class="group flex flex-col rounded-[28px] bg-brand-100 p-8 transition-colors hover:bg-brand-200/70 lg:col-span-4">
        <span class="flex items-center gap-4">
          <span class="oz-stripes grid size-[70px] shrink-0 place-items-center overflow-hidden rounded-full bg-brand-600 font-display text-xl font-semibold text-white">
            <img v-if="rector?.photo" :src="rector.photo" :alt="rector.name" loading="lazy" width="70" height="70" class="size-full object-cover">
            <template v-else-if="rector">{{ initials(rector.name) }}</template>
          </span>
          <span>
            <span class="block font-semibold text-ink">{{ t('about.rector') }}</span>
            <span v-if="rector" class="block text-muted">{{ rector.name }}</span>
          </span>
        </span>
        <blockquote class="mt-8 font-display text-[1.375rem] leading-relaxed text-ink">“{{ t('about.quote') }}”</blockquote>
      </NuxtLink>

      <!-- Video tur -->
      <NuxtLink :to="localePath('/video-darsliklar')" class="oz-stripes group relative flex min-h-[300px] flex-col justify-between overflow-hidden rounded-[28px] bg-brand-600 p-6 text-white lg:col-span-3">
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
