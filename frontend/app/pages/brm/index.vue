<script setup lang="ts">
import type { SdgOverview } from '#shared/types/api'

// BRM — barqaror rivojlanish maqsadlari (canvas: "BRM — Barqaror rivojlanish")
const { t, locale } = useI18n()
const localePath = useLocalePath()

const { data } = await useFetch<SdgOverview>('/api/sdg', { key: 'sdg', query: { lang: locale } })

const stripe = `linear-gradient(90deg, ${Array.from({ length: 17 }, (_, i) => `${sdgColor(i + 1)} ${((i / 17) * 100).toFixed(2)}% ${(((i + 1) / 17) * 100).toFixed(2)}%`).join(', ')})`
const isInternal = (url: string) => url.startsWith('/')
const NuxtLink = resolveComponent('NuxtLink')

useSeoMeta({ title: () => t('sdg.eyebrow'), description: () => t('sdg.lead') })
</script>

<template>
  <div v-if="data">
    <!-- Hero: aylana + GreenMetric -->
    <section class="relative overflow-hidden bg-brand-950 text-white">
      <span class="decor pointer-events-none absolute -top-56 -left-44 size-[560px] rounded-full border-[56px] border-accent-400/5" aria-hidden="true" />
      <span class="absolute inset-x-0 bottom-0 h-2.5" :style="{ background: stripe }" aria-hidden="true" />
      <div class="relative mx-auto max-w-7xl px-4 pt-8 pb-22 sm:px-6 lg:px-8">
        <PageBreadcrumbs dark :items="[{ label: t('sdg.crumb') }]" />
        <div class="mt-7 grid items-center gap-14 lg:grid-cols-[1fr_minmax(0,600px)]">
          <div class="min-w-0">
            <p class="text-xs font-semibold tracking-[0.2em] text-accent-400 uppercase">{{ t('sdg.eyebrow') }}</p>
            <h1 class="mt-3.5 font-display text-[2.75rem] leading-[1.04] font-semibold sm:text-[56px]">{{ t('sdg.title') }} <span class="text-accent-400 italic">{{ t('sdg.titleAccent') }}</span></h1>
            <p class="mt-5 max-w-xl text-lg leading-relaxed text-white/72">{{ t('sdg.lead') }}</p>

            <div class="mt-9 max-w-[560px] rounded-3xl border border-white/14 bg-white/[0.06] p-6">
              <p class="text-[13px] font-semibold tracking-[0.14em] text-white/65 uppercase">UI GreenMetric {{ data.greenmetric.year }}</p>
              <dl class="mt-4 grid grid-cols-3 gap-3">
                <div v-for="key in (['world', 'asia', 'country'] as const)" :key="key" class="flex flex-col-reverse gap-1.5">
                  <dt class="text-[13px] text-white/65">
                    {{ t(`sdg.${key}`) }}
                    <span v-if="data.greenmetric[key].change" class="text-accent-400">↑ {{ data.greenmetric[key].change }}</span>
                  </dt>
                  <dd class="font-display text-3xl leading-none font-semibold sm:text-[44px]">{{ data.greenmetric[key].rank }}</dd>
                </div>
              </dl>
              <NuxtLink v-if="data.greenmetric.highlight" :to="localePath(data.greenmetric.highlight.url)" class="mt-[18px] flex items-center justify-between gap-3 rounded-[14px] bg-accent-400 px-4 py-3 font-bold text-ink transition-colors hover:bg-accent-300">
                {{ data.greenmetric.highlight.text }}
                <Icon name="lucide:arrow-right" class="size-4 shrink-0" />
              </NuxtLink>
            </div>
          </div>

          <SdgWheel :goals="data.goals" :impact-year="data.impactYear" />
        </div>
      </div>
    </section>

    <!-- GreenMetric yo'nalishlari -->
    <section class="mx-auto max-w-7xl px-4 pt-20 sm:px-6 lg:px-8">
      <SectionHeading eyebrow="UI GreenMetric" :title="t('sdg.categoriesTitle')" />
      <ul class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <li v-for="c in data.categories" :key="c.code">
          <NuxtLink
            :to="localePath(c.url)"
            class="flex h-full items-center gap-4 rounded-[22px] border p-[22px] transition hover:-translate-y-0.5"
            :class="c.badge ? 'border-brand-950 bg-brand-950 text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
          >
            <span class="grid size-14 shrink-0 place-items-center rounded-2xl text-[15px] font-extrabold tracking-[0.04em]" :class="c.badge ? 'bg-accent-400 text-ink' : 'bg-accent-100 text-accent-700'">{{ c.code }}</span>
            <span class="min-w-0 flex-1">
              <span class="block text-lg font-bold">{{ c.title }}</span>
              <span class="mt-0.5 block text-[13px] opacity-70">{{ c.subtitle }}</span>
            </span>
            <span class="shrink-0 text-[13px] font-bold">{{ c.badge ?? '→' }}</span>
          </NuxtLink>
        </li>
      </ul>
    </section>

    <!-- 17 maqsad -->
    <section class="mx-auto max-w-7xl px-4 pt-20 sm:px-6 lg:px-8">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <SectionHeading :eyebrow="`THE Impact Rankings ${data.impactYear}`" :title="t('sdg.goalsTitle')" />
        <p class="max-w-md text-[15px] leading-relaxed text-muted">{{ t('sdg.goalsText') }}</p>
      </div>
      <ul data-a11y-keep class="mt-8 grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        <li v-for="g in data.goals" :key="g.n">
          <NuxtLink :to="localePath(g.url)" class="group flex h-full flex-col overflow-hidden rounded-[22px] border border-line bg-white text-ink transition hover:-translate-y-0.5 hover:shadow-[0_18px_40px_-24px_rgba(19,17,47,0.5)]">
            <span class="flex min-h-[104px] items-start justify-between gap-3 px-5 py-[18px]" :style="{ background: sdgColor(g.n), color: sdgInk(g.n) }">
              <span class="font-display text-5xl leading-none font-semibold">{{ g.n }}</span>
              <span class="max-w-[70%] text-right text-[15px] leading-snug font-bold">{{ g.title }}</span>
            </span>
            <span class="flex items-center justify-between gap-3 px-5 py-3.5 text-sm">
              <span><span class="block text-xs text-muted">{{ t('sdg.rank') }}</span><span class="font-bold">{{ g.rank ?? t('sdg.notRanked') }}</span></span>
              <span class="text-right"><span class="block text-xs text-muted">{{ t('sdg.score') }}</span><span class="font-bold">{{ g.score ?? '—' }}</span></span>
            </span>
          </NuxtLink>
        </li>
      </ul>
    </section>

    <!-- Hisobotlar + Ta'lim va barqarorlik -->
    <section class="mx-auto grid max-w-7xl gap-6 px-4 pt-20 sm:px-6 lg:grid-cols-[1fr_1.2fr] lg:px-8">
      <div class="rounded-[28px] border border-line bg-white p-7 sm:p-8">
        <h2 class="font-display text-[32px] font-semibold">{{ t('sdg.reports') }}</h2>
        <ul class="mt-5">
          <li v-for="r in data.reports" :key="r.title" class="border-t border-line/70">
            <component :is="isInternal(r.url) ? NuxtLink : 'a'" v-bind="isInternal(r.url) ? { to: localePath(r.url) } : { href: r.url, target: '_blank', rel: 'noopener' }" class="flex items-center gap-3.5 px-1 py-3.5 text-ink transition-colors hover:text-brand-700">
              <span class="grid h-[46px] w-10 shrink-0 place-items-center rounded-lg text-[10px] font-extrabold" :class="r.kind === 'pdf' ? 'bg-red-50 text-red-700' : 'bg-accent-100 text-accent-700'">{{ r.kind === 'pdf' ? 'PDF' : t('sdg.page') }}</span>
              <span class="flex-1 font-semibold">{{ r.title }}</span>
              <Icon name="lucide:arrow-right" class="size-4 text-muted" />
            </component>
          </li>
        </ul>
      </div>
      <NuxtLink :to="localePath(data.education.url)" class="group rounded-[28px] bg-brand-900 p-7 text-white sm:p-8">
        <p class="text-xs font-semibold tracking-[0.2em] text-accent-400 uppercase">{{ t('sdg.education') }}</p>
        <h2 class="mt-3 font-display text-[32px] leading-tight font-semibold">{{ data.education.title }}</h2>
        <p class="mt-3.5 leading-relaxed text-white/75">{{ data.education.text }}</p>
        <div class="mt-5 flex flex-wrap gap-2 text-[13px] font-semibold">
          <span v-for="(tag, i) in data.education.tags" :key="tag" class="rounded-full px-3 py-2" :class="i === 0 ? 'bg-accent-400/15 text-accent-400' : 'bg-white/[0.08]'">{{ tag }}</span>
        </div>
      </NuxtLink>
    </section>

    <!-- Yashil universitet -->
    <section class="mx-auto max-w-7xl px-4 pt-20 pb-24 sm:px-6 lg:px-8">
      <SectionHeading :eyebrow="t('sdg.crumb')" :title="t('sdg.green')" :link="{ to: localePath('/yashil-universitet'), label: t('sdg.allNews') }" />
      <ul class="mt-7 grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
        <li v-for="(item, i) in data.news" :key="item.id"><PostCard :item="item" :tone="i + 1" /></li>
      </ul>
    </section>
  </div>
</template>
