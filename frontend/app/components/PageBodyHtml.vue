<script setup lang="ts">
import type { PageShowcase } from '#shared/types/api'

// Sahifa matni: <!-- showcase:N --> belgisi ([[kartalar-N]]) joyida N-kartali blok; blok bölmasa belgi tashlab yuboriladi
const props = defineProps<{ html: string; docStyle?: boolean; showcase?: PageShowcase[] }>()

const pieces = computed(() => {
  const parts = props.html.split(/<!-- showcase:(\d+) -->/)
  const out: { html?: string; block?: PageShowcase }[] = []
  parts.forEach((part, i) => {
    if (i % 2 === 0) { if (part.trim()) out.push({ html: part }) }
    else {
      const block = props.showcase?.find(b => b.n === Number(part))
      if (block) out.push({ block })
    }
  })
  return out
})
</script>

<template>
  <template v-for="(piece, i) in pieces" :key="i">
    <ProseHtml v-if="piece.html" :html="piece.html" :class="docStyle && 'doc-style'" />
    <PageShowcase v-else-if="piece.block" :data="piece.block" />
  </template>
</template>
