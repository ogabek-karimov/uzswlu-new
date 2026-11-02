<script setup lang="ts">
// Backend'dan kelgan (tozalangan) HTML matn. Ichki havolalar ("/…") sahifa qayta yuklanmasdan,
// joriy til prefiksi bilan ochiladi.
defineProps<{ html: string; lead?: boolean }>()

const localePath = useLocalePath()

function onClick(event: MouseEvent) {
  const link = (event.target as HTMLElement).closest('a')
  if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target === '_blank') return
  const href = link.getAttribute('href') ?? ''
  if (!href.startsWith('/') || href.startsWith('//')) return
  event.preventDefault()
  navigateTo(localePath(href))
}
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -- matn backend'da tozalanadi (ContentPage.body) -->
  <div class="prose-page" :class="lead && 'prose-lead'" @click="onClick" v-html="html" />
</template>
