<script setup lang="ts">
import type { StaffCabinet } from '#shared/types/api'

// "Mening profilim" — HEMIS'dan, faqat o'qish. Lavozimlar: har bir ish joyi alohida, chiplar bilan
// (ish shakli, stavka, xodim turi, holat). "Boshqa" turi (kod 10) va ishdan bo'shaganlar (kod 14) ko'rsatilmaydi.
const props = defineProps<{ cabinet: StaffCabinet }>()

const { t, locale } = useI18n()
const formatDate = useFormatDate()

const fields = computed(() => {
  const h = props.cabinet.hemis
  return [
    { key: 'lastName', value: h.lastName },
    { key: 'firstName', value: h.firstName },
    { key: 'patronymic', value: h.patronymic },
    { key: 'birthDate', value: h.birthDate ? formatDate(h.birthDate) : null },
    { key: 'phone', value: h.phone },
    { key: 'email', value: h.email },
  ]
})

const rate = (n: number) => new Intl.NumberFormat(locale.value === 'en' || locale.value === 'zh' ? 'en-US' : 'ru-RU', { minimumFractionDigits: 2 }).format(n)

const jobs = computed(() => props.cabinet.profile.employments
  .filter(e => e.status?.code !== '14')
  .map(e => ({
    key: `${e.department.id}-${e.position.code}`,
    department: e.department.name,
    position: e.position.name,
    chips: [
      e.form?.name,
      e.rate != null ? t('cabinet.hemis.rate', { n: rate(e.rate) }) : null,
      e.type && e.type.code !== '10' ? e.type.name : null,
    ].filter(Boolean) as string[],
    status: e.status?.name,
  })))
</script>

<template>
  <section class="rounded-[28px] border border-line bg-white p-6 transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_24px_50px_-34px_rgba(17,12,46,0.35)] sm:p-7">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="font-display text-[28px] font-semibold text-ink">{{ t('cabinet.hemis.title') }}</h2>
      <span class="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1.5 text-xs font-bold text-brand-700">
        <Icon name="lucide:lock" class="size-3.5" />
        {{ t('cabinet.hemis.badge') }}
      </span>
    </div>

    <dl class="mt-5 grid gap-x-7 gap-y-4 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="f in fields" :key="f.key">
        <dt class="text-sm text-muted">{{ t(`cabinet.hemis.${f.key}`) }}</dt>
        <dd class="mt-1 text-[17px] font-semibold break-words text-ink">{{ f.value || '—' }}</dd>
      </div>
    </dl>

    <p class="mt-7 flex items-center gap-3.5 text-xs font-bold tracking-[0.18em] text-muted uppercase">
      {{ t('cabinet.hemis.jobs') }}
      <span class="h-px flex-1 bg-line" />
    </p>
    <ul class="mt-3.5 grid gap-3">
      <li v-for="job in jobs" :key="job.key" class="flex gap-4 rounded-[18px] border border-line bg-[#fcfbf9] p-4 transition duration-200 hover:-translate-y-0.5 hover:border-accent-500">
        <span class="grid size-12 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-700"><Icon name="lucide:building-2" class="size-[22px]" /></span>
        <span class="min-w-0">
          <span class="block font-bold text-ink">{{ job.department }}</span>
          <span class="mt-0.5 block text-muted">{{ job.position }}</span>
          <span class="mt-2.5 flex flex-wrap gap-1.5">
            <span v-for="c in job.chips" :key="c" class="rounded-full bg-[#f2f0ea] px-2.5 py-1 text-xs font-semibold text-ink">{{ c }}</span>
            <span v-if="job.status" class="rounded-full bg-accent-100 px-2.5 py-1 text-xs font-semibold text-accent-700">{{ job.status }}</span>
          </span>
        </span>
      </li>
    </ul>
  </section>
</template>
