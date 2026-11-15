<script setup lang="ts">
// «Oldingi / Keyingi» — sayt menyusidagi shu bo'lim (guruh) sahifalari orasida. Sahifa menyuda bo'lmasa, hech narsa chiqmaydi,
// shuning uchun uni istalgan sahifa oxiriga xavfsiz qo'yish mumkin. Faqat ichki havolalar hisoblanadi.
const { t } = useI18n()
const route = useRoute()
const localePath = useLocalePath()
const { data: site } = await useSiteData()

const path = computed(() => {
  const p = route.path.replace(/^\/(ru|en|zh)(?=\/|$)/, '').replace(/\/+$/, '')
  return p || '/'
})
const group = computed(() => site.value?.menu.find(g => g.links.some(l => l.url === path.value)))
const internal = computed(() => (group.value?.links ?? []).filter(l => !isExternal(l)))
const index = computed(() => internal.value.findIndex(l => l.url === path.value))
const prev = computed(() => (index.value > 0 ? internal.value[index.value - 1] : undefined))
const next = computed(() => (index.value >= 0 ? internal.value[index.value + 1] : undefined))
</script>

<template>
  <nav v-if="group && (prev || next)" :aria-label="t('page.sectionNav')" class="no-print mx-auto max-w-7xl px-4 pt-4 pb-16 sm:px-6 lg:px-8">
    <p class="mb-3 text-xs font-semibold tracking-[0.18em] text-muted uppercase">{{ group.title }}</p>
    <div class="grid gap-4 sm:grid-cols-2">
      <NuxtLink
        v-if="prev"
        :to="localePath(prev.url)"
        class="group flex items-center gap-4 rounded-[22px] border border-line bg-white p-5 text-ink transition-colors duration-200 hover:border-accent-500 hover:bg-brand-50"
      >
        <span class="grid size-11 shrink-0 place-items-center rounded-full border border-brand-200 text-brand-700 transition-colors group-hover:border-accent-400 group-hover:bg-accent-400 group-hover:text-ink">
          <Icon name="lucide:arrow-left" class="size-5" />
        </span>
        <span class="min-w-0">
          <span class="block text-[13px] text-muted">{{ t('page.prev') }}</span>
          <span class="mt-0.5 block truncate text-lg font-semibold">{{ prev.title }}</span>
        </span>
      </NuxtLink>
      <span v-else class="hidden rounded-[22px] border border-dashed border-line p-5 text-sm text-muted sm:block">{{ t('page.first') }}</span>
      <NuxtLink
        v-if="next"
        :to="localePath(next.url)"
        class="group flex items-center justify-end gap-4 rounded-[22px] border border-line bg-white p-5 text-right text-ink transition-colors duration-200 hover:border-accent-500 hover:bg-brand-50"
      >
        <span class="min-w-0">
          <span class="block text-[13px] text-muted">{{ t('page.next') }}</span>
          <span class="mt-0.5 block truncate text-lg font-semibold">{{ next.title }}</span>
        </span>
        <span class="grid size-11 shrink-0 place-items-center rounded-full border border-brand-200 text-brand-700 transition-colors group-hover:border-accent-400 group-hover:bg-accent-400 group-hover:text-ink">
          <Icon name="lucide:arrow-right" class="size-5" />
        </span>
      </NuxtLink>
      <span v-else class="hidden rounded-[22px] border border-dashed border-line p-5 text-right text-sm text-muted sm:block">{{ t('page.last') }}</span>
    </div>
  </nav>
</template>
