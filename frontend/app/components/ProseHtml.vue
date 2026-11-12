<script setup lang="ts">
// Backend'dan kelgan (tozalangan) HTML matn. Ichki havolalar ("/…") sahifa qayta yuklanmasdan,
// joriy til prefiksi bilan ochiladi. Matndagi rasm (havola ichida bo'lmasa) bosilsa — to'liq ekranda kattalashadi.
defineOptions({ inheritAttrs: false })
defineProps<{ html: string; lead?: boolean }>()

const localePath = useLocalePath()
const viewerImages = ref<string[]>([])
const viewerIndex = ref<number | null>(null)
const viewerCaption = ref('')

function openImage(img: HTMLImageElement, root: HTMLElement) {
  const images = Array.from(root.querySelectorAll('img')).filter(i => !i.closest('a'))
  viewerImages.value = images.map(i => i.currentSrc || i.src)
  viewerCaption.value = img.alt
  viewerIndex.value = images.indexOf(img)
}

function onClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  const img = target.closest('img')
  if (img && !img.closest('a')) {
    openImage(img, event.currentTarget as HTMLElement)
    return
  }
  const link = target.closest('a')
  if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target === '_blank') return
  const href = link.getAttribute('href') ?? ''
  if (!href.startsWith('/') || href.startsWith('//')) return
  event.preventDefault()
  navigateTo(localePath(href))
}
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -- matn backend'da tozalanadi (ContentPage.body) -->
  <div v-bind="$attrs" class="prose-page" :class="lead && 'prose-lead'" @click="onClick" v-html="html" />
  <ImageViewer v-model:index="viewerIndex" :images="viewerImages" :caption="viewerCaption" />
</template>
