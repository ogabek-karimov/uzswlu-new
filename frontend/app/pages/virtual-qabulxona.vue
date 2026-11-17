<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// Virtual qabulxona: murojaat tartibi + shakl (shakl «Aloqa» sahifasidagi bilan bir xil komponent)
const { t, locale } = useI18n()
const { data } = await useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale } })

const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`
const steps = computed(() => [0, 1, 2, 3].map(i => ({ title: t(`reception.steps[${i}].title`), text: t(`reception.steps[${i}].text`) })))
const rules = computed(() => [0, 1, 2, 3].map(i => t(`reception.rules[${i}]`)))

useSeo({ title: () => t('reception.title'), description: () => t('reception.lead') })
</script>

<template>
  <div v-if="data">
    <PageIntro :crumbs="[{ label: t('reception.title') }]" :title="t('reception.title')" :lead="t('reception.lead')" />

    <section class="mx-auto max-w-7xl px-4 pt-9 sm:px-6 lg:px-8">
      <div class="grid gap-4 sm:grid-cols-2">
        <a :href="tel(data.hotline.phone)" class="rounded-3xl bg-brand-900 p-6 text-white transition-colors hover:bg-brand-800">
          <span class="block text-[13px] text-white/60">{{ t('reception.hotline') }}</span>
          <span class="mt-1.5 block font-display text-[28px] font-semibold">{{ data.hotline.phone }}</span>
          <span v-if="data.hotline.ext" class="mt-1 block text-[13px] text-accent-400">{{ t('contact.ext', { ext: data.hotline.ext }) }}</span>
        </a>
        <a v-if="data.reception" :href="tel(data.reception)" class="rounded-3xl border border-line bg-white p-6 transition-colors hover:border-accent-500">
          <span class="block text-[13px] text-muted">{{ t('reception.phone') }}</span>
          <span class="mt-1.5 block font-display text-[28px] font-semibold">{{ data.reception }}</span>
        </a>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 pt-16 sm:px-6 lg:px-8" aria-labelledby="rq-steps">
      <h2 id="rq-steps" class="font-display text-4xl font-semibold sm:text-[40px]">{{ t('reception.stepsTitle') }}</h2>
      <ol class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <li v-for="(s, i) in steps" :key="i" class="rounded-3xl border border-line bg-white p-6">
          <span class="grid size-10 place-items-center rounded-full bg-brand-50 font-display text-lg font-semibold text-brand-800">{{ i + 1 }}</span>
          <h3 class="mt-4 text-lg font-semibold">{{ s.title }}</h3>
          <p class="mt-1.5 text-[15px] leading-relaxed text-muted">{{ s.text }}</p>
        </li>
      </ol>
    </section>

    <section class="mx-auto grid max-w-7xl items-start gap-7 px-4 pt-16 pb-24 sm:px-6 lg:grid-cols-[1fr_1.1fr] lg:px-8">
      <div class="rounded-[28px] bg-brand-50 p-6 sm:p-8">
        <h2 class="font-display text-[30px] font-semibold">{{ t('reception.rulesTitle') }}</h2>
        <ul class="mt-5 grid gap-3">
          <li v-for="(r, i) in rules" :key="i" class="flex gap-3 text-[15px] leading-relaxed text-ink/85">
            <Icon name="lucide:circle-check" class="mt-0.5 size-5 shrink-0 text-accent-600" />
            {{ r }}
          </li>
        </ul>
      </div>
      <AppealForm :recipients="data.recipients" />
    </section>
    <SectionNav />
  </div>
</template>
