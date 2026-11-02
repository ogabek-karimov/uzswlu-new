<script setup lang="ts">
defineProps<{ items: { label: string; to?: string }[]; dark?: boolean }>()

const { t } = useI18n()
const localePath = useLocalePath()
</script>

<template>
  <nav :aria-label="t('nav.breadcrumb')" class="text-sm" :class="dark ? 'text-white/60' : 'text-muted'">
    <ol class="flex flex-wrap items-center gap-x-2 gap-y-1">
      <li class="flex items-center gap-2">
        <NuxtLink :to="localePath('/')" class="transition-colors" :class="dark ? 'hover:text-white' : 'hover:text-ink'">{{ t('nav.home') }}</NuxtLink>
      </li>
      <li v-for="(item, i) in items" :key="i" class="flex min-w-0 items-center gap-2">
        <span aria-hidden="true" :class="dark ? 'text-white/30' : 'text-line'">/</span>
        <NuxtLink v-if="item.to" :to="localePath(item.to)" class="transition-colors" :class="dark ? 'hover:text-white' : 'hover:text-ink'">{{ item.label }}</NuxtLink>
        <span v-else-if="i < items.length - 1">{{ item.label }}</span>
        <span v-else aria-current="page" class="max-w-[60vw] truncate font-medium sm:max-w-md" :class="dark ? 'text-white' : 'text-ink'">{{ item.label }}</span>
      </li>
    </ol>
  </nav>
</template>
