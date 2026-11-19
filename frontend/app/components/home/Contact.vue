<script setup lang="ts">
import type { ContactPage, Faculty } from '#shared/types/api'

// «Biz bilan bog'lanish»: chapda binolarni tanlash (najottalim.uz kabi), o'ngda tanlangan binoning Yandex xaritasi.
// Ma'lumot — admin panel: Sozlamalar → Binolar va xarita; Aloqa sahifasi bilan bitta so'rov (kalit umumiy)
const props = defineProps<{ faculties?: Faculty[] }>()

const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale }, lazy: true })
const campuses = computed(() => data.value?.campuses ?? [])
// Bino belgisi: bosh bino — universitet logosi, qolganlari — o'z fakultetining logosi (Fakultetlar bo'limidagi rasm).
// Bino kaliti (admin: Binolar va kampuslar) fakultet slug'iga shu ro'yxat orqali bog'lanadi; topilmasa — universitet logosi
const FACULTY_OF: Record<string, string> = {
  philology: 'english-philology',
  journalism: 'international-journalism',
  russian: 'russian-philology',
}
function logoFor(key: string) {
  const slug = FACULTY_OF[key] ?? key
  const f = (props.faculties ?? []).find(x => x.slug === slug)
  return f?.logo || '/logos/uzswlu.png'
}
// Tanlangan bino (xarita faqat shu bino uchun yuklanadi)
const current = ref(0)
const active = computed(() => campuses.value[current.value] ?? campuses.value[0])
const tel = (phone: string) => `tel:${phone.replace(/[^\d+]/g, '')}`
</script>

<template>
  <section v-if="campuses.length" class="relative overflow-hidden py-16 lg:py-24" :aria-label="t('homeContact.title')">
    <!-- Fon: xalqaro aloqa tasviri (sekin harakatda) va yumshoq rangli nurlar (yalpiz va lavanda) -->
    <div class="decor pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <img src="/images/bg/world.webp" alt="" width="1280" height="720" loading="lazy" decoding="async" class="bg-kb absolute -inset-10 size-[calc(100%+5rem)] max-w-none object-cover opacity-70">
      <span class="absolute inset-0 bg-[linear-gradient(180deg,rgb(250_248_244/0.8),rgb(250_248_244/0.3)_35%,rgb(250_248_244/0.3)_80%,rgb(250_248_244/0.6))]" />
      <span class="absolute -top-24 -left-32 size-[520px] rounded-full bg-accent-100 opacity-80 blur-3xl" />
      <span class="absolute -right-24 -bottom-32 size-[560px] rounded-full bg-brand-100 opacity-80 blur-3xl" />
    </div>

    <div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <SectionHeading
        :eyebrow="t('homeContact.eyebrow')"
        :title="t('homeContact.title')"
        :link="{ to: localePath('/aloqa'), label: t('homeContact.all') }"
      />

      <div class="mt-10 grid gap-5 lg:grid-cols-12 lg:gap-6">
        <!-- Chap: binoni tanlash + tanlangan bino ma'lumoti -->
        <div class="flex flex-col gap-4 lg:col-span-5">
          <p class="text-xs font-semibold tracking-[0.18em] text-muted uppercase">{{ t('homeContact.choose') }}</p>
          <ul class="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-1">
            <li v-for="(c, i) in campuses" :key="c.id" data-reveal-item>
              <button
                type="button"
                data-spot
                :aria-pressed="i === current"
                class="group flex w-full items-center gap-4 rounded-[22px] border p-3 pr-4 text-left transition duration-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 motion-reduce:transition-none"
                :class="i === current
                  ? 'border-brand-900 bg-brand-900 text-white shadow-[0_22px_40px_-22px_rgb(17_12_46/0.7)]'
                  : 'border-white bg-white/85 text-ink shadow-[0_1px_0_rgba(19,17,47,0.04)] backdrop-blur hover:border-brand-200 hover:shadow-[0_18px_36px_-24px_rgb(17_12_46/0.45)]'"
                @click="current = i"
              >
                <span
                  class="grid size-14 shrink-0 place-items-center overflow-hidden rounded-full bg-white ring-[3px] transition-transform duration-300 group-hover:scale-105"
                  :class="i === current ? 'ring-accent-400' : 'ring-brand-100'"
                  aria-hidden="true"
                >
                  <img
                    :src="logoFor(c.id)"
                    alt=""
                    width="56"
                    height="56"
                    loading="lazy"
                    :class="logoFor(c.id) === '/logos/uzswlu.png' ? 'size-[78%] object-contain' : 'size-full object-cover'"
                  >
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block font-display text-lg leading-tight font-semibold">{{ c.name }}</span>
                  <span class="mt-1 line-clamp-2 block text-[13px] leading-snug" :class="i === current ? 'text-white/70' : 'text-muted'">{{ c.address }}</span>
                </span>
                <Icon
                  :name="i === current ? 'lucide:map-pin' : 'lucide:chevron-right'"
                  class="size-5 shrink-0 transition-transform duration-300 group-hover:translate-x-0.5"
                  :class="i === current ? 'text-accent-400' : 'text-brand-300'"
                />
              </button>
            </li>
          </ul>

          <!-- Tanlangan bino: manzil, telefon, e-pochta (bosiladi) -->
          <div v-if="active" class="rounded-[28px] border border-white bg-white/90 p-3 shadow-[0_24px_50px_-34px_rgb(17_12_46/0.55)] backdrop-blur">
            <ul class="flex flex-col text-sm">
              <li>
                <a :href="active.mapUrl" target="_blank" rel="noopener" class="flex items-start gap-3 rounded-2xl px-3 py-2.5 transition-colors hover:bg-brand-50">
                  <span class="grid size-9 shrink-0 place-items-center rounded-xl bg-[#FFF1D6] text-base text-[#9A5B00]"><Icon name="lucide:map-pin" /></span>
                  <span class="min-w-0"><span class="block text-[11px] font-semibold tracking-wider text-muted uppercase">{{ t('homeContact.address') }}</span><span class="font-medium text-ink">{{ active.address }}</span></span>
                </a>
              </li>
              <li v-if="active.phone">
                <a :href="tel(active.phone)" class="flex items-start gap-3 rounded-2xl px-3 py-2.5 transition-colors hover:bg-brand-50">
                  <span class="grid size-9 shrink-0 place-items-center rounded-xl bg-accent-100 text-base text-accent-600"><Icon name="lucide:phone" /></span>
                  <span class="min-w-0"><span class="block text-[11px] font-semibold tracking-wider text-muted uppercase">{{ t('homeContact.phone') }}</span><span class="font-medium text-ink">{{ active.phone }}</span></span>
                </a>
              </li>
              <li v-if="active.email">
                <a :href="`mailto:${active.email}`" class="flex items-start gap-3 rounded-2xl px-3 py-2.5 transition-colors hover:bg-brand-50">
                  <span class="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-100 text-base text-brand-700"><Icon name="lucide:mail" /></span>
                  <span class="min-w-0"><span class="block text-[11px] font-semibold tracking-wider text-muted uppercase">{{ t('homeContact.email') }}</span><span class="block truncate font-medium text-ink">{{ active.email }}</span></span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        <!-- O'ng: tanlangan binoning Yandex xaritasi (katta) -->
        <div v-if="active" class="relative min-h-[360px] overflow-hidden rounded-[32px] border-4 border-white bg-brand-50 shadow-[0_34px_70px_-40px_rgb(17_12_46/0.6)] lg:col-span-7 lg:min-h-[560px]">
          <MapFrame v-if="active.mapEmbed" :key="active.id" :src="active.mapEmbed" :title="`${active.name} — ${t('homeContact.map')}`" />
          <!-- Yandex iframe'ning o'z «Открыть в Яндекс Картах» havolasi bor — ustma-ust tushmasligi uchun bizning tugma faqat xarita yo'q bo'lganda -->
          <a
            v-if="!active.mapEmbed"
            :href="active.mapUrl"
            target="_blank"
            rel="noopener"
            class="absolute bottom-4 left-4 inline-flex items-center gap-2 rounded-full bg-brand-900 px-4 py-2.5 text-sm font-semibold text-white shadow-[0_14px_30px_-14px_rgb(17_12_46/0.8)] transition hover:bg-brand-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-400"
          >
            <Icon name="lucide:navigation" class="size-4 text-accent-400" />
            {{ t('homeContact.openMap') }}
            <Icon name="lucide:arrow-up-right" class="size-4" />
          </a>
        </div>
      </div>
    </div>
  </section>
</template>
