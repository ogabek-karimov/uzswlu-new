<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// Aloqa va Virtual qabulxona (canvas: "Aloqa va Virtual qabulxona")
const { t, locale } = useI18n()

const { data } = await useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale } })

const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`

useSeo({ title: () => t('contact.title'), description: () => t('contact.lead') })
</script>

<template>
  <div v-if="data">
    <PageIntro :crumbs="[{ label: t('nav.contact') }]" :title="t('contact.title')" :lead="t('contact.lead')" />

    <section class="mx-auto max-w-7xl px-4 pt-9 sm:px-6 lg:px-8">
      <div v-reveal class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <a :href="tel(data.hotline.phone)" data-reveal-item class="rounded-3xl bg-brand-900 p-6 text-white transition-colors hover:bg-brand-800">
          <span class="block text-[13px] text-white/60">{{ t('contact.hotline') }}</span>
          <span class="mt-1.5 block font-display text-[28px] font-semibold">{{ data.hotline.phone }}</span>
          <span v-if="data.hotline.ext" class="mt-1 block text-[13px] text-accent-400">{{ t('contact.ext', { ext: data.hotline.ext }) }}</span>
        </a>
        <div v-for="e in data.emails" :key="e.value" data-reveal-item class="rounded-3xl border border-line bg-white p-6">
          <span class="block text-[13px] text-muted">{{ e.title }}</span>
          <a :href="`mailto:${e.value}`" class="mt-1.5 block text-lg font-semibold break-all hover:text-brand-700">{{ e.value }}</a>
          <span v-if="e.extra.length" class="mt-1 block text-[13px] break-all text-muted">{{ e.extra.join(' · ') }}</span>
        </div>
        <a href="https://t.me/UzSWLU" target="_blank" rel="noopener" data-reveal-item class="rounded-3xl border border-line bg-white p-6 text-ink transition-colors hover:border-accent-500">
          <span class="block text-[13px] text-muted">Telegram</span>
          <span class="mt-1.5 block text-lg font-semibold">t.me/UzSWLU</span>
          <span class="mt-1 block text-[13px] text-brand-700">{{ t('contact.channel') }} →</span>
        </a>
      </div>
    </section>

    <!-- Binolar -->
    <section class="mx-auto max-w-7xl px-4 pt-16 sm:px-6 lg:px-8">
      <h2 class="font-display text-4xl font-semibold sm:text-[40px]">{{ t('contact.campuses') }}</h2>
      <CampusCards :campuses="data.campuses" />
    </section>

    <!-- Rahbariyat telefonlari + Virtual qabulxona -->
    <section v-reveal class="mx-auto grid max-w-7xl items-start gap-7 px-4 pt-16 pb-24 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:px-8">
      <div data-reveal-item class="min-w-0">
        <h2 class="font-display text-[34px] font-semibold">{{ t('contact.leaders') }}</h2>
        <div class="mt-5 overflow-x-auto rounded-[22px] border border-line bg-white">
          <table class="w-full min-w-[520px] border-collapse text-sm">
            <thead>
              <tr class="text-left text-xs text-muted">
                <th scope="col" class="border-b border-line px-[18px] py-3.5 font-semibold">{{ t('contact.table.name') }}</th>
                <th scope="col" class="border-b border-line px-[18px] py-3.5 font-semibold">{{ t('contact.table.ext') }}</th>
                <th scope="col" class="border-b border-line px-[18px] py-3.5 font-semibold">{{ t('contact.table.phone') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in data.leaders" :key="l.name" class="border-b border-line/60 last:border-0">
                <td class="px-[18px] py-3.5"><span class="block font-semibold">{{ l.name }}</span><span class="mt-0.5 block text-muted">{{ l.role }}</span></td>
                <td class="px-[18px] py-3.5 font-semibold">{{ l.ext }}</td>
                <td class="px-[18px] py-3.5 whitespace-nowrap"><a :href="tel(l.phone)" class="hover:text-brand-700">{{ l.phone }}</a></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 text-[13px] text-muted">{{ t('contact.reception', { phone: data.reception }) }}</p>
      </div>

      <AppealForm data-reveal-item :recipients="data.recipients" />
    </section>
    <SectionNav />
  </div>
</template>
