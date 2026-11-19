<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// Binolar kartalari (Aloqa sahifasi va «O'quv binolari» sahifasi uchun umumiy): Yandex xaritasi, manzil, telefon, yo'nalish.
// Ma'lumot bitta joydan — admin panel → Sozlamalar → «Binolar va xarita»
defineProps<{ campuses: ContactPage['campuses'] }>()

const { t } = useI18n()
const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`
</script>

<template>
  <ul class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
    <li v-for="c in campuses" :key="c.id" class="overflow-hidden rounded-3xl border border-line bg-white">
      <!-- Yandex xaritasi (bosh sahifadagi bilan bir xil); xarita bo'lmasa — belgi -->
      <div class="relative h-[190px] overflow-hidden bg-brand-100">
        <MapFrame v-if="c.mapEmbed" :src="c.mapEmbed" :title="`${c.name} — ${t('contact.route')}`" />
        <span v-else class="absolute top-1/2 left-1/2 size-10 -translate-x-1/2 -translate-y-1/2 -rotate-45 rounded-[999px_999px_999px_0] bg-brand-800" aria-hidden="true" />
      </div>
      <div class="p-5">
        <h3 class="text-lg font-semibold">{{ c.name }}</h3>
        <p class="mt-2 text-sm leading-normal text-muted">{{ c.address }}</p>
        <a :href="tel(c.phone)" class="mt-2.5 block text-[15px] font-semibold hover:text-brand-700">{{ c.phone }}</a>
        <a :href="c.mapUrl" target="_blank" rel="noopener" class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700">{{ t('contact.route') }} →</a>
      </div>
    </li>
  </ul>
</template>
