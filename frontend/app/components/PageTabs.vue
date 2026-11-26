<script setup lang="ts">
import type { ContentPage, PageShowcase, PageSubpage } from '#shared/types/api'

// Ichki sahifalar — tugmali menyu (admin → Sahifalar → «Ichki sahifalar — tugmali menyu»): tugmalar tepada,
// bosilgan sahifaning matni va hujjatlari pastda ochiladi (sahifadan chiqmasdan). Ichki sahifasi bor bo'lim —
// xuddi shunday ichma-ich (kichikroq tugmalar). Tanlov manzilda saqlanadi: ?tab=study-programme~curriculum (ulashsa bo'ladi).
// trail — yuqori darajalarda tanlangan sahifalar (ichma-ich tablar uchun)
const props = withDefaults(defineProps<{ items: PageSubpage[]; depth?: number; trail?: string[] }>(), { depth: 0, trail: () => [] })
const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

const chain = computed(() => String(route.query.tab ?? '').split('~').filter(Boolean))
const selected = computed(() => {
  const want = chain.value[props.depth]
  return props.items.find(i => i.slug === want)?.slug ?? props.items[0]?.slug ?? ''
})

function pick(slug: string) {
  if (slug === selected.value) return
  router.replace({ query: { ...route.query, tab: [...props.trail, slug].join('~') } })
}

const { data: page, pending } = await useFetch<ContentPage>(() => `/api/pages/${selected.value}`, {
  query: { lang: locale },
})

// Kartali bloklardan faqat ma'lumotlisi (raqamlar, ustunlar, rasmlar) qoladi — ichki sahifa kartalari o'rniga tugmalar bor
const showcase = computed<PageShowcase[]>(() => (page.value?.showcase ?? []).filter(b =>
  b.intro || b.outro || b.stats.length || b.columns.length || b.photos.length))
const hasBody = computed(() => (page.value?.body ?? '').replace(/<!--[^>]*-->|<p>\s*<\/p>|\s/g, '').length > 0)
const empty = computed(() => page.value && !hasBody.value && !page.value.attachments.length && !page.value.subpages?.length)
const top = computed(() => props.depth === 0)
</script>

<template>
  <section :class="top ? 'page-tabs' : 'page-tabs-sub'">
    <div role="tablist" :aria-label="t('page.tabsLabel')" class="flex flex-wrap" :class="top ? 'gap-2.5' : 'gap-2'">
      <button
        v-for="(item, i) in items"
        :id="`tab-${depth}-${item.slug}`"
        :key="item.slug"
        type="button"
        role="tab"
        :aria-selected="item.slug === selected"
        :aria-controls="`tabpanel-${depth}`"
        :class="[top ? 'tab-btn' : 'tab-pill', item.slug === selected && 'is-active']"
        @click="pick(item.slug)"
      >
        <span v-if="top" class="tab-num" aria-hidden="true">{{ String(i + 1).padStart(2, '0') }}</span>
        <Icon v-else-if="item.icon" :name="`lucide:${item.icon}`" class="size-4 shrink-0" />
        <span class="min-w-0">{{ item.title }}</span>
      </button>
    </div>

    <div :id="`tabpanel-${depth}`" role="tabpanel" :aria-labelledby="`tab-${depth}-${selected}`" class="tab-panel" :class="pending && 'is-loading'">
      <template v-if="page">
        <h2 v-if="top" class="mb-5 font-display text-2xl font-semibold text-ink sm:text-[28px]">{{ page.title }}</h2>
        <h3 v-else class="mb-4 text-lg font-semibold text-ink">{{ page.title }}</h3>
        <p v-if="page.lead" class="mb-5 text-muted">{{ page.lead }}</p>
        <PageBodyHtml v-if="hasBody" :html="page.body" :doc-style="page.docStyle" :showcase="showcase" />
        <PageDocs v-if="page.attachments.length" :docs="page.attachments" :class="hasBody && 'mt-8'" />
        <PageTabs v-if="page.subpages?.length" :items="page.subpages" :depth="depth + 1" :trail="[...trail, selected]" :class="(hasBody || page.attachments.length) && 'mt-10'" />
        <p v-if="empty" class="flex items-center gap-2.5 rounded-2xl border border-dashed border-line px-5 py-4 text-sm text-muted">
          <Icon name="lucide:folder-open" class="size-5 shrink-0" />{{ t('page.tabsEmpty') }}
        </p>
      </template>
      <div v-else-if="pending" class="flex flex-col gap-3" aria-hidden="true">
        <span class="h-7 w-2/5 animate-pulse rounded-lg bg-line" />
        <span class="h-16 animate-pulse rounded-2xl bg-line/70" />
      </div>
    </div>
  </section>
</template>
