<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
  text?: string
  link?: { to: string; label: string }
  dark?: boolean
}>()
</script>

<template>
  <div class="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
    <div class="max-w-2xl">
      <p class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] uppercase" :class="dark ? 'text-accent-400' : 'text-accent-600'">
        <span class="h-px w-8" :class="dark ? 'bg-accent-400' : 'bg-accent-500'" />
        {{ eyebrow }}
      </p>
      <h2 class="mt-4 font-display text-4xl leading-tight font-semibold tracking-tight sm:text-5xl" :class="dark ? 'text-white' : 'text-ink'">
        {{ title }}
      </h2>
      <p v-if="text" class="mt-4 text-lg leading-relaxed" :class="dark ? 'text-white/65' : 'text-muted'">{{ text }}</p>
    </div>
    <NuxtLink
      v-if="link"
      :to="link.to"
      class="group inline-flex shrink-0 items-center gap-2 self-start rounded-full border px-5 py-2.5 text-sm font-semibold transition-colors md:self-auto"
      :class="dark ? 'border-white/20 text-white hover:bg-white hover:text-ink' : 'border-ink/15 text-ink hover:border-ink hover:bg-ink hover:text-white'"
    >
      {{ link.label }}
      <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-0.5" />
    </NuxtLink>
  </div>
</template>
