<script setup lang="ts">
import type { PostSummary } from '#shared/types/api'

// Yangilik / e'lon / tadbir kartasi (ro'yxatlar va "O'xshash yangiliklar")
defineProps<{ item: PostSummary; tone?: number }>()

const localePath = useLocalePath()
const formatDate = useFormatDate()
</script>

<template>
  <article class="group relative">
    <NewsCover :item="item" :tone="tone ?? 0" class="aspect-[16/10] rounded-[22px]" />
    <time :datetime="item.date" class="mt-3.5 block text-[13px] text-muted">{{ formatDate(item.date) }}</time>
    <h3 class="mt-1.5 text-[19px] leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700">
      <NuxtLink :to="localePath(`/${item.type}/${item.slug}`)">
        <span class="absolute inset-0" aria-hidden="true" />
        {{ item.title }}
      </NuxtLink>
    </h3>
  </article>
</template>
