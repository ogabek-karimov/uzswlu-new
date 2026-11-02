<script setup lang="ts">
import type { Leader, Leadership } from '#shared/types/api'

// Rektorat (canvas: "Rahbariyat — Rektorat")
const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = await useFetch<Leadership>('/api/leadership', { key: 'leadership', query: { lang: locale } })

const tel = (phone: string) => `tel:${phone.replace(/[^\d+]/g, '')}`
const phoneLine = (l: Leader) => [l.phone, l.ext].filter(Boolean).join(' · ')

useSeoMeta({ title: () => t('leaders.title'), description: () => t('leaders.lead') })
</script>

<template>
  <div v-if="data">
    <PageIntro :crumbs="[{ label: t('menu.university.title') }, { label: t('leaders.title') }]" :title="t('leaders.title')" :lead="t('leaders.lead')" />

    <!-- Rektor -->
    <section class="mx-auto max-w-7xl px-4 pt-10 sm:px-6 lg:px-8">
      <article class="relative flex flex-col gap-8 overflow-hidden rounded-[32px] bg-brand-900 p-6 text-white sm:p-10 md:flex-row md:items-center md:gap-10">
        <span class="decor pointer-events-none absolute -top-36 -right-28 size-[460px] rounded-full border-[48px] border-white/[0.04]" aria-hidden="true" />
        <div class="relative h-80 w-full shrink-0 overflow-hidden rounded-3xl bg-white/[0.08] sm:w-[260px]">
          <img v-if="data.rector.photo" :src="data.rector.photo" :alt="data.rector.name" class="size-full object-cover">
          <span v-else class="grid size-full place-items-center font-display text-7xl font-semibold text-white/35" aria-hidden="true">{{ initials(data.rector.name) }}</span>
        </div>
        <div class="relative min-w-0 flex-1">
          <p class="text-xs font-semibold tracking-[0.2em] text-accent-400 uppercase">{{ data.rector.role }}</p>
          <h2 class="mt-3 font-display text-3xl leading-tight font-semibold sm:text-[44px]">{{ data.rector.name }}</h2>
          <p class="mt-3 text-[17px] text-white/70">{{ t('leaders.rectorLine') }}</p>
          <dl class="mt-7 grid gap-4 sm:grid-cols-3">
            <div v-if="data.rector.hours" class="border-t border-white/15 pt-3.5">
              <dt class="text-[13px] text-white/55">{{ t('leaders.hours') }}</dt>
              <dd class="mt-1 font-semibold">{{ data.rector.hours }}</dd>
            </div>
            <div v-if="data.rector.phone" class="border-t border-white/15 pt-3.5">
              <dt class="text-[13px] text-white/55">{{ t('leaders.phone') }}</dt>
              <dd class="mt-1 font-semibold"><a :href="tel(data.rector.phone)" class="hover:text-accent-400">{{ phoneLine(data.rector) }}</a></dd>
            </div>
            <div v-if="data.rector.email" class="border-t border-white/15 pt-3.5">
              <dt class="text-[13px] text-white/55">{{ t('leaders.email') }}</dt>
              <dd class="mt-1 font-semibold break-all"><a :href="`mailto:${data.rector.email}`" class="hover:text-accent-400">{{ data.rector.email }}</a></dd>
            </div>
          </dl>
          <div class="mt-7 flex flex-wrap gap-3">
            <NuxtLink :to="localePath('/aloqa') + '#appeal'" class="inline-flex h-[52px] items-center gap-2 rounded-full bg-accent-400 px-6 font-semibold text-ink transition-colors hover:bg-accent-300">
              {{ t('leaders.write') }}
              <Icon name="lucide:arrow-right" class="size-4" />
            </NuxtLink>
            <NuxtLink :to="localePath('/rektor-tabrigi')" class="inline-flex h-[52px] items-center rounded-full border border-white/25 px-6 font-semibold transition-colors hover:bg-white hover:text-ink">{{ t('leaders.welcome') }}</NuxtLink>
            <NuxtLink v-if="data.rector.staffId" :to="localePath(`/teacher/${data.rector.staffId}`)" class="inline-flex h-[52px] items-center rounded-full px-4 font-semibold text-white/80 transition-colors hover:text-accent-400">{{ t('leaders.profile') }} →</NuxtLink>
          </div>
        </div>
      </article>
    </section>

    <!-- Prorektorlar -->
    <section class="mx-auto max-w-7xl px-4 pt-18 sm:px-6 lg:px-8">
      <h2 class="font-display text-4xl font-semibold sm:text-[40px]">{{ t('leaders.prorectors') }}</h2>
      <ul class="mt-7 grid gap-5 lg:grid-cols-2">
        <li v-for="p in data.prorectors" :key="p.name" class="flex gap-5 rounded-3xl border border-line bg-white p-5 sm:p-6">
          <span class="grid h-28 w-24 shrink-0 place-items-center overflow-hidden rounded-[18px] bg-brand-100 font-display text-3xl font-semibold text-brand-700">
            <img v-if="p.photo" :src="p.photo" :alt="p.name" class="size-full object-cover">
            <span v-else aria-hidden="true">{{ initials(p.name) }}</span>
          </span>
          <div class="flex min-w-0 flex-col gap-1.5">
            <h3 class="text-[19px] leading-snug font-semibold">
              <NuxtLink v-if="p.staffId" :to="localePath(`/teacher/${p.staffId}`)" class="text-ink transition-colors hover:text-brand-700">{{ p.name }}</NuxtLink>
              <template v-else>{{ p.name }}</template>
            </h3>
            <p class="text-sm leading-normal text-muted">{{ p.role }}</p>
            <ul class="mt-2 flex flex-col gap-1.5 border-t border-line/70 pt-3 text-sm">
              <li v-if="p.hours" class="flex items-center gap-2"><Icon name="lucide:clock" class="size-4 shrink-0 text-accent-600" />{{ p.hours }}</li>
              <li v-if="p.phone" class="flex items-center gap-2"><Icon name="lucide:phone" class="size-4 shrink-0 text-accent-600" /><a :href="tel(p.phone)" class="hover:text-brand-700">{{ phoneLine(p) }}</a></li>
              <li v-if="p.email" class="flex items-center gap-2"><Icon name="lucide:mail" class="size-4 shrink-0 text-accent-600" /><a :href="`mailto:${p.email}`" class="break-all hover:text-brand-700">{{ p.email }}</a></li>
            </ul>
            <NuxtLink v-if="p.staffId" :to="localePath(`/teacher/${p.staffId}`)" class="mt-1.5 text-sm font-semibold text-accent-600 hover:text-accent-700">{{ t('leaders.profile') }} →</NuxtLink>
          </div>
        </li>
      </ul>
    </section>

    <!-- Matbuot kotibi + murojaat -->
    <section class="mx-auto grid max-w-7xl gap-5 px-4 pt-18 pb-24 sm:px-6 lg:grid-cols-[1.3fr_1fr] lg:px-8">
      <article v-if="data.press" class="flex flex-col gap-5 rounded-3xl bg-brand-50 p-6 sm:flex-row sm:items-center sm:p-7">
        <span class="grid size-20 shrink-0 place-items-center rounded-full bg-white font-display text-[26px] font-semibold text-brand-700" aria-hidden="true">{{ initials(data.press.name) }}</span>
        <div class="min-w-0">
          <p class="text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">{{ t('leaders.press') }}</p>
          <h3 class="mt-1.5 text-[19px] font-semibold">
            <NuxtLink v-if="data.press.staffId" :to="localePath(`/teacher/${data.press.staffId}`)" class="text-ink hover:text-brand-700">{{ data.press.name }}</NuxtLink>
            <template v-else>{{ data.press.name }}</template>
          </h3>
          <p class="mt-1 text-sm text-muted">
            {{ data.press.role }}
            <template v-if="data.press.phone"> · <a :href="tel(data.press.phone)" class="hover:text-brand-700">{{ data.press.phone }}</a></template>
            <template v-if="data.press.email"> · <a :href="`mailto:${data.press.email}`" class="hover:text-brand-700">{{ data.press.email }}</a></template>
          </p>
        </div>
      </article>
      <NuxtLink :to="localePath('/aloqa') + '#appeal'" class="group flex flex-col justify-between gap-4 rounded-3xl bg-brand-950 p-7 text-white">
        <span class="font-display text-[26px] font-semibold">{{ t('leaders.appeal.title') }}</span>
        <span class="text-[15px] text-white/70">{{ t('leaders.appeal.text') }}</span>
        <span class="inline-flex items-center gap-1.5 font-semibold text-accent-400">
          {{ t('leaders.appeal.cta') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
        </span>
      </NuxtLink>
    </section>
  </div>
</template>
