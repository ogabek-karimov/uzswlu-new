<script setup lang="ts">
import type { MenuGroup } from '#shared/types/api'

const props = defineProps<{ group: MenuGroup }>()

const { t } = useI18n()
const localePath = useLocalePath()

const isSdg = computed(() => props.group.links.some(l => l.sdg))
const featured = computed(() => props.group.links.find(l => l.highlight))
const columns = computed(() => {
  const n = props.group.links.length
  return n > 10 ? 'columns-3' : n > 4 ? 'columns-2' : 'columns-1'
})
</script>

<template>
  <div class="mx-auto grid max-w-7xl grid-cols-12 gap-10 px-8 py-10">
    <div class="col-span-3 flex flex-col">
      <!-- Umumiy sahifasi bor bo'lim (BRM → /brm): belgi va nom shu sahifaga olib boradi -->
      <NuxtLink v-if="group.overview" :to="localePath(group.overview)" class="group/ov self-start" :title="t('nav.overview')">
        <span class="grid size-12 place-items-center rounded-2xl bg-brand-800 text-accent-400 transition-colors group-hover/ov:bg-brand-700">
          <Icon :name="groupIcon(group.id)" class="size-6" />
        </span>
        <span class="mt-5 flex items-center gap-2.5 font-display text-3xl font-semibold text-ink transition-colors group-hover/ov:text-brand-700">
          {{ group.title }}
          <Icon name="lucide:arrow-right" class="size-5 text-brand-600 transition-transform group-hover/ov:translate-x-1" />
        </span>
      </NuxtLink>
      <template v-else>
        <span class="grid size-12 place-items-center rounded-2xl bg-brand-800 text-accent-400">
          <Icon :name="groupIcon(group.id)" class="size-6" />
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

      <!-- Ajratilgan havola (masalan, Qabul 2026/2027) — alohida karta -->
      <NavMenuLink
        v-if="featured"
        :link="featured"
        class="group/feat relative mt-8 overflow-hidden rounded-2xl bg-brand-900 p-5 text-white"
      >
        <span class="decor absolute -right-8 -bottom-10 size-32 rounded-full border-[14px] border-white/5" />
        <span class="relative text-[11px] font-semibold tracking-[0.2em] text-accent-400 uppercase">{{ t('nav.featured') }}</span>
        <span class="relative mt-1.5 block font-display text-xl font-semibold">{{ featured.title }}</span>
        <span class="relative mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-accent-400">
          {{ t('nav.open') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover/feat:translate-x-1" />
        </span>
      </NavMenuLink>
    </div>

    <div class="col-span-9 border-l border-line pl-10">
      <NavSdgGrid v-if="isSdg" :links="group.links" />
      <ul v-else class="gap-x-6" :class="columns">
        <li v-for="link in group.links" :key="link.url" class="break-inside-avoid">
          <NavMenuLink
            :link="link"
            class="group/link flex items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] transition-colors hover:bg-brand-50"
            :class="link.highlight ? 'font-semibold text-brand-800' : 'text-ink/85 hover:text-ink'"
          >
            <span class="size-1.5 shrink-0 rounded-full transition-colors" :class="link.highlight ? 'bg-accent-500' : 'bg-brand-200 group-hover/link:bg-brand-600'" />
            <span class="flex-1">{{ link.title }}</span>
            <span v-if="link.file" class="rounded-md bg-red-50 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-red-700 uppercase">{{ link.file }}</span>
            <Icon v-else name="lucide:arrow-right" class="size-4 shrink-0 -translate-x-1 text-brand-600 opacity-0 transition group-hover/link:translate-x-0 group-hover/link:opacity-100" />
          </NavMenuLink>
        </li>
      </ul>
    </div>
  </div>
</template>
