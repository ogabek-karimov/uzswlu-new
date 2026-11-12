<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// «Biz bilan bog'lanish»: binolar kartalari (telefon, e-pochta, manzil, xarita).
// Ma'lumot — admin panel: Sozlamalar → Binolar va xarita; Aloqa sahifasi bilan bitta so'rov (kalit umumiy)
const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale }, lazy: true })
const campuses = computed(() => data.value?.campuses ?? [])
const tel = (phone: string) => `tel:${phone.replace(/[^\d+]/g, '')}`
</script>

<template>
  <section v-if="campuses.length" class="relative overflow-hidden py-16 lg:py-24" :aria-label="t('homeContact.title')">
    <!-- Yumshoq rangli fon (yalpiz va lavanda) -->
    <div class="decor pointer-events-none absolute inset-0" aria-hidden="true">
      <span class="absolute -top-24 -left-32 size-[520px] rounded-full bg-accent-100 opacity-80 blur-3xl" />
      <span class="absolute -right-24 -bottom-32 size-[560px] rounded-full bg-brand-100 opacity-80 blur-3xl" />
    </div>

    <div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <SectionHeading
        :eyebrow="t('homeContact.eyebrow')"
        :title="t('homeContact.title')"
        :link="{ to: localePath('/aloqa'), label: t('homeContact.all') }"
      />

      <ul class="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <li v-for="(c, i) in campuses" :key="c.id">
          <article class="group relative flex h-full flex-col overflow-hidden rounded-[28px] border border-white bg-white/85 shadow-[0_1px_0_rgba(19,17,47,0.04)] backdrop-blur transition duration-300 hover:-translate-y-1.5 hover:border-brand-200 hover:shadow-[0_34px_70px_-38px_rgba(19,17,47,0.55)] motion-reduce:transition-none motion-reduce:hover:translate-y-0">
            <!-- Sarlavha: tartib raqami, belgi va nomi -->
            <div class="relative px-6 pt-6">
              <span class="pointer-events-none absolute -top-2 right-4 font-display text-[5.5rem] leading-none font-semibold text-brand-50 transition-colors duration-300 select-none group-hover:text-accent-100" aria-hidden="true">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="relative grid size-12 place-items-center rounded-2xl bg-brand-800 text-[22px] text-accent-400 transition-transform duration-300 group-hover:scale-105 group-hover:-rotate-6 motion-reduce:transition-none">
                <Icon name="lucide:building-2" />
              </span>
              <h3 class="relative mt-4 line-clamp-2 min-h-[2lh] font-display text-[1.375rem] leading-tight font-semibold text-ink">{{ c.name }}</h3>
            </div>

            <!-- Aloqa qatorlari: har biri bosiladi -->
            <ul class="mt-3 flex flex-col px-3 text-sm">
              <li v-if="c.phone">
                <a :href="tel(c.phone)" class="flex items-start gap-3 rounded-2xl px-3 py-2 transition-colors hover:bg-brand-50">
                  <span class="grid size-8 shrink-0 place-items-center rounded-xl bg-accent-100 text-base text-accent-600"><Icon name="lucide:phone" /></span>
                  <span class="min-w-0"><span class="block text-[11px] font-semibold tracking-wider text-muted uppercase">{{ t('homeContact.phone') }}</span><span class="font-medium text-ink">{{ c.phone }}</span></span>
                </a>
              </li>
              <li v-if="c.email">
                <a :href="`mailto:${c.email}`" class="flex items-start gap-3 rounded-2xl px-3 py-2 transition-colors hover:bg-brand-50">
                  <span class="grid size-8 shrink-0 place-items-center rounded-xl bg-brand-100 text-base text-brand-700"><Icon name="lucide:mail" /></span>
                  <span class="min-w-0"><span class="block text-[11px] font-semibold tracking-wider text-muted uppercase">{{ t('homeContact.email') }}</span><span class="block truncate font-medium text-ink">{{ c.email }}</span></span>
                </a>
              </li>
              <li>
                <a :href="c.mapUrl" target="_blank" rel="noopener" class="flex items-start gap-3 rounded-2xl px-3 py-2 transition-colors hover:bg-brand-50">
                  <span class="grid size-8 shrink-0 place-items-center rounded-xl bg-[#FFF1D6] text-base text-[#9A5B00]"><Icon name="lucide:map-pin" /></span>
                  <span class="min-w-0"><span class="block text-[11px] font-semibold tracking-wider text-muted uppercase">{{ t('homeContact.address') }}</span><span class="line-clamp-3 min-h-[3lh] font-medium text-ink">{{ c.address }}</span></span>
                </a>
              </li>
            </ul>

            <!-- Xarita (doim rangli) -->
            <div class="relative m-3 mt-auto aspect-[4/3] overflow-hidden rounded-[20px] bg-brand-50">
              <iframe
                v-if="c.mapEmbed"
                :src="c.mapEmbed"
                loading="lazy"
                referrerpolicy="no-referrer-when-downgrade"
                :title="`${c.name} — ${t('homeContact.map')}`"
                class="absolute inset-0 size-full border-0"
              />
              <a :href="c.mapUrl" target="_blank" rel="noopener" class="absolute top-3 left-3 inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1.5 text-xs font-semibold text-ink shadow-[0_8px_20px_-10px_rgba(19,17,47,0.5)] transition-colors hover:bg-accent-400">
                {{ t('homeContact.openMap') }}
                <Icon name="lucide:arrow-up-right" class="text-sm" />
              </a>
            </div>
          </article>
        </li>
      </ul>
    </div>
  </section>
</template>
