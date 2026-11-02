<script setup lang="ts">
import type { MenuGroup } from '#shared/types/api'

const props = defineProps<{ groups: MenuGroup[] }>()

const { t } = useI18n()
const localePath = useLocalePath()

const gridCols = computed(() => ['grid-cols-1', 'grid-cols-2', 'grid-cols-3'][props.groups.length - 1] ?? 'grid-cols-4')
</script>

<!-- "⋯" tugmasi ostidagi panel: navbarga sig'magan bo'limlar ustunma-ustun -->
<template>
  <div class="mx-auto max-w-7xl px-8 py-10">
    <p class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-brand-600 uppercase">
      <span class="h-px w-8 bg-brand-400" />
      {{ t('nav.moreTitle') }}
    </p>

    <div class="mt-6 grid gap-6" :class="gridCols">
      <section v-for="group in groups" :key="group.id" class="flex min-w-0 flex-col rounded-3xl border border-line bg-white p-5">
        <div class="flex items-center gap-3">
          <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
            <Icon :name="groupIcon(group.id)" class="size-5" />
          </span>
          <p class="text-lg font-semibold text-ink">{{ group.title }}</p>
        </div>

        <!-- Bitta sahifali bo'lim -->
        <NuxtLink
          v-if="group.url"
          :to="localePath(group.url)"
          class="group/open mt-4 flex items-center justify-between rounded-2xl bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-800 transition-colors hover:bg-brand-100"
        >
          {{ t('nav.open') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover/open:translate-x-1" />
        </NuxtLink>

        <NuxtLink
          v-if="!group.url && group.overview"
          :to="localePath(group.overview)"
          class="group/ov mt-4 flex items-center justify-between rounded-2xl bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-800 transition-colors hover:bg-brand-100"
        >
          {{ t('nav.overview') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover/ov:translate-x-1" />
        </NuxtLink>

        <NavSdgGrid v-else-if="group.links.some(l => l.sdg)" :links="group.links" compact class="mt-4" />

        <ul v-else class="mt-3 -mx-2 max-h-80 overflow-y-auto">
          <li v-for="link in group.links" :key="link.url">
            <NavMenuLink
              :link="link"
              class="flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm transition-colors hover:bg-brand-50"
              :class="link.highlight ? 'font-semibold text-brand-800' : 'text-ink/85 hover:text-ink'"
            >
              <span class="size-1 shrink-0 rounded-full" :class="link.highlight ? 'bg-accent-500' : 'bg-brand-300'" />
              <span class="flex-1">{{ link.title }}</span>
              <span v-if="link.file" class="rounded bg-red-50 px-1 py-px text-[9px] font-bold text-red-700 uppercase">{{ link.file }}</span>
            </NavMenuLink>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
