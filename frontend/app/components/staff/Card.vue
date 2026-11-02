<script setup lang="ts">
import type { StaffSummary } from '#shared/types/api'

const props = defineProps<{ person: StaffSummary }>()

const localePath = useLocalePath()
// HEMIS ish joylaridan: avval boshqaruv lavozimi, keyin o'qituvchilik lavozimlari
const roles = computed(() => staffRoles(props.person.employments))
const fullName = computed(() => staffName(props.person.name, props.person.patronymic).full)
</script>

<template>
  <NuxtLink
    :to="localePath(`/teacher/${person.id}`)"
    class="group flex h-full items-center gap-4 rounded-3xl border border-line bg-white p-4 text-ink transition duration-300 hover:-translate-y-0.5 hover:border-accent-500 hover:shadow-[0_20px_44px_-30px_var(--color-accent-600)] sm:p-[18px]"
  >
    <StaffAvatar :id="person.id" :name="fullName" :photo="person.photo" :fallback="person.photoFallback" decorative class="size-[72px] shrink-0 rounded-[20px] text-2xl" />
    <span class="min-w-0 flex-1">
      <span class="block leading-snug font-bold">{{ fullName }}</span>
      <span class="mt-1 block text-[13px] leading-snug text-muted">{{ roles.departments.map(d => d.name).join(', ') }}</span>
      <span
        class="mt-2 inline-block rounded-full px-2.5 py-1 text-xs font-bold"
        :class="person.group === 'lead' ? 'bg-brand-900 text-accent-400' : 'bg-[#f2f0ea] text-ink'"
      >{{ roles.positions.join(', ') }}</span>
    </span>
    <span aria-hidden="true" class="grid size-9 shrink-0 place-items-center rounded-full bg-[#f2f0ea] text-muted transition-colors group-hover:bg-accent-400 group-hover:text-ink">
      <Icon name="lucide:arrow-right" class="size-4" />
    </span>
  </NuxtLink>
</template>
