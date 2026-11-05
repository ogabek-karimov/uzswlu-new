<script setup lang="ts">
import type { NuxtError } from '#app'

// 404 va boshqa xatolar (canvas: "404 — Sahifa topilmadi"). Sarlavha va footer bilan, oddiy sahifa kabi.
const props = defineProps<{ error: NuxtError }>()

const { t } = useI18n()
const localePath = useLocalePath()

const notFound = computed(() => props.error.statusCode === 404)
const query = ref('')

// "Sahifa topilmadi" — 11 tilda, bezak sifatida
const PHRASES = [
  ['Page not found', 'en'], ['Страница не найдена', 'ru'], ['页面未找到', 'zh'], ['Seite nicht gefunden', 'de'],
  ['Page introuvable', 'fr'], ['Página no encontrada', 'es'], ['ページが見つかりません', 'ja'], ['페이지를 찾을 수 없습니다', 'ko'],
  ['الصفحة غير موجودة', 'ar'], ['Sayfa bulunamadı', 'tr'], ['Pagina non trovata', 'it'],
] as const
const TINTS = ['text-white/[0.07]', 'text-white/[0.11]', 'text-brand-300/[0.16]', 'text-accent-400/[0.12]']

function search() {
  const q = query.value.trim()
  clearError({ redirect: q ? `${localePath('/search')}?q=${encodeURIComponent(q)}` : localePath('/search') })
}
const go = (path: string) => clearError({ redirect: localePath(path) })

useSeoMeta({ title: () => (notFound.value ? t('notFound.title') : t('notFound.errorTitle')), robots: 'noindex' })
</script>

<template>
  <NuxtLayout>
    <section class="relative overflow-hidden bg-brand-950 text-white">
      <div class="decor pointer-events-none absolute inset-0 flex flex-wrap content-center justify-center gap-x-9 gap-y-2.5 px-10 py-6 font-display text-[30px] leading-[1.3] italic" aria-hidden="true">
        <span v-for="([text, lang], i) in PHRASES" :key="lang" :lang="lang" :dir="lang === 'ar' ? 'rtl' : 'ltr'" class="whitespace-nowrap" :class="TINTS[i % TINTS.length]">{{ text }}</span>
      </div>
      <div class="relative mx-auto max-w-[900px] px-4 py-24 text-center sm:px-10">
        <p class="font-display text-[clamp(7rem,22vw,11.25rem)] leading-[0.9] font-bold text-accent-400">{{ error.statusCode || 500 }}</p>
        <h1 class="mt-4 font-display text-4xl font-semibold sm:text-[44px]">{{ notFound ? t('notFound.title') : t('notFound.errorTitle') }}</h1>
        <p class="mx-auto mt-3.5 max-w-xl text-lg leading-relaxed text-white/75">{{ notFound ? t('notFound.text') : t('notFound.errorText') }}</p>
        <form role="search" class="mx-auto mt-8 max-w-[520px]" @submit.prevent="search">
          <label for="nf-q" class="sr-only">{{ t('hero.searchLabel') }}</label>
          <div class="flex h-14 items-center gap-2 rounded-[18px] bg-white pr-1.5 pl-[18px]">
            <Icon name="lucide:search" class="size-5 shrink-0 text-muted" />
            <input id="nf-q" v-model="query" type="search" autocomplete="off" :placeholder="t('notFound.placeholder')" class="h-full min-w-0 flex-1 bg-transparent text-ink outline-none placeholder:text-muted">
            <button type="submit" class="h-11 rounded-xl bg-ink px-[18px] text-sm font-semibold text-white">{{ t('search.submit') }}</button>
          </div>
        </form>
        <div class="mt-[22px] flex flex-wrap justify-center gap-2.5 text-[15px] font-semibold">
          <button type="button" class="rounded-full bg-accent-400 px-5 py-3 text-ink transition-colors hover:bg-accent-300" @click="go('/')">{{ t('nav.home') }}</button>
          <button type="button" class="rounded-full border border-white/25 px-5 py-3 transition-colors hover:bg-white hover:text-ink" @click="go('/yangiliklar')">{{ t('nav.news') }}</button>
          <button type="button" class="rounded-full border border-white/25 px-5 py-3 transition-colors hover:bg-white hover:text-ink" @click="go('/aloqa')">{{ t('nav.contact') }}</button>
        </div>
      </div>
    </section>
  </NuxtLayout>
</template>
