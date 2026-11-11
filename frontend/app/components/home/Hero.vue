<script setup lang="ts">
import type { Stat } from '#shared/types/api'

const props = defineProps<{ students?: Stat }>()

const { t } = useI18n()
const localePath = useLocalePath()
const router = useRouter()

const query = ref('')

function submit() {
  const q = query.value.trim()
  router.push({ path: localePath('/search'), query: q ? { q } : undefined })
}

const chips = ['fees', 'schedule', 'master', 'grants'] as const

// Har xil tillardagi salomlashuvlar — "jahon tillari" g'oyasining vizual ifodasi.
// x/y — foizda, size — kartaning kengligiga nisbatan (cqw).
const greetings = [
  { word: 'Salom', x: 9, y: 9, size: 13, cls: 'font-display italic text-accent-400' },
  { word: 'Hola', x: 70, y: 6, size: 6.5, cls: 'text-white/45' },
  { word: 'Привет', x: 50, y: 20, size: 8, cls: 'text-white/80' },
  { word: 'Hello', x: 12, y: 32, size: 15, cls: 'font-display font-semibold text-white' },
  { word: '你好', x: 64, y: 40, size: 12, cls: 'text-brand-300' },
  { word: 'Bonjour', x: 8, y: 54, size: 7.5, cls: 'text-white/55' },
  { word: 'こんにちは', x: 42, y: 59, size: 6, cls: 'text-white/70' },
  { word: 'مرحبا', x: 13, y: 70, size: 10, cls: 'text-white/80', rtl: true },
  { word: 'Hallo', x: 58, y: 71, size: 10, cls: 'font-display italic text-accent-300' },
  { word: '안녕하세요', x: 30, y: 86, size: 5.5, cls: 'text-white/45' },
]

const circleText = computed(() => `${t('university.short')} • 1949 • `.repeat(2))
</script>

<template>
  <section class="relative overflow-hidden">
    <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <div class="absolute -top-48 -right-40 size-[44rem] rounded-full bg-brand-100/70 blur-3xl" />
      <div class="absolute top-1/3 -left-48 size-[28rem] rounded-full bg-accent-100 blur-3xl" />
    </div>

    <div class="mx-auto grid max-w-7xl items-center gap-14 px-4 pt-10 pb-20 sm:px-6 lg:grid-cols-12 lg:gap-10 lg:px-8 lg:pt-16 lg:pb-24">
      <div class="lg:col-span-7">
        <p class="inline-flex items-center gap-2 rounded-full border border-line bg-white/70 px-3.5 py-1.5 text-xs font-semibold tracking-[0.14em] text-brand-700 uppercase">
          <span class="size-1.5 rounded-full bg-accent-500" />
          {{ t('hero.eyebrow') }}
        </p>

        <h1 class="mt-6 font-display text-5xl leading-[1.04] font-semibold tracking-tight text-ink sm:text-6xl xl:text-7xl">
          {{ t('hero.title1') }}
          <span class="block text-brand-700 italic">{{ t('hero.title2') }}</span>
        </h1>

        <p class="mt-6 max-w-xl text-lg leading-relaxed text-muted">{{ t('hero.text') }}</p>

        <div class="mt-8 flex flex-wrap gap-3">
          <NuxtLink
            :to="localePath('/qabul-20262027')"
            class="group inline-flex items-center gap-2 rounded-full bg-brand-800 px-6 py-3.5 font-semibold text-white shadow-[0_12px_30px_-12px_var(--color-brand-700)] transition-colors hover:bg-brand-700"
          >
            {{ t('hero.ctaPrimary') }}
            <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-0.5" />
          </NuxtLink>
          <NuxtLink
            :to="localePath('/bakalavriat')"
            class="inline-flex items-center gap-2 rounded-full border border-ink/15 bg-white px-6 py-3.5 font-semibold text-ink transition-colors hover:border-ink"
          >
            {{ t('hero.ctaSecondary') }}
          </NuxtLink>
        </div>

        <form role="search" class="mt-10 max-w-xl" @submit.prevent="submit">
          <label for="hero-search" class="sr-only">{{ t('hero.searchLabel') }}</label>
          <div class="flex items-center gap-2 rounded-2xl border border-line bg-white p-2 shadow-sm transition focus-within:border-brand-300 focus-within:ring-4 focus-within:ring-brand-100">
            <button type="submit" class="ml-3 grid shrink-0 cursor-pointer place-items-center text-muted transition-colors hover:text-brand-800" :aria-label="t('hero.searchButton')">
              <Icon name="lucide:search" class="size-5" />
            </button>
            <input
              id="hero-search"
              v-model="query"
              type="search"
              autocomplete="off"
              :placeholder="t('hero.searchPlaceholder')"
              class="min-w-0 flex-1 bg-transparent py-2 text-[15px] text-ink outline-none placeholder:text-muted/70 focus-visible:outline-none"
            >
            <button type="submit" class="rounded-xl bg-ink px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-800">
              {{ t('hero.searchButton') }}
            </button>
          </div>
          <div class="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span class="text-muted">{{ t('hero.popular') }}</span>
            <NuxtLink
              v-for="chip in chips"
              :key="chip"
              :to="{ path: localePath('/search'), query: { q: t(`hero.chips.${chip}`) } }"
              class="rounded-full bg-brand-50 px-3 py-1 text-brand-800 transition-colors hover:bg-brand-100"
            >
              {{ t(`hero.chips.${chip}`) }}
            </NuxtLink>
          </div>
        </form>
      </div>

      <!-- Vizual: salomlashuvlar kartasi -->
      <div class="relative mx-auto w-full max-w-md lg:col-span-5 lg:max-w-none">
        <div class="@container relative aspect-[4/5] overflow-hidden rounded-[2rem] bg-brand-900 shadow-[0_40px_80px_-40px_var(--color-brand-900)]">
          <svg class="decor absolute inset-0 size-full text-white/[0.07]" viewBox="0 0 400 500" fill="none" aria-hidden="true">
            <circle cx="200" cy="250" r="190" stroke="currentColor" stroke-width="1.5" />
            <ellipse cx="200" cy="250" rx="95" ry="190" stroke="currentColor" stroke-width="1.5" />
            <ellipse cx="200" cy="250" rx="160" ry="190" stroke="currentColor" stroke-width="1" />
            <path d="M10 250h380M30 160h340M30 340h340M80 90h240M80 410h240" stroke="currentColor" stroke-width="1" />
          </svg>

          <span
            v-for="(g, i) in greetings"
            :key="g.word"
            class="absolute animate-float leading-none whitespace-nowrap select-none"
            :class="g.cls"
            :dir="g.rtl ? 'rtl' : undefined"
            :style="{ left: `${g.x}%`, top: `${g.y}%`, fontSize: `${g.size}cqw`, animationDelay: `${-i * 0.9}s` }"
            aria-hidden="true"
          >{{ g.word }}</span>
        </div>

        <!-- Aylanuvchi muhr -->
        <div class="absolute -top-6 -right-3 grid size-28 place-items-center rounded-full bg-accent-400 text-ink shadow-xl sm:-right-6 sm:size-32" aria-hidden="true">
          <svg viewBox="0 0 100 100" class="absolute inset-0 size-full animate-[spin_28s_linear_infinite]">
            <defs>
              <path id="seal-circle" d="M50,50 m-38,0 a38,38 0 1,1 76,0 a38,38 0 1,1 -76,0" />
            </defs>
            <text class="fill-ink text-[7.2px] font-semibold tracking-[0.12em] uppercase">
              <textPath href="#seal-circle" textLength="236" lengthAdjust="spacingAndGlyphs">{{ circleText }}</textPath>
            </text>
          </svg>
          <span class="font-display text-xl font-semibold">1949</span>
        </div>

        <!-- Talabalar soni (HEMIS) -->
        <div v-if="props.students" class="absolute -bottom-6 -left-3 flex items-center gap-4 rounded-2xl bg-white px-5 py-4 shadow-[0_20px_50px_-20px_rgba(19,17,47,0.45)] sm:-left-8">
          <div class="flex -space-x-2" aria-hidden="true">
            <span class="grid size-9 place-items-center rounded-full border-2 border-white bg-brand-100 text-xs font-semibold text-brand-800">A</span>
            <span class="grid size-9 place-items-center rounded-full border-2 border-white bg-accent-100 text-xs font-semibold text-accent-600">Я</span>
            <span class="grid size-9 place-items-center rounded-full border-2 border-white bg-brand-800 text-xs font-semibold text-white">文</span>
          </div>
          <div>
            <p class="font-display text-2xl leading-none font-semibold text-ink">{{ formatStat(props.students.value).number }}{{ formatStat(props.students.value).suffix }}</p>
            <p class="mt-1 text-xs text-muted">{{ t('hero.students') }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
