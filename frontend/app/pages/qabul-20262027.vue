<script setup lang="ts">
import type { Admission } from '#shared/types/api'

// Qabul 2026/2027 (canvas: "Qabul sahifasi")
const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = await useFetch<Admission>('/api/admission', { key: 'admission', query: { lang: locale } })

const LEVELS = ['all', 'bachelor', 'master', 'phd'] as const
const level = ref<(typeof LEVELS)[number]>('all')
const search = ref('')
const fold = (v: string) => v.toLocaleLowerCase().replace(/[‘’ʻʼ`']/g, '\'')
const programs = computed(() => {
  const q = fold(search.value.trim())
  return (data.value?.programs ?? []).filter(p => (level.value === 'all' || p.level === level.value) && (!q || fold(`${p.title} ${p.faculty} ${p.code}`).includes(q)))
})

const open = ref(0)
const tel = (phone: string) => `tel:${phone.replace(/[^\d+]/g, '')}`

useSeo({ title: () => t('admission.title'), description: () => t('admissionPage.lead') })
</script>

<template>
  <div v-if="data">
    <!-- Hero -->
    <section class="relative isolate overflow-hidden bg-brand-900 text-white">
      <!-- Fon: asosiy bino surati, ustida chuqur indigo → binafsha gradient va mint/binafsha yog'dular -->
      <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <img src="/images/main-building.webp" alt="" width="1920" height="1080" loading="eager" class="bg-kb absolute inset-0 size-full object-cover opacity-35">
        <span class="absolute inset-0 bg-[linear-gradient(120deg,rgb(28_21_72/0.96)_0%,rgb(56_43_133/0.86)_45%,rgb(91_75_190/0.7)_100%)]" />
        <span class="absolute -top-40 -left-24 size-[34rem] rounded-full bg-accent-400/20 blur-3xl" />
        <span class="absolute -right-32 -bottom-48 size-[38rem] rounded-full bg-brand-400/35 blur-3xl" />
      </div>
      <span class="decor pointer-events-none absolute -top-52 -right-40 size-[620px] rounded-full border-[60px] border-white/[0.05]" aria-hidden="true" />
      <div class="relative mx-auto max-w-7xl px-4 pt-8 pb-20 sm:px-6 lg:px-8 lg:pb-22">
        <PageBreadcrumbs dark :items="[{ label: t('menu.applicants.title') }, { label: t('admission.title') }]" />
        <div class="mt-12 grid items-end gap-12 lg:grid-cols-[1.4fr_1fr]">
          <div class="min-w-0">
            <p class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-accent-400 uppercase"><span class="h-px w-8 bg-accent-400" />{{ t('admissionPage.eyebrow') }}</p>
            <h1 class="mt-[18px] font-display text-5xl leading-none font-semibold sm:text-[76px]">{{ t('admissionPage.title') }} <span class="text-accent-400 italic">{{ data.year }}</span></h1>
            <p class="mt-6 max-w-xl text-[19px] leading-relaxed text-white/72">{{ t('admissionPage.lead') }}</p>
            <div class="mt-8 flex flex-wrap gap-3">
              <a :href="data.applyUrl" target="_blank" rel="noopener" @click="trackEvent('“Ariza topşiriş” bosildi')" class="inline-flex h-14 items-center gap-2 rounded-full bg-accent-400 px-7 font-semibold text-ink transition-colors hover:bg-accent-300">
                {{ t('admissionPage.apply') }}
                <Icon name="lucide:arrow-up-right" class="size-[18px]" />
              </a>
              <a href="#contact" class="inline-flex h-14 items-center rounded-full border border-white/25 px-7 font-semibold transition-colors hover:bg-white hover:text-ink">{{ t('admissionPage.contact') }}</a>
            </div>
          </div>
          <div class="shine rounded-[28px] border border-white/20 bg-white/10 p-7 shadow-[0_30px_60px_-30px_rgb(0_0_0/0.6)] backdrop-blur-xl" style="--shine-delay: 0.6s">
            <p class="text-[13px] font-semibold tracking-[0.14em] text-white/60 uppercase">{{ t('admissionPage.dates') }}</p>
            <ol class="mt-5">
              <li v-for="(d, i) in data.dates" :key="i" class="flex gap-4 border-b border-white/10 py-3.5 last:border-0">
                <span class="mt-1.5 size-2.5 shrink-0 rounded-full" :class="d.current ? 'bg-accent-400' : 'border-2 border-white/50'" />
                <span class="flex-1">
                  <span class="block font-semibold">{{ d.title }}</span>
                  <span class="mt-0.5 block text-sm text-white/65">{{ d.period }}</span>
                </span>
              </li>
            </ol>
          </div>
        </div>
      </div>
    </section>

    <!-- Bosqichlar -->
    <section class="section-wave relative isolate mt-20 overflow-hidden py-24">
      <!-- Fon: yumshoq indigo → binafsha → mint gradient va yog'dular (shisha kartalar ko'rinishi uchun) -->
      <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <span class="absolute inset-0 bg-[linear-gradient(120deg,#e9e6fb_0%,#d9d3f6_40%,#cdeee2_100%)]" />
        <span class="absolute -top-24 left-[8%] size-[26rem] rounded-full bg-brand-400/40 blur-3xl" />
        <span class="absolute right-[6%] -bottom-24 size-[28rem] rounded-full bg-accent-400/35 blur-3xl" />
        <span class="absolute top-1/3 left-1/2 size-[20rem] -translate-x-1/2 rounded-full bg-white/60 blur-3xl" />
      </div>
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading :eyebrow="t('admissionPage.how')" :title="t('admissionPage.stepsTitle')" />
        <ol class="relative mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <!-- 1 → 4 yo'lini ko'rsatuvchi yorug' chiziq -->
          <span class="pointer-events-none absolute top-[3.25rem] right-[12%] left-[12%] hidden h-px bg-[linear-gradient(90deg,transparent,rgb(255_255_255/0.9),rgb(0_252_180/0.8),rgb(255_255_255/0.9),transparent)] lg:block" aria-hidden="true" />
          <li
            v-for="n in 4"
            :key="n"
            class="shine group relative rounded-[28px] border border-white/70 bg-white/45 p-7 shadow-[0_24px_50px_-30px_rgb(56_43_133/0.55)] backdrop-blur-xl transition duration-300 hover:-translate-y-1.5 hover:bg-white/60 hover:shadow-[0_34px_70px_-30px_rgb(56_43_133/0.6)] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
            :style="{ '--shine-delay': `${0.3 + n * 0.35}s` }"
          >
            <span class="relative grid size-14 place-items-center rounded-2xl bg-[linear-gradient(135deg,var(--color-brand-600),var(--color-brand-400)_55%,var(--color-accent-500))] font-display text-2xl font-semibold text-white shadow-[0_12px_24px_-12px_rgb(56_43_133/0.8)] transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6">{{ String(n).padStart(2, '0') }}</span>
            <p class="relative mt-6 text-[19px] font-semibold text-ink">{{ t(`admission.steps.s${n}.title`) }}</p>
            <p class="relative mt-2 text-[15px] leading-relaxed text-ink/70">{{ t(`admission.steps.s${n}.text`) }}</p>
          </li>
        </ol>
      </div>
    </section>

    <!-- Yo'nalish qidiruvi -->
    <section class="mx-auto max-w-7xl px-4 pt-24 sm:px-6 lg:px-8">
      <div class="flex flex-wrap items-end justify-between gap-6">
        <SectionHeading :eyebrow="t('admissionPage.programsEyebrow')" :title="t('admissionPage.programsTitle')" />
        <p class="text-[15px] text-muted" aria-live="polite">{{ t('programs.shown', { n: programs.length }) }}</p>
      </div>
      <div class="mt-8 flex flex-wrap items-center gap-4">
        <div role="group" :aria-label="t('admissionPage.levelLabel')" class="flex flex-wrap gap-2">
          <button
            v-for="l in LEVELS"
            :key="l"
            type="button"
            :aria-pressed="level === l"
            class="h-11 rounded-full border px-5 text-sm font-semibold transition-colors"
            :class="level === l ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
            @click="level = l"
          >
            {{ l === 'all' ? t('programs.all') : t(`faculty.levels.${l}`) }}
          </button>
        </div>
        <label class="flex h-12 w-full items-center gap-2 rounded-full border border-line bg-white px-4 focus-within:border-accent-600 sm:ml-auto sm:w-[360px]">
          <Icon name="lucide:search" class="size-[18px] shrink-0 text-muted" />
          <span class="sr-only">{{ t('admissionPage.search') }}</span>
          <input v-model="search" type="search" autocomplete="off" :placeholder="t('admissionPage.searchPlaceholder')" class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-muted">
        </label>
      </div>
      <ul v-if="programs.length" class="mt-7 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        <li v-for="p in programs" :key="p.id" class="group relative flex flex-col gap-4 overflow-hidden rounded-3xl border border-line bg-white p-[26px] transition duration-300 before:absolute before:inset-x-0 before:top-0 before:h-1 before:origin-left before:scale-x-0 before:bg-[linear-gradient(90deg,var(--color-brand-600),var(--color-accent-500))] before:transition-transform before:duration-500 hover:-translate-y-1 hover:border-brand-200 hover:shadow-[0_28px_56px_-32px_rgb(56_43_133/0.55)] hover:before:scale-x-100 motion-reduce:transition-none motion-reduce:hover:translate-y-0">
          <div class="flex items-start justify-between gap-3">
            <span class="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-800">{{ t(`faculty.levels.${p.level}`) }}</span>
            <span class="text-[13px] text-muted">{{ p.code }}</span>
          </div>
          <div>
            <h3 class="text-[19px] leading-snug font-semibold transition-colors group-hover:text-brand-700">{{ p.title }}</h3>
            <p class="mt-1.5 text-sm text-muted">{{ p.faculty }}</p>
          </div>
          <dl class="mt-auto grid grid-cols-3 gap-3 border-y border-line/70 py-4 text-[13px]">
            <div><dt class="text-muted">{{ t('admissionPage.form') }}</dt><dd class="mt-0.5 font-semibold">{{ p.form }}</dd></div>
            <div><dt class="text-muted">{{ t('admissionPage.duration') }}</dt><dd class="mt-0.5 font-semibold">{{ t('programs.years', { n: p.years }) }}</dd></div>
            <div><dt class="text-muted">{{ t('admissionPage.price') }}</dt><dd class="mt-0.5 font-semibold">{{ p.price ?? '—' }}</dd></div>
          </dl>
        </li>
      </ul>
      <p v-else class="mt-7 rounded-3xl border border-dashed border-brand-200 bg-white p-10 text-center text-muted">{{ t('admissionPage.empty') }}</p>
    </section>

    <!-- Narx, grant, hujjatlar -->
    <section class="mx-auto grid max-w-7xl gap-6 px-4 pt-24 sm:px-6 md:grid-cols-2 lg:grid-cols-[1fr_1fr_1.3fr] lg:px-8">
      <div class="shine group rounded-[28px] border border-line bg-white p-8 transition duration-300 hover:-translate-y-1 hover:border-brand-200 hover:shadow-[0_28px_56px_-32px_rgb(56_43_133/0.55)] motion-reduce:transition-none motion-reduce:hover:translate-y-0">
        <span class="grid size-[52px] place-items-center rounded-[14px] bg-[linear-gradient(135deg,var(--color-brand-600),var(--color-accent-500))] text-white shadow-[0_10px_22px_-12px_rgb(56_43_133/0.8)] transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6"><Icon name="lucide:wallet" class="size-6" /></span>
        <h2 class="mt-5 text-2xl font-semibold">{{ t('admissionPage.fees.title') }}</h2>
        <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ t('admissionPage.fees.text') }}</p>
        <NuxtLink :to="localePath('/tolov-kontrakt-miqdori')" class="mt-5 inline-flex items-center gap-1.5 font-semibold text-brand-700">{{ t('admissionPage.fees.cta') }} <Icon name="lucide:arrow-right" class="size-4" /></NuxtLink>
      </div>
      <div class="shine group rounded-[28px] border border-line bg-white p-8 transition duration-300 hover:-translate-y-1 hover:border-brand-200 hover:shadow-[0_28px_56px_-32px_rgb(56_43_133/0.55)] motion-reduce:transition-none motion-reduce:hover:translate-y-0">
        <span class="grid size-[52px] place-items-center rounded-[14px] bg-[linear-gradient(135deg,var(--color-brand-600),var(--color-accent-500))] text-white shadow-[0_10px_22px_-12px_rgb(56_43_133/0.8)] transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6"><Icon name="lucide:award" class="size-6" /></span>
        <h2 class="mt-5 text-2xl font-semibold">{{ t('admissionPage.grants.title') }}</h2>
        <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ t('admissionPage.grants.text') }}</p>
        <NuxtLink :to="localePath('/talim-grantlar-soni')" class="mt-5 inline-flex items-center gap-1.5 font-semibold text-brand-700">{{ t('admissionPage.grants.cta') }} <Icon name="lucide:arrow-right" class="size-4" /></NuxtLink>
      </div>
      <div class="rounded-[28px] border border-brand-100 bg-[linear-gradient(150deg,#f3f1fd_0%,#e7f8f0_100%)] p-8 md:col-span-2 lg:col-span-1">
        <h2 class="text-2xl font-semibold">{{ t('admissionPage.documents') }}</h2>
        <ul class="mt-5 flex flex-col gap-3 text-[15px]">
          <li v-for="doc in data.documents" :key="doc" class="flex items-start gap-3">
            <span class="grid size-6 shrink-0 place-items-center rounded-full bg-brand-800 text-white"><Icon name="lucide:check" class="size-3.5" /></span>
            {{ doc }}
          </li>
        </ul>
        <a v-if="data.documentsUrl" :href="data.documentsUrl" target="_blank" rel="noopener" class="mt-5 inline-flex items-center gap-1.5 font-semibold text-brand-800">{{ t('admissionPage.documentsFull') }} <Icon name="lucide:arrow-right" class="size-4" /></a>
      </div>
    </section>

    <!-- Savol-javob -->
    <section class="mx-auto grid max-w-7xl gap-12 px-4 pt-24 sm:px-6 lg:grid-cols-[1fr_2fr] lg:px-8">
      <div>
        <SectionHeading :eyebrow="t('admissionPage.faqEyebrow')" :title="t('admissionPage.faqTitle')" :text="t('admissionPage.faqText')" />
      </div>
      <ul class="flex flex-col gap-3">
        <li v-for="(f, i) in data.faq" :key="i" class="rounded-[20px] border bg-white transition duration-300" :class="open === i ? 'border-brand-300 shadow-[0_20px_44px_-30px_rgb(56_43_133/0.6)]' : 'border-line hover:border-brand-200'">
          <h3>
            <button
              type="button"
              :aria-expanded="open === i"
              :aria-controls="`faq-${i}`"
              class="flex min-h-16 w-full items-center justify-between gap-4 px-6 py-[18px] text-left text-[17px] font-semibold text-ink"
              @click="open = open === i ? -1 : i"
            >
              {{ f.q }}
              <span class="grid size-9 shrink-0 place-items-center rounded-full bg-brand-50 text-brand-800">
                <Icon name="lucide:chevron-down" class="size-[18px] transition-transform" :class="open === i && 'rotate-180'" />
              </span>
            </button>
          </h3>
          <p v-show="open === i" :id="`faq-${i}`" class="px-6 pb-[22px] text-[15px] leading-relaxed text-muted">{{ f.a }}</p>
        </li>
      </ul>
    </section>

    <!-- Qabul komissiyasi -->
    <section id="contact" class="mx-auto max-w-7xl scroll-mt-32 px-4 py-24 sm:px-6 lg:px-8">
      <div class="shine relative isolate flex flex-wrap items-center justify-between gap-8 overflow-hidden rounded-[32px] bg-[linear-gradient(120deg,#241c5e_0%,#382b85_50%,#5b4bbe_100%)] p-7 text-white shadow-[0_34px_70px_-34px_rgb(56_43_133/0.7)] sm:p-12">
        <span class="decor pointer-events-none absolute -top-24 -right-16 -z-10 size-80 rounded-full bg-accent-400/25 blur-3xl" aria-hidden="true" />
        <div class="max-w-xl">
          <h2 class="font-display text-4xl leading-tight font-semibold sm:text-[40px]">{{ t('admissionPage.commission') }}</h2>
          <p class="mt-3 leading-relaxed text-white/68">{{ data.contact.address }} · {{ data.contact.hours }}</p>
        </div>
        <div class="flex flex-wrap gap-3">
          <a :href="tel(data.contact.phone)" class="inline-flex h-14 items-center gap-2.5 rounded-full bg-accent-400 px-6 font-semibold text-ink transition-colors hover:bg-accent-300">
            <Icon name="lucide:phone" class="size-[18px]" />
            {{ data.contact.phone }}
          </a>
          <a :href="data.contact.telegram" target="_blank" rel="noopener" class="inline-flex h-14 items-center gap-2.5 rounded-full border border-white/25 px-6 font-semibold transition-colors hover:bg-white hover:text-ink">
            <Icon name="simple-icons:telegram" class="size-[18px]" />
            Telegram
          </a>
        </div>
      </div>
    </section>
    <SectionNav />
  </div>
</template>
