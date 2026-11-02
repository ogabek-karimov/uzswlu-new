<script setup lang="ts">
// Ichki sahifa boshi: yo'l (breadcrumb), sarlavha, kirish matni; o'ng tomonga — slot (statistika, qidiruv …)
defineProps<{
  crumbs: { label: string; to?: string }[]
  title: string
  lead?: string | null
  eyebrow?: string
}>()
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
    <PageBreadcrumbs :items="crumbs" />
    <div class="mt-7 flex flex-wrap items-end justify-between gap-6">
      <div class="max-w-3xl min-w-0">
        <p v-if="eyebrow" class="mb-3.5 flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">
          <span class="h-px w-8 bg-accent-500" />
          {{ eyebrow }}
        </p>
        <h1 class="font-display text-[2.75rem] leading-[1.04] font-semibold tracking-tight text-ink sm:text-6xl lg:text-[64px]">{{ title }}</h1>
        <p v-if="lead" class="mt-4 text-lg leading-relaxed text-muted sm:text-xl">{{ lead }}</p>
      </div>
      <slot />
    </div>
  </section>
</template>
