<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// «O'quv binolari»: Aloqa sahifasidagi binolar bilan bir xil ma'lumot (admin panel → Sozlamalar → «Binolar va xarita»)
const { t, locale } = useI18n()

const { data } = await useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale } })

useSeo({ title: () => t('social.buildings'), description: () => t('buildings.lead') })
</script>

<template>
  <div>
    <PageIntro :crumbs="[{ label: t('social.buildings') }]" :title="t('social.buildings')" :lead="t('buildings.lead')" />
    <section class="mx-auto max-w-7xl px-4 pt-3 pb-24 sm:px-6 lg:px-8">
      <CampusCards v-if="data?.campuses.length" :campuses="data.campuses" />
      <p v-else class="mt-6 text-muted">{{ t('buildings.empty') }}</p>
    </section>
    <SectionNav />
  </div>
</template>
