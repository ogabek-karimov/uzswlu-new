<script setup lang="ts">
// Ichki sahifa boshi: yo'l (breadcrumb), sarlavha, kirish matni; o'ng tomonga — slot (statistika, qidiruv …)
// Töq indigo fon (mint va lavanda nur): assets/css/main.css → .page-hero; slot ham töq fonda turadi
defineProps<{
  crumbs: { label: string; to?: string }[]
  title: string
  lead?: string | null
  eyebrow?: string
}>()
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
    <div class="page-hero px-5 py-6 sm:px-8 sm:py-7">
      <PageBreadcrumbs :items="crumbs" dark />
      <div class="mt-4 flex flex-wrap items-end justify-between gap-5">
        <div class="max-w-3xl min-w-0">
          <p v-if="eyebrow" class="mb-3.5 flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-accent-400 uppercase">
            <span class="h-px w-8 bg-accent-400" />
            {{ eyebrow }}
          </p>
          <h1 class="font-display text-[2.25rem] leading-[1.06] font-semibold tracking-tight text-white sm:text-5xl lg:text-[52px]">{{ title }}</h1>
          <p v-if="lead" class="mt-3 text-base leading-relaxed text-white/75 sm:text-lg">{{ lead }}</p>
        </div>
        <slot />
      </div>
    </div>
  </section>
</template>
