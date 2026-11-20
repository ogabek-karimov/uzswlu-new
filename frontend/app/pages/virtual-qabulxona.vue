<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// Virtual qabulxona: murojaat tartibi + shakl (shakl «Aloqa» sahifasidagi bilan bir xil komponent)
const { t, locale } = useI18n()
const { data } = await useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale } })

const steps = computed(() => [0, 1, 2, 3].map(i => ({ title: t(`reception.steps[${i}].title`), text: t(`reception.steps[${i}].text`) })))
const rules = computed(() => [0, 1, 2, 3].map(i => t(`reception.rules[${i}]`)))

useSeo({ title: () => t('reception.title'), description: () => t('reception.lead') })
</script>

<template>
  <div v-if="data">
    <PageIntro :crumbs="[{ label: t('reception.title') }]" :title="t('reception.title')" :lead="t('reception.lead')" />


    <!-- Chapda — ko'rib chiqish tartibi, o'ngda — yuborishdan oldin eslatmalar; ikkalasi 2×2, bir xil o'lchamda -->
    <section class="mx-auto grid max-w-7xl items-stretch gap-6 px-4 pt-6 sm:px-6 lg:grid-cols-2 lg:px-8">
      <div class="rounded-[30px] border border-line bg-white/70 p-5 shadow-[0_30px_60px_-44px_rgb(56_43_133/0.5)] backdrop-blur-sm sm:p-7" aria-labelledby="rq-steps">
        <h2 id="rq-steps" class="font-display text-[28px] leading-tight font-semibold sm:text-[32px]">{{ t('reception.stepsTitle') }}</h2>
        <ol class="mt-5 grid gap-3.5 sm:grid-cols-2">
          <li v-for="(s, i) in steps" :key="i" class="lift-card grad-border group rounded-[22px] p-5">
            <span class="grid size-9 place-items-center rounded-full bg-brand-50 font-display text-base font-semibold text-brand-800 transition-colors duration-300 group-hover:bg-brand-800 group-hover:text-white">{{ i + 1 }}</span>
            <h3 class="mt-3 text-[17px] font-semibold">{{ s.title }}</h3>
            <p class="mt-1 text-[14px] leading-relaxed text-muted">{{ s.text }}</p>
          </li>
        </ol>
      </div>
      <div class="rounded-[30px] border border-brand-100 bg-[linear-gradient(160deg,var(--color-brand-50),#fff_65%)] p-5 shadow-[0_30px_60px_-44px_rgb(56_43_133/0.5)] sm:p-7" aria-labelledby="rq-rules">
        <h2 id="rq-rules" class="font-display text-[28px] leading-tight font-semibold sm:text-[32px]">{{ t('reception.rulesTitle') }}</h2>
        <ul class="mt-5 grid gap-3.5 sm:grid-cols-2">
          <li v-for="(r, i) in rules" :key="i" class="lift-card group flex gap-3 rounded-[22px] p-5 text-[14px] leading-relaxed text-ink/85">
            <span class="grid size-9 shrink-0 place-items-center rounded-full bg-accent-100 text-accent-700 transition-transform duration-300 group-hover:scale-110"><Icon name="lucide:check" class="text-lg" /></span>
            <span class="pt-1.5">{{ r }}</span>
          </li>
        </ul>
      </div>
    </section>

    <!-- Murojaat shakli: keng, pastda -->
    <section class="mx-auto max-w-7xl px-4 pt-12 pb-24 sm:px-6 lg:px-8">
      <AppealForm :recipients="data.recipients" :rude-words="data.rudeWords" />
    </section>
    <SectionNav />
  </div>
</template>
