<script setup lang="ts">
import type { FacultyList } from '#shared/types/api'

// Fakultetlar va kafedralar (canvas: "Fakultetlar va kafedralar")
const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = await useFetch<FacultyList>('/api/faculties', { key: 'faculties', query: { lang: locale } })

useSeoMeta({ title: () => t('facultyList.title'), description: () => t('faculties.text') })
</script>

<template>
  <div>
    <PageIntro :crumbs="[{ label: t('menu.university.title') }, { label: t('facultyList.title') }]" :title="t('facultyList.title')" :lead="t('faculties.text')">
      <dl v-if="data" class="flex gap-8">
        <div class="flex flex-col-reverse">
          <dt class="text-[13px] text-muted">{{ t('facultyList.faculties') }}</dt>
          <dd class="font-display text-5xl font-semibold text-brand-800">{{ data.summary.faculties }}</dd>
        </div>
        <div class="flex flex-col-reverse">
          <dt class="text-[13px] text-muted">{{ t('facultyList.departments') }}</dt>
          <dd class="font-display text-5xl font-semibold text-brand-800">{{ data.summary.departments }}</dd>
        </div>
      </dl>
    </PageIntro>

    <section class="mx-auto max-w-7xl px-4 pt-10 pb-24 sm:px-6 lg:px-8">
      <ul class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        <li v-for="(f, i) in data?.items ?? []" :key="f.id">
          <NuxtLink :to="localePath(`/faculty/${f.slug}`)" class="group flex h-full items-center gap-4 rounded-[26px] sm:gap-5 border border-line bg-white p-5 text-ink transition hover:-translate-y-0.5 hover:border-accent-500 hover:shadow-[0_18px_40px_-24px_rgba(19,17,47,0.45)] sm:p-6">
            <span class="grid size-20 shrink-0 place-items-center rounded-full bg-brand-50 sm:size-[104px]">
              <img v-if="f.logo" :src="f.logo" alt="" class="size-16 rounded-full bg-white object-cover sm:size-[88px] shadow-[0_6px_18px_-8px_rgba(19,17,47,0.4)]">
              <Icon v-else name="lucide:graduation-cap" class="size-9 text-brand-700" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block text-xs font-semibold text-brand-600">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="mt-1 block text-[17px] leading-snug font-semibold [overflow-wrap:anywhere] sm:text-[19px]">{{ f.name }}</span>
              <span class="mt-2 block text-[13px] text-muted">{{ t('facultyList.meta', { departments: f.departments, programs: f.programs }) }}</span>
            </span>
            <span class="grid size-10 shrink-0 place-items-center rounded-full bg-brand-50 text-brand-800 transition-colors group-hover:bg-brand-800 group-hover:text-white" aria-hidden="true">
              <Icon name="lucide:arrow-right" class="size-4" />
            </span>
          </NuxtLink>
        </li>
      </ul>

      <div class="mt-8 grid gap-5 md:grid-cols-2">
        <NuxtLink :to="localePath('/bolimlar')" class="flex items-center justify-between gap-4 rounded-3xl bg-brand-950 p-7 text-white">
          <span>
            <span class="block font-display text-2xl font-semibold">{{ t('facultyList.units.title') }}</span>
            <span class="mt-1 block text-white/65">{{ t('facultyList.units.text') }}</span>
          </span>
          <span class="shrink-0 font-semibold text-accent-400">{{ t('facultyList.view') }} →</span>
        </NuxtLink>
        <NuxtLink :to="localePath('/tuzilma')" class="flex items-center justify-between gap-4 rounded-3xl bg-accent-100 p-7 text-ink">
          <span>
            <span class="block font-display text-2xl font-semibold">{{ t('facultyList.structure.title') }}</span>
            <span class="mt-1 block text-muted">{{ t('facultyList.structure.text') }}</span>
          </span>
          <span class="shrink-0 font-semibold text-accent-700">{{ t('facultyList.view') }} →</span>
        </NuxtLink>
      </div>
    </section>
  </div>
</template>
