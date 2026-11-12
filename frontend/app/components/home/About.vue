<script setup lang="ts">
import type { Leadership, Stat } from '#shared/types/api'

// «Universitet haqida»: to'q statistika tasmasi (1949, talaba, professor-o'qituvchi, til, hamkor)
// va uchta karta — universitet haqida, rektor murojaati, video tur
const props = defineProps<{ stats: Stat[]; languages: number; partners: number }>()

const { t, locale } = useI18n()
const localePath = useLocalePath()

// Rektor ismi va surati — «Rektorat» sahifasi bilan bitta so'rov (kalit umumiy)
const { data: leadership } = useFetch<Leadership>('/api/leadership', { key: 'leadership', query: { lang: locale }, lazy: true })
const rector = computed(() => leadership.value?.rector ?? null)
const initials = (name: string) => name.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase()

const statValue = (key: Stat['key']) => props.stats.find(s => s.key === key)?.value
const facts = computed(() => [
  { key: 'founded', number: '1949', suffix: '', hide: false },
  { key: 'students', ...formatStat(statValue('students') ?? 0), hide: statValue('students') === undefined },
  { key: 'staff', ...formatStat(statValue('staff') ?? 0), hide: statValue('staff') === undefined },
  { key: 'languages', number: String(props.languages), suffix: '', hide: !props.languages },
  { key: 'partners', number: String(props.partners), suffix: '', hide: !props.partners },
].filter(fact => !fact.hide))
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :aria-label="t('about.eyebrow')">
    <!-- Raqamlar tasmasi -->
    <dl class="grid grid-cols-2 gap-x-6 gap-y-7 rounded-[28px] bg-brand-950 px-7 py-8 sm:grid-cols-3 sm:px-10 lg:grid-cols-5 lg:gap-0">
      <div
        v-for="(fact, i) in facts"
        :key="fact.key"
        class="flex flex-col-reverse gap-2 lg:px-8 lg:first:pl-2"
        :class="i > 0 && 'lg:border-l lg:border-white/10'"
      >
        <dt class="text-[15px] text-white/70">{{ t(`about.facts.${fact.key}`) }}</dt>
        <dd class="font-display text-[2.6rem] leading-none text-accent-400 sm:text-5xl">{{ fact.number }}{{ fact.suffix }}</dd>
      </div>
    </dl>

    <div class="mt-8 grid gap-6 lg:grid-cols-12">
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
