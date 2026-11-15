<script setup lang="ts">
import type { CabinetPanel, CabinetRole } from '#shared/types/api'

// Rolga mos panel: rol HEMIS lavozimidan avtomatik aniqlanadi (backend: apps/api/cabinet_roles.py).
// Dekan — fakultet ko'rsatkichlari va kafedralar; kafedra mudiri — kafedra xodimlari; o'qituvchi/xodim — shaxsiy sahifa.
const props = defineProps<{ role: CabinetRole; panel: CabinetPanel; personId: string }>()

const { t } = useI18n()
const localePath = useLocalePath()

const ICONS: Record<CabinetRole, string> = {
  dean: 'lucide:landmark',
  chair_head: 'lucide:users-round',
  teacher: 'lucide:book-open-check',
  staff: 'lucide:briefcase',
  student: 'lucide:graduation-cap',
}

const stats = computed(() => {
  const s = props.panel.faculty?.stats ?? {}
  return [
    { key: 'students', icon: 'lucide:graduation-cap', value: s.students },
    { key: 'teachers', icon: 'lucide:book-open', value: s.teachers },
    { key: 'departments', icon: 'lucide:library', value: s.departments },
    { key: 'programs', icon: 'lucide:layers', value: s.programs },
  ].filter(x => typeof x.value === 'number')
})
</script>

<template>
  <section class="overflow-hidden rounded-[28px] border border-line bg-white" :aria-label="t('cabinet.rolePanel.title')">
    <!-- Sarlavha: rol, lavozim, bo'lim -->
    <div class="relative overflow-hidden bg-gradient-to-br from-brand-800 via-brand-900 to-brand-950 p-6 text-white sm:p-7">
      <span class="decor pointer-events-none absolute -top-12 -right-10 size-44 rounded-full border-[1.8rem] border-white/[0.06]" aria-hidden="true" />
      <div class="relative flex items-start gap-4">
        <span class="grid size-14 shrink-0 place-items-center rounded-2xl bg-accent-400 text-brand-950">
          <Icon :name="ICONS[role]" class="size-7" />
        </span>
        <div class="min-w-0">
          <p class="text-xs font-semibold tracking-[0.18em] text-accent-300 uppercase">{{ t('cabinet.rolePanel.title') }}</p>
          <h2 class="mt-1 font-display text-2xl font-semibold sm:text-3xl">{{ t(`cabinet.role.${role}`) }}</h2>
          <p v-if="panel.position || panel.department" class="mt-1 text-sm text-white/70">
            {{ panel.position }}<template v-if="panel.position && panel.department"> · </template>{{ panel.department }}
          </p>
          <p class="mt-3 max-w-2xl text-[15px] text-white/80">{{ t(`cabinet.roleDesc.${role}`) }}</p>
        </div>
      </div>
    </div>

    <div class="p-5 sm:p-6">
      <!-- Dekan: fakultet ko'rsatkichlari va kafedralar -->
      <template v-if="role === 'dean' && panel.faculty">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="font-display text-xl font-semibold">{{ panel.faculty.name }}</h3>
          <NuxtLink :to="localePath(`/faculty/${panel.faculty.slug}`)" class="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-900">
            {{ t('cabinet.rolePanel.openFaculty') }}
            <Icon name="lucide:arrow-up-right" class="size-4" />
          </NuxtLink>
        </div>
        <dl class="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <div v-for="s in stats" :key="s.key" class="rounded-2xl bg-brand-50 p-4">
            <dt class="flex items-center gap-2 text-[13px] text-muted">
              <Icon :name="s.icon" class="size-4 text-brand-600" />
              {{ t(`cabinet.rolePanel.${s.key}`) }}
            </dt>
            <dd class="mt-1 font-display text-3xl font-semibold text-ink">{{ s.value }}</dd>
          </div>
        </dl>
        <h3 class="mt-6 text-sm font-semibold tracking-[0.14em] text-muted uppercase">{{ t('cabinet.rolePanel.chairs') }}</h3>
        <ul v-if="panel.faculty.chairs.length" class="mt-3 grid gap-2 sm:grid-cols-2">
          <li v-for="c in panel.faculty.chairs" :key="c.id" class="flex items-center justify-between gap-3 rounded-2xl border border-line px-4 py-3">
            <span class="min-w-0 truncate font-medium text-ink">{{ c.name }}</span>
            <span class="shrink-0 rounded-full bg-accent-100 px-2.5 py-1 text-xs font-semibold text-accent-600">{{ t('cabinet.rolePanel.staffCount', { n: c.staffCount }) }}</span>
          </li>
        </ul>
        <p v-else class="mt-3 text-sm text-muted">{{ t('cabinet.rolePanel.empty') }}</p>
      </template>

      <!-- Kafedra mudiri: kafedra xodimlari -->
      <template v-else-if="role === 'chair_head' && panel.team">
        <h3 class="flex items-center gap-2 text-sm font-semibold tracking-[0.14em] text-muted uppercase">
          {{ t('cabinet.rolePanel.team') }}
          <span class="rounded-full bg-accent-100 px-2.5 py-0.5 text-xs font-semibold tracking-normal text-accent-600 normal-case">{{ panel.team.count }}</span>
        </h3>
        <ul v-if="panel.team.members.length" class="mt-3 grid gap-2 sm:grid-cols-2">
          <li v-for="m in panel.team.members" :key="m.id">
            <NuxtLink :to="localePath(`/teacher/${m.id}`)" class="flex items-center gap-3 rounded-2xl border border-line px-4 py-3 transition-colors hover:border-accent-500 hover:bg-brand-50">
              <span class="grid size-10 shrink-0 place-items-center overflow-hidden rounded-full bg-brand-100 text-brand-700">
                <img v-if="m.photo" :src="m.photo" alt="" width="40" height="40" loading="lazy" class="size-full object-cover">
                <Icon v-else name="lucide:user-round" class="size-5" />
              </span>
              <span class="min-w-0">
                <span class="block truncate font-medium text-ink">{{ m.name }}</span>
                <span class="block truncate text-xs text-muted">{{ m.position }}</span>
              </span>
            </NuxtLink>
          </li>
        </ul>
        <p v-else class="mt-3 text-sm text-muted">{{ t('cabinet.rolePanel.empty') }}</p>
      </template>

      <!-- Talaba: HEMIS talaba kirishi ulanganda -->
      <p v-else-if="role === 'student'" class="rounded-2xl bg-brand-50 p-4 text-sm text-muted">{{ t('cabinet.rolePanel.studentSoon') }}</p>

      <!-- O'qituvchi / xodim: shaxsiy sahifa -->
      <NuxtLink v-else :to="localePath(`/teacher/${personId}`)" class="inline-flex items-center gap-2 rounded-2xl bg-brand-50 px-5 py-3 font-semibold text-brand-800 transition-colors hover:bg-brand-100">
        <Icon name="lucide:user-round" class="size-5" />
        {{ t('cabinet.rolePanel.myPage') }}
        <Icon name="lucide:arrow-up-right" class="size-4" />
      </NuxtLink>
    </div>
  </section>
</template>
