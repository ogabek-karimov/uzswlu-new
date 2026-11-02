<script setup lang="ts">
import type { DocumentList } from '#shared/types/api'

// Me'yoriy hujjatlar (canvas: "Hujjatlar — Me'yoriy hujjatlar"): toifa tablari + nom bo'yicha qidiruv
const { t, locale } = useI18n()

const { data } = await useFetch<DocumentList>('/api/documents', { key: 'documents', query: { lang: locale } })

const category = ref('all')
const search = ref('')
const fold = (v: string) => v.toLocaleLowerCase().replace(/[‘’ʻʼ`']/g, '\'')

const tabs = computed(() => [
  { id: 'all', title: t('docs.all'), count: data.value?.items.length ?? 0 },
  ...(data.value?.categories ?? []).map(c => ({ ...c, count: data.value!.items.filter(d => d.category === c.id).length })),
])
const categoryTitle = (id: string) => data.value?.categories.find(c => c.id === id)?.title ?? ''
const items = computed(() => {
  const q = fold(search.value.trim())
  return (data.value?.items ?? []).filter(d => (category.value === 'all' || d.category === category.value) && (!q || fold(d.title).includes(q)))
})

useSeoMeta({ title: () => t('docs.title'), description: () => t('docs.lead') })
</script>

<template>
  <div>
    <PageIntro :crumbs="[{ label: t('menu.activity.title') }, { label: t('docs.title') }]" :title="t('docs.title')" :lead="t('docs.lead')">
      <div role="search" class="w-full sm:w-[380px]">
        <label for="doc-search" class="mb-2 block text-[13px] font-semibold text-muted">{{ t('docs.search') }}</label>
        <div class="flex h-[52px] items-center gap-2 rounded-2xl border border-line bg-white px-4 focus-within:border-accent-600">
          <Icon name="lucide:search" class="size-[18px] shrink-0 text-muted" />
          <input id="doc-search" v-model="search" type="search" :placeholder="t('docs.placeholder')" class="h-full min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted">
        </div>
      </div>
    </PageIntro>

    <section class="mx-auto max-w-7xl px-4 pt-9 pb-24 sm:px-6 lg:px-8">
      <div role="group" :aria-label="t('docs.categories')" class="flex flex-wrap gap-2">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          :aria-pressed="category === tab.id"
          class="h-11 rounded-full border px-[18px] text-sm font-semibold transition-colors"
          :class="category === tab.id ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink hover:border-accent-500'"
          @click="category = tab.id"
        >
          {{ tab.title }} <span class="ml-1.5" :class="category === tab.id ? 'text-white/60' : 'text-muted'">{{ tab.count }}</span>
        </button>
      </div>

      <ul v-if="items.length" class="mt-7 flex flex-col gap-3">
        <li v-for="doc in items" :key="doc.id" class="flex flex-wrap items-center gap-4 rounded-[22px] border border-line bg-white px-5 py-5 sm:gap-5 sm:px-6">
          <span
            class="grid h-[58px] w-12 shrink-0 place-items-center rounded-[10px] text-[11px] font-bold"
            :class="doc.kind === 'pdf' ? 'bg-red-50 text-red-700' : 'bg-brand-50 text-brand-700'"
          >
            <template v-if="doc.kind === 'pdf'">PDF</template>
            <Icon v-else name="lucide:link" class="size-5" />
          </span>
          <div class="min-w-0 flex-[1_1_300px]">
            <p class="text-[17px] leading-snug font-semibold">{{ doc.title }}</p>
            <p class="mt-1 text-[13px] text-muted">{{ categoryTitle(doc.category) }} · {{ doc.kind === 'pdf' ? 'PDF' : t('docs.link') }}</p>
          </div>
          <span class="flex gap-2">
            <a :href="doc.url" target="_blank" rel="noopener" class="inline-flex h-11 items-center rounded-full border border-line px-4 text-sm font-semibold text-ink transition-colors hover:border-accent-500">
              {{ doc.kind === 'pdf' ? t('docs.view') : t('docs.open') }}
            </a>
            <a v-if="doc.kind === 'pdf'" :href="doc.url" download :aria-label="`${t('docs.download')}: ${doc.title}`" class="grid size-11 place-items-center rounded-full bg-brand-800 text-white transition-colors hover:bg-brand-700">
              <Icon name="lucide:download" class="size-[18px]" />
            </a>
          </span>
        </li>
      </ul>
      <p v-else class="mt-7 rounded-[22px] border border-dashed border-brand-200 bg-white p-10 text-center text-muted">{{ t('docs.empty') }}</p>

      <p class="mt-5 text-sm text-muted" aria-live="polite">{{ t('docs.shown', { n: items.length }) }}</p>
    </section>
  </div>
</template>
