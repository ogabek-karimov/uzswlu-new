<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// Binolar kartalari (Aloqa sahifasi va «O'quv binolari» sahifasi uchun umumiy): Yandex xaritasi, manzil, telefon, yo'nalish.
// Ma'lumot bitta joydan — admin panel → Sozlamalar → «Binolar va xarita»
defineProps<{ campuses: ContactPage['campuses'] }>()

const { t } = useI18n()

// Bino logosi: bosh bino — universitet logosi, qolganlari — o'sha binodagi fakultet logosi (fakultetlar ma'lumotidan)
const CAMPUS_FACULTY: Record<string, string> = {
  philology: 'english-philology',
  journalism: 'international-journalism',
  russian: 'russian-philology',
}
const { data: faculties } = await useFetch<{ items: { slug: string; logo: string | null }[] }>('/api/faculties', { key: 'faculties-logos', query: { lang: 'uz' } })
function logoOf(id: string): string | null {
  if (id === 'main') return '/logos/uzswlu.png'
  const slug = CAMPUS_FACULTY[id]
  return faculties.value?.items.find(f => f.slug === slug)?.logo ?? null
}
const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`
</script>

<template>
  <ul v-reveal class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
    <li v-for="c in campuses" :key="c.id" data-reveal-item class="group/campus overflow-hidden rounded-3xl border border-line bg-white shadow-[0_1px_0_rgb(19_17_47/0.04)] transition duration-300 ease-out hover:z-10 hover:-translate-y-1.5 hover:scale-[1.03] hover:border-brand-300 hover:shadow-[0_30px_60px_-28px_rgb(56_43_133/0.55)] motion-reduce:transition-none motion-reduce:hover:transform-none">
      <!-- Yandex xaritasi (bosh sahifadagi bilan bir xil); xarita bo'lmasa — belgi -->
      <div class="relative h-[250px] overflow-hidden bg-brand-100">
        <MapFrame v-if="c.mapEmbed" :src="c.mapEmbed" :title="`${c.name} — ${t('contact.route')}`" />
        <!-- Bino logosi: hamma kartada bir xil o'lcham va joy (xaritaning yuqori chap burchagi) -->
        <span v-if="logoOf(c.id)" class="pointer-events-none absolute top-3 left-3 z-10 size-[62px] rounded-full shadow-[0_0_22px_-2px_rgb(0_252_180/0.65)]" aria-hidden="true">
          <!-- Aylanuvchi yorqin nur (mint → indigo) -->
          <span class="absolute inset-0 animate-spin rounded-full bg-[conic-gradient(from_0deg,#00fcb4,#7f70d3,#ffffff,#00fcb4)] [animation-duration:4s] motion-reduce:animate-none" />
          <span class="absolute inset-[3px] grid place-items-center overflow-hidden rounded-full bg-white">
            <img :src="logoOf(c.id)!" alt="" width="56" height="56" loading="lazy" class="size-full object-cover" :class="c.id === 'main' && 'scale-90 object-contain'">
          </span>
        </span>
        <span v-else class="absolute top-1/2 left-1/2 size-10 -translate-x-1/2 -translate-y-1/2 -rotate-45 rounded-[999px_999px_999px_0] bg-brand-800" aria-hidden="true" />
      </div>
      <div class="p-5">
        <h3 class="text-lg font-semibold transition-colors group-hover/campus:text-brand-700">{{ c.name }}</h3>
        <p class="mt-2 text-sm leading-normal text-muted">{{ c.address }}</p>
        <a :href="tel(c.phone)" class="mt-2.5 block text-[15px] font-semibold hover:text-brand-700">{{ c.phone }}</a>
        <a :href="c.mapUrl" target="_blank" rel="noopener" class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700">{{ t('contact.route') }} →</a>
      </div>
    </li>
  </ul>
</template>
