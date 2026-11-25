<script setup lang="ts">
import type { MenuGroup } from '#shared/types/api'

const props = defineProps<{ group: MenuGroup }>()

const { t } = useI18n()
const localePath = useLocalePath()

const isSdg = computed(() => props.group.links.some(l => l.sdg))
const columns = computed(() => {
  const n = props.group.links.length
  return n > 10 ? 'grid-cols-3' : n > 4 ? 'grid-cols-2' : 'grid-cols-1 max-w-md'
})
const num = (i: number) => String(i + 1).padStart(2, '0')
</script>

<template>
  <div class="mx-auto grid max-w-7xl grid-cols-12 gap-10 px-8 py-10">
    <div class="col-span-3 flex flex-col">
      <!-- Umumiy sahifasi bor bo'lim (BRM → /brm): belgi va nom shu sahifaga olib boradi -->
      <NuxtLink v-if="group.overview" :to="localePath(group.overview)" class="group/ov self-start" :title="t('nav.overview')">
        <span class="grid place-items-center rounded-2xl transition-colors" :class="group.id === 'sdg' ? 'size-16' : 'size-12', group.id === 'sdg' ? 'bg-white shadow-[0_8px_20px_-12px_rgb(19_17_47/0.5)] ring-1 ring-line' : 'bg-brand-800 text-accent-400 group-hover/ov:bg-brand-700'">
          <NavGroupIcon :id="group.id" :label="group.id === 'sdg' ? '17' : undefined" :class="group.id === 'sdg' ? 'size-[3.25rem]' : 'size-6'" />
        </span>
        <span class="mt-5 flex items-center gap-2.5 font-display text-3xl font-semibold text-ink transition-colors group-hover/ov:text-brand-700">
          {{ group.title }}
          <Icon name="lucide:arrow-right" class="size-5 text-brand-600 transition-transform group-hover/ov:translate-x-1" />
        </span>
      </NuxtLink>
      <template v-else>
        <span class="grid place-items-center rounded-2xl" :class="group.id === 'sdg' ? 'size-16' : 'size-12', group.id === 'sdg' ? 'bg-white shadow-[0_8px_20px_-12px_rgb(19_17_47/0.5)] ring-1 ring-line' : 'bg-brand-800 text-accent-400'">
          <NavGroupIcon :id="group.id" :label="group.id === 'sdg' ? '17' : undefined" :class="group.id === 'sdg' ? 'size-[3.25rem]' : 'size-6'" />
        </span>
        <p class="mt-5 font-display text-3xl font-semibold text-ink">{{ group.title }}</p>
      </template>
      <p v-if="group.description" class="mt-3 text-sm leading-relaxed text-muted">{{ group.description }}</p>
      <p class="mt-4 text-xs font-semibold tracking-[0.16em] text-brand-600 uppercase">{{ t('nav.pages', { n: group.links.length }) }}</p>
      <NuxtLink
        v-if="group.overview"
        :to="localePath(group.overview)"
        class="group/ovb mt-5 inline-flex h-11 items-center gap-2 self-start rounded-full bg-brand-800 px-[18px] text-sm font-semibold text-white transition-colors hover:bg-brand-700"
      >
        {{ t('nav.overview') }}
        <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover/ovb:translate-x-1" />
      </NuxtLink>

    </div>

    <div class="col-span-9 border-l border-line pl-10">
      <NavSdgGrid v-if="isSdg" :links="group.links" />
      <!-- Ichki sahifalar: har biri — kartoçka (tartib raqami, yumşoq gradient fon); hover'da töq indigo gradient, mint strelka -->
      <ul v-else class="grid gap-2.5" :class="columns">
        <li v-for="(link, i) in group.links" :key="link.url" class="min-w-0">
          <NavMenuLink
            :link="link"
            class="group/link relative isolate flex h-full min-h-[58px] items-center gap-3 overflow-hidden rounded-2xl border px-3 py-2.5 text-[15px] leading-snug transition duration-300 ease-out hover:-translate-y-0.5 hover:border-transparent hover:shadow-[0_18px_36px_-20px_rgb(56_43_133/0.75)] motion-reduce:hover:transform-none"
            :class="link.highlight ? 'border-accent-400/60 bg-[linear-gradient(135deg,#effff9,#f4f2fd)]' : 'border-line/80 bg-[linear-gradient(135deg,#fbfaff,#f3f1fc)]'"
          >
            <span class="absolute inset-0 -z-10 bg-[linear-gradient(135deg,#382b85,#13112f)] opacity-0 transition-opacity duration-300 group-hover/link:opacity-100" aria-hidden="true" />
            <span
              class="grid size-9 shrink-0 place-items-center rounded-xl text-[12px] font-bold tabular-nums ring-1 transition-colors duration-300 group-hover/link:bg-white/10 group-hover/link:text-accent-400 group-hover/link:ring-white/15"
              :class="link.highlight ? 'bg-accent-400 text-brand-950 ring-accent-400' : 'bg-white text-brand-700 ring-line'"
              aria-hidden="true"
            >{{ num(i) }}</span>
            <span class="min-w-0 flex-1 transition-colors duration-300 group-hover/link:text-white" :class="link.highlight ? 'font-semibold text-brand-800' : 'font-medium text-ink/90'">{{ link.title }}</span>
            <span v-if="link.file" class="shrink-0 rounded-md bg-red-50 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-red-700 uppercase">{{ link.file }}</span>
            <Icon v-else name="lucide:arrow-up-right" class="size-4 shrink-0 text-brand-400 transition duration-300 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 group-hover/link:text-accent-400" />
          </NavMenuLink>
        </li>
      </ul>
    </div>
  </div>
</template>
