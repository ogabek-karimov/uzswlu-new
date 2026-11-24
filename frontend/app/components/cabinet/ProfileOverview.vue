<script setup lang="ts">
import type { CabinetAdminLink, StaffCabinet } from '#shared/types/api'

// Kabinet → «Profil ma'lumotlari» boshidagi karta: profil to'liqligi (Staff sahifasida nima chiqadi), admin paneldagi rol va ruxsatlar,
// pastdagi kartalarga tez o'tish. Ma'lumot o'zgarmaydi — faqat ko'rsatadi
const props = defineProps<{ cabinet: StaffCabinet; admin: CabinetAdminLink }>()
const { t } = useI18n()
const localePath = useLocalePath()

const p = computed(() => props.cabinet.profile)
const steps = computed(() => [
  { key: 'photo', ok: props.cabinet.hasOwnPhoto || !!p.value.photo, to: null },
  { key: 'about', ok: Object.values(props.cabinet.about ?? {}).some(v => !!v?.trim()), to: '#about' },
  { key: 'contacts', ok: p.value.contacts.length > 0, to: '#contacts' },
  { key: 'socials', ok: p.value.socials.length > 0, to: '#socials' },
  { key: 'science', ok: p.value.science.length > 0, to: '#science' },
  { key: 'docs', ok: Object.values(props.cabinet.documents ?? {}).some(d => d.count > 0), to: null },
])
const percent = computed(() => Math.round(steps.value.filter(s => s.ok).length / steps.value.length * 100))
const ring = computed(() => `conic-gradient(var(--color-accent-400) ${percent.value * 3.6}deg, rgba(255,255,255,0.14) 0)`)
const writable = computed(() => props.admin.sections.filter(s => s.level === 'write').length)
</script>

<template>
  <section class="overflow-hidden rounded-3xl border border-line bg-white">
    <div class="relative flex flex-wrap items-center gap-6 bg-[linear-gradient(135deg,var(--color-brand-900),var(--color-brand-700))] px-6 py-6 text-white sm:px-7">
      <span aria-hidden="true" class="absolute -top-28 -right-16 size-[280px] rounded-full border-[36px] border-white/6" />
      <div class="relative grid size-[92px] shrink-0 place-items-center rounded-full" :style="{ background: ring }" role="img" :aria-label="t('cabinet.overviewProfile.complete', { n: percent })">
        <span class="grid size-[76px] place-items-center rounded-full bg-brand-900 text-xl font-bold">{{ percent }}%</span>
      </div>
      <div class="relative min-w-0 flex-[1_1_240px]">
        <h2 class="text-xl font-bold">{{ t('cabinet.overviewProfile.title') }}</h2>
        <p class="mt-1.5 text-sm leading-relaxed text-white/75">{{ percent === 100 ? t('cabinet.overviewProfile.done') : t('cabinet.overviewProfile.text') }}</p>
        <NuxtLink :to="localePath(`/teacher/${p.id}`)" class="mt-3 inline-flex items-center gap-1.5 text-sm font-bold text-accent-400 hover:underline">
          {{ t('cabinet.overviewProfile.viewPage') }}<Icon name="lucide:arrow-up-right" class="size-4" />
        </NuxtLink>
      </div>
    </div>

    <ul class="grid gap-2 p-5 sm:grid-cols-2 sm:p-6 xl:grid-cols-3">
      <li v-for="s in steps" :key="s.key">
        <component
          :is="s.to ? 'a' : 'div'" :href="s.to ?? undefined"
          class="flex items-center gap-3 rounded-2xl border px-3.5 py-3 text-sm transition-colors"
          :class="[s.ok ? 'border-[#bfebdd] bg-[#effcf7]' : 'border-line bg-paper', s.to ? 'hover:border-brand-700' : '']"
        >
          <span class="grid size-7 shrink-0 place-items-center rounded-full" :class="s.ok ? 'bg-accent-400 text-ink' : 'bg-white text-muted ring-1 ring-line'">
            <Icon :name="s.ok ? 'lucide:check' : 'lucide:plus'" class="size-4" />
          </span>
          <span class="font-medium text-ink">{{ t(`cabinet.overviewProfile.steps.${s.key}`) }}</span>
        </component>
      </li>
    </ul>

    <div v-if="admin.role" class="border-t border-line px-5 py-5 sm:px-6">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-sm text-muted">{{ t('cabinet.overviewProfile.role') }}: <b class="text-ink">{{ admin.role }}</b></p>
        <span class="text-xs text-muted">{{ t('cabinet.overviewProfile.sections', { n: admin.sections.length, w: writable }) }}</span>
      </div>
      <ul class="mt-3 flex flex-wrap gap-2">
        <li v-for="s in admin.sections" :key="s.key" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold" :class="s.level === 'write' ? 'bg-brand-50 text-brand-700' : 'bg-paper text-muted'">
          <Icon :name="s.level === 'write' ? 'lucide:pencil' : 'lucide:eye'" class="size-3.5" />{{ s.label }}
        </li>
      </ul>
    </div>
  </section>
</template>
