<script setup lang="ts">
import type { CabinetAdminLink, StaffCabinet } from '#shared/types/api'

// Kabinet bosh sahifasi: rolga mos panel. Kabinetga faqat admin panelda roli bor xodim kiradi (superadmin «Rollar»da beradi);
// HEMIS lavozimi (dekan, mudir, o'qituvchi) bu yerda ishlatilmaydi. Rol bo'lsa: raqamlar (postlar, hujjatlar);
// rolsiz xodim faqat ko'radi — salomlashish va «rol berilmagan» izohi. Bo'limlar, KPI va admin panel — chapdagi menyuda
const props = defineProps<{ cabinet: StaffCabinet; admin: CabinetAdminLink; hasRole: boolean }>()
const { t } = useI18n()

const name = computed(() => props.cabinet.profile.name)
const docs = computed(() => Object.values(props.cabinet.documents ?? {}).reduce((n, d) => n + d.count, 0))

const cards = computed(() => [
  { key: 'published', icon: 'lucide:newspaper', value: props.admin.stats?.published ?? 0, tone: 'bg-brand-50 text-brand-700' },
  { key: 'month', icon: 'lucide:calendar-check', value: props.admin.stats?.month ?? 0, tone: 'bg-accent-100 text-accent-700' },
  { key: 'drafts', icon: 'lucide:file-pen-line', value: props.admin.stats?.drafts ?? 0, tone: 'bg-[#fff6db] text-[#8a5a00]' },
  { key: 'docs', icon: 'lucide:folder-open', value: docs.value, tone: 'bg-[#eef0f6] text-[#3d4466]' },
])

</script>

<template>
  <section class="overflow-hidden rounded-3xl border border-line bg-white">
    <div class="relative bg-[linear-gradient(135deg,var(--color-brand-900),var(--color-brand-700))] px-6 py-6 text-white sm:px-7">
      <span aria-hidden="true" class="absolute -top-28 -right-16 size-[280px] rounded-full border-[36px] border-white/6" />
      <p class="relative text-sm text-white/70">{{ t('cabinet.home.welcome') }}</p>
      <h2 class="relative mt-1 text-2xl font-bold [overflow-wrap:anywhere]">{{ name }}</h2>
      <div class="relative mt-3 flex flex-wrap items-center gap-2">
        <span v-if="hasRole" class="inline-flex items-center gap-1.5 rounded-full bg-accent-400 px-3 py-1 text-xs font-bold text-ink"><Icon name="lucide:shield-check" class="size-3.5" />{{ admin.role }}</span>
        <span v-else class="rounded-full bg-white/12 px-3 py-1 text-xs font-semibold">{{ t('cabinet.home.noRole') }}</span>
        <span v-if="hasRole" class="text-xs text-white/70">{{ t('cabinet.home.sections', { n: admin.sections.length }) }}</span>
      </div>
    </div>

    <div v-if="hasRole" class="grid gap-3 p-5 sm:grid-cols-2 sm:p-6 xl:grid-cols-4">
      <div v-for="c in cards" :key="c.key" class="rounded-2xl border border-line p-4">
        <span class="grid size-10 place-items-center rounded-xl" :class="c.tone"><Icon :name="c.icon" class="size-5" /></span>
        <p class="mt-3 text-3xl leading-none font-bold text-ink tabular-nums">{{ c.value }}</p>
        <p class="mt-1.5 text-sm text-muted">{{ t(`cabinet.home.cards.${c.key}`) }}</p>
      </div>
    </div>

    <p v-if="!hasRole" class="border-t border-line px-5 py-4 text-sm leading-relaxed text-muted sm:px-6">{{ t('cabinet.home.noRoleHint') }}</p>
  </section>
</template>
