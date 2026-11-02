<script setup lang="ts">
import type { FacultyDetail } from '#shared/types/api'

// Fakultet sahifasi (canvas: "Fakultet sahifasi")
const { t, locale } = useI18n()
const route = useRoute()
const localePath = useLocalePath()

const slug = computed(() => String(route.params.slug ?? ''))
const { data: faculty, error } = await useFetch<FacultyDetail>(() => `/api/faculties/${slug.value}`, { query: { lang: locale } })
if (error.value || !faculty.value) {
  throw createError({ statusCode: error.value?.statusCode ?? 404, statusMessage: 'Faculty not found', fatal: true })
}

const sections = ['about', 'programs', 'departments', 'deanery', 'news'] as const
const active = ref<(typeof sections)[number]>('about')

// Bo'lim ko'rinishga kelganda tab ham almashadi
let observer: IntersectionObserver | undefined
onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    const visible = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
    if (visible) active.value = visible.target.id as (typeof sections)[number]
  }, { rootMargin: '-40% 0px -55% 0px' })
  for (const id of sections) {
    const el = document.getElementById(id)
    if (el) observer.observe(el)
  }
})
onBeforeUnmount(() => observer?.disconnect())

const tel = (phone: string) => `tel:${phone.replace(/[^\d+]/g, '')}`

useSeoMeta({ title: () => faculty.value?.name ?? '', description: () => faculty.value?.about })
</script>

<template>
  <div v-if="faculty">
    <section class="mx-auto max-w-7xl px-4 pt-7 sm:px-6 lg:px-8">
      <PageBreadcrumbs :items="[{ label: t('facultyList.title'), to: '/fakultetlar-va-kafedralar' }, { label: faculty.name }]" />
      <div id="about" class="mt-7 grid scroll-mt-40 gap-8 lg:grid-cols-[2fr_1fr]">
        <div class="relative overflow-hidden rounded-[32px] bg-brand-900 p-6 text-white sm:p-12">
          <span class="decor pointer-events-none absolute -right-24 -bottom-40 size-[420px] rounded-full border-[44px] border-white/5" aria-hidden="true" />
          <div class="relative flex flex-wrap items-center gap-6">
            <img v-if="faculty.logo" :src="faculty.logo" :alt="t('faculty.logo', { name: faculty.name })" class="size-24 rounded-full bg-white object-cover shadow-[0_0_0_4px_rgba(255,255,255,0.15)] sm:size-28">
            <div class="min-w-0 flex-1">
              <p class="text-xs font-semibold tracking-[0.2em] text-accent-400 uppercase">{{ t('faculty.label') }} · {{ String(faculty.number).padStart(2, '0') }}</p>
              <h1 class="mt-2.5 font-display text-4xl leading-[1.05] font-semibold sm:text-[52px]">{{ faculty.name }}</h1>
            </div>
          </div>
          <p class="relative mt-7 max-w-2xl text-lg leading-relaxed text-white/72">{{ faculty.about }}</p>
          <dl class="relative mt-9 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div v-for="key in (['students', 'departments', 'programs', 'teachers'] as const)" :key="key" class="flex flex-col-reverse gap-1 border-t border-white/15 pt-4">
              <dt class="text-[13px] text-white/60">{{ t(`faculty.stats.${key}`) }}</dt>
              <dd class="font-display text-[34px] font-semibold text-white/85">{{ faculty.stats[key].toLocaleString('ru-RU') }}</dd>
            </div>
          </dl>
          <p class="relative mt-4 flex items-center gap-2 text-xs text-white/50"><span class="size-2 rounded-full bg-emerald-400" />{{ t('faculty.source') }}</p>
        </div>

        <aside class="flex flex-col rounded-[32px] border border-line bg-white p-7 sm:p-8">
          <p class="text-xs font-semibold tracking-[0.2em] text-brand-700 uppercase">{{ faculty.dean.role }}</p>
          <div class="mt-5 flex items-center gap-4">
            <span class="grid size-[88px] shrink-0 place-items-center overflow-hidden rounded-full bg-brand-100 text-brand-700">
              <img v-if="faculty.dean.photo" :src="faculty.dean.photo" :alt="faculty.dean.name" class="size-full object-cover">
              <Icon v-else name="lucide:user-round" class="size-9" />
            </span>
            <div class="min-w-0">
              <p class="text-xl font-semibold">
                <NuxtLink v-if="faculty.dean.staffId" :to="localePath(`/teacher/${faculty.dean.staffId}`)" class="hover:text-brand-700">{{ faculty.dean.name }}</NuxtLink>
                <template v-else>{{ faculty.dean.name }}</template>
              </p>
              <p v-if="faculty.dean.degree" class="mt-1 text-sm text-muted">{{ faculty.dean.degree }}</p>
            </div>
          </div>
          <dl class="mt-6 flex flex-col gap-3.5 text-sm">
            <div v-if="faculty.dean.hours"><dt class="text-muted">{{ t('faculty.hours') }}</dt><dd class="mt-0.5 font-medium">{{ faculty.dean.hours }}</dd></div>
            <div v-if="faculty.dean.phone"><dt class="text-muted">{{ t('leaders.phone') }}</dt><dd class="mt-0.5 font-medium"><a :href="tel(faculty.dean.phone)" class="hover:text-brand-700">{{ faculty.dean.phone }}</a></dd></div>
            <div v-if="faculty.dean.email"><dt class="text-muted">{{ t('leaders.email') }}</dt><dd class="mt-0.5 font-medium break-all"><a :href="`mailto:${faculty.dean.email}`" class="hover:text-brand-700">{{ faculty.dean.email }}</a></dd></div>
          </dl>
          <a v-if="faculty.dean.email" :href="`mailto:${faculty.dean.email}`" class="mt-auto flex h-[52px] items-center justify-center rounded-full bg-brand-800 font-semibold text-white transition-colors hover:bg-brand-700 max-lg:mt-6 lg:mt-auto">{{ t('faculty.contactDean') }}</a>
        </aside>
      </div>
    </section>

    <!-- Bo'limlar navigatsiyasi -->
    <nav :aria-label="t('faculty.sections')" class="sticky top-[82px] z-20 mx-auto mt-8 max-w-7xl px-4 sm:px-6 md:top-[138px] lg:px-8">
      <ul class="flex w-fit max-w-full gap-1 overflow-x-auto rounded-full border border-line bg-white/95 p-1.5 text-[15px] font-medium shadow-[0_10px_30px_-20px_rgba(19,17,47,0.4)] backdrop-blur">
        <li v-for="id in sections" :key="id" class="shrink-0">
          <a :href="`#${id}`" :aria-current="active === id ? 'true' : undefined" class="block rounded-full px-[18px] py-2.5 transition-colors" :class="active === id ? 'bg-ink text-white' : 'text-ink hover:bg-brand-50'" @click="active = id">{{ t(`faculty.tabs.${id}`) }}</a>
        </li>
      </ul>
    </nav>

    <!-- Ta'lim yo'nalishlari -->
    <section id="programs" class="mx-auto max-w-7xl scroll-mt-40 px-4 pt-20 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="t('faculty.study')" :title="t('faculty.tabs.programs')" />
      <div class="mt-8 overflow-x-auto rounded-3xl border border-line bg-white">
        <table class="w-full min-w-[720px] border-collapse text-[15px]">
          <thead>
            <tr class="text-left text-[13px] text-muted">
              <th scope="col" class="border-b border-line px-6 py-[18px] font-semibold">{{ t('faculty.table.program') }}</th>
              <th scope="col" class="border-b border-line px-6 py-[18px] font-semibold">{{ t('faculty.table.level') }}</th>
              <th scope="col" class="border-b border-line px-6 py-[18px] font-semibold">{{ t('faculty.table.form') }}</th>
              <th scope="col" class="border-b border-line px-6 py-[18px] font-semibold">{{ t('faculty.table.years') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in faculty.programs" :key="`${p.code}-${p.form}`" class="border-b border-line/60 last:border-0">
              <td class="px-6 py-5"><span class="block font-semibold">{{ p.title }}</span><span class="mt-0.5 block text-[13px] text-muted">{{ p.code }}</span></td>
              <td class="px-6 py-5"><span class="rounded-full bg-brand-50 px-3 py-1 text-[13px] font-medium text-brand-800">{{ t(`faculty.levels.${p.level}`) }}</span></td>
              <td class="px-6 py-5 text-muted">{{ p.form }}</td>
              <td class="px-6 py-5 text-muted">{{ t('programs.years', { n: p.years }) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Kafedralar -->
    <section id="departments" class="mx-auto max-w-7xl scroll-mt-40 px-4 pt-20 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="t('faculty.structure')" :title="t('faculty.tabs.departments')" />
      <ul class="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        <li v-for="(d, i) in faculty.departments" :key="d.id">
          <NuxtLink :to="{ path: localePath('/staff'), query: { q: d.name } }" class="group flex h-full items-start gap-[18px] rounded-[22px] border border-line bg-white p-6 text-ink transition-colors hover:border-accent-500">
            <span class="grid size-12 shrink-0 place-items-center rounded-[14px] bg-brand-50 font-display text-xl font-semibold text-brand-700">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="min-w-0 flex-1">
              <span class="block text-[17px] font-semibold">{{ d.name }}</span>
              <span v-if="d.head" class="mt-1 block text-sm text-muted">{{ t('faculty.head', { name: d.head }) }}</span>
            </span>
            <Icon name="lucide:arrow-right" class="mt-1 size-4 shrink-0 text-muted transition-transform group-hover:translate-x-0.5" />
          </NuxtLink>
        </li>
      </ul>
    </section>

    <!-- Dekanat -->
    <section id="deanery" class="mx-auto max-w-7xl scroll-mt-40 px-4 pt-20 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="t('faculty.leadership')" :title="t('faculty.tabs.deanery')" />
      <ul class="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <li v-for="(s, i) in faculty.deanery" :key="i" class="rounded-3xl border border-line bg-white p-6 text-center">
          <span class="mx-auto grid size-[104px] place-items-center overflow-hidden rounded-full bg-brand-100 text-brand-700">
            <img v-if="s.photo" :src="s.photo" :alt="s.name" class="size-full object-cover">
            <Icon v-else name="lucide:user-round" class="size-10" />
          </span>
          <p class="mt-[18px] text-[17px] font-semibold">{{ s.name }}</p>
          <p class="mt-1 text-sm text-muted">{{ s.role }}</p>
        </li>
      </ul>
    </section>

    <!-- Yangiliklar va aloqa -->
    <section id="news" class="mx-auto grid max-w-7xl scroll-mt-40 gap-8 px-4 pt-20 pb-24 sm:px-6 lg:grid-cols-[2fr_1fr] lg:px-8">
      <div class="min-w-0">
        <h2 class="font-display text-4xl font-semibold">{{ t('faculty.newsTitle') }}</h2>
        <ul class="mt-6 grid gap-6 sm:grid-cols-2">
          <li v-for="(item, i) in faculty.news" :key="item.id"><PostCard :item="item" :tone="i + 1" /></li>
        </ul>
      </div>
      <aside class="rounded-[28px] bg-brand-50 p-8">
        <h2 class="text-xl font-semibold">{{ t('faculty.contact') }}</h2>
        <ul class="mt-5 flex flex-col gap-4 text-[15px]">
          <li class="flex gap-3"><Icon name="lucide:map-pin" class="mt-0.5 size-5 shrink-0 text-brand-700" />{{ faculty.contact.address }}</li>
          <li class="flex gap-3"><Icon name="lucide:phone" class="mt-0.5 size-5 shrink-0 text-brand-700" /><a :href="tel(faculty.contact.phone)" class="hover:text-brand-700">{{ faculty.contact.phone }}</a></li>
          <li v-if="faculty.contact.email" class="flex gap-3"><Icon name="lucide:mail" class="mt-0.5 size-5 shrink-0 text-brand-700" /><a :href="`mailto:${faculty.contact.email}`" class="break-all hover:text-brand-700">{{ faculty.contact.email }}</a></li>
        </ul>
        <a v-if="faculty.contact.mapUrl" :href="faculty.contact.mapUrl" target="_blank" rel="noopener" class="mt-6 flex h-40 flex-col items-center justify-center gap-2 rounded-[18px] bg-brand-100 font-semibold text-brand-700 transition-colors hover:bg-brand-200">
          <Icon name="lucide:map" class="size-7" />
          {{ t('faculty.map') }}
        </a>
      </aside>
    </section>
  </div>
</template>
