<script setup lang="ts">
// Sahifalash: havolalar URL'dagi ?page= ni o'zgartiradi (qidiruv tizimlari ham o'qiy oladi)
const props = defineProps<{ page: number; totalPages: number }>()

const { t } = useI18n()
const route = useRoute()

const to = (page: number) => ({ query: { ...route.query, page: page > 1 ? page : undefined } })

/** 1 … 4 5 6 … 20 */
const items = computed(() => {
  const { page, totalPages } = props
  const set = new Set([1, totalPages, page - 1, page, page + 1].filter(n => n >= 1 && n <= totalPages))
  const sorted = [...set].sort((a, b) => a - b)
  const out: (number | 'gap')[] = []
  sorted.forEach((n, i) => {
    if (i && n - sorted[i - 1]! > 1) out.push('gap')
    out.push(n)
  })
  return out
})
</script>

<template>
  <nav v-if="totalPages > 1" :aria-label="t('staff.pages')" class="flex flex-wrap items-center justify-between gap-4">
    <span class="text-sm text-muted">{{ t('staff.pageOf', { page, total: totalPages }) }}</span>
    <ul class="flex flex-wrap items-center gap-1.5 text-[15px] font-semibold">
      <li v-if="page > 1">
        <NuxtLink :to="to(page - 1)" class="flex h-11 items-center gap-1.5 rounded-2xl border border-line bg-white px-4 text-ink transition-colors hover:border-accent-500">
          <Icon name="lucide:arrow-left" class="size-4" />
          {{ t('staff.prev') }}
        </NuxtLink>
      </li>
      <li v-for="(item, i) in items" :key="i">
        <span v-if="item === 'gap'" class="grid size-11 place-items-center text-muted" aria-hidden="true">…</span>
        <span v-else-if="item === page" aria-current="page" class="grid size-11 place-items-center rounded-2xl bg-brand-900 text-white">{{ item }}</span>
        <NuxtLink v-else :to="to(item)" class="grid size-11 place-items-center rounded-2xl border border-line bg-white text-ink transition-colors hover:border-accent-500">{{ item }}</NuxtLink>
      </li>
      <li v-if="page < totalPages">
        <NuxtLink :to="to(page + 1)" class="flex h-11 items-center gap-1.5 rounded-2xl bg-accent-400 px-4 text-ink transition-colors hover:bg-accent-300">
          {{ t('staff.next') }}
          <Icon name="lucide:arrow-right" class="size-4" />
        </NuxtLink>
      </li>
    </ul>
  </nav>
</template>
