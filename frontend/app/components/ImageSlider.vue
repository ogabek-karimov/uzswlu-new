<script setup lang="ts">
// Rasm slayderi (buklet sahifalari): bitta katta rasm, ostida ← 1 2 3 … → — bosilsa faqat rasm almaşadi, sahifa joyida qoladi.
// ← / → klaviatura; rasm bosilsa — to'liq ekranda (ImageViewer). Keyingi rasm oldindan yuklanadi.
type Photo = { url: string; thumb: string; alt: string; width?: number | null; height?: number | null }
const props = defineProps<{ photos: Photo[] }>()
const { t } = useI18n()

const index = ref(0)
const viewer = ref<number | null>(null)
const total = computed(() => props.photos.length)
const current = computed(() => props.photos[index.value]!)
const ratio = computed(() => {
  const p = props.photos[0]
  return p?.width && p.height ? `${p.width} / ${p.height}` : '3 / 4'
})

function go(n: number) {
  if (n < 0 || n >= total.value) return
  index.value = n
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowRight') { e.preventDefault(); go(index.value + 1) }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); go(index.value - 1) }
}
// Keyingi rasmni oldindan yuklab qo'yiş — almaşganda kutilmaydi
watch(index, (i) => {
  const next = props.photos[i + 1]
  if (next && import.meta.client) new Image().src = next.url
}, { immediate: true })

// 1 … 4 5 6 … 17
const pages = computed<(number | '…')[]>(() => {
  const n = total.value
  const c = index.value + 1
  if (n <= 9) return Array.from({ length: n }, (_, i) => i + 1)
  const set = new Set([1, 2, n - 1, n, c - 1, c, c + 1].filter(x => x >= 1 && x <= n))
  const list = [...set].sort((a, b) => a - b)
  const out: (number | '…')[] = []
  list.forEach((x, i) => {
    if (i && x - list[i - 1]! > 1) out.push('…')
    out.push(x)
  })
  return out
})
</script>

<template>
  <figure class="overflow-hidden rounded-[22px] border border-line bg-white" tabindex="0" :aria-label="t('slider.label', { n: index + 1, total })" @keydown="onKey">
    <div class="relative bg-[#f4f3f8]">
      <button type="button" class="group block w-full cursor-zoom-in" :aria-label="current.alt || t('slider.open')" @click="viewer = index">
        <img :src="current.url" :alt="current.alt" loading="lazy" decoding="async" class="mx-auto block max-h-[85vh] w-full object-contain" :style="{ aspectRatio: ratio }">
      </button>
      <button v-if="index > 0" type="button" class="slide-nav left-3" :aria-label="t('pdf.prev')" @click="go(index - 1)"><Icon name="lucide:chevron-left" class="text-xl" /></button>
      <button v-if="index < total - 1" type="button" class="slide-nav right-3" :aria-label="t('pdf.next')" @click="go(index + 1)"><Icon name="lucide:chevron-right" class="text-xl" /></button>
      <span class="absolute top-3 right-3 rounded-full bg-black/55 px-2.5 py-1 text-xs font-bold text-white tabular-nums backdrop-blur-sm">{{ index + 1 }} / {{ total }}</span>
    </div>
    <nav v-if="total > 1" class="flex flex-wrap items-center justify-center gap-1.5 border-t border-line px-3 py-3" :aria-label="t('slider.pages')">
      <template v-for="(p, i) in pages" :key="i">
        <span v-if="p === '…'" class="px-1 text-muted" aria-hidden="true">…</span>
        <button v-else type="button" class="pg-btn tabular-nums" :class="p === index + 1 && 'is-on'" :aria-current="p === index + 1 ? 'true' : undefined" :aria-label="t('slider.label', { n: p, total })" @click="go(p - 1)">{{ p }}</button>
      </template>
    </nav>
    <ImageViewer v-model:index="viewer" :images="photos.map(p => p.url)" :caption="viewer !== null ? photos[viewer]?.alt : ''" />
  </figure>
</template>

<style scoped>
.slide-nav {
  position: absolute;
  top: 50%;
  translate: 0 -50%;
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 9999px;
  background: rgb(255 255 255 / 0.92);
  color: var(--color-ink);
  box-shadow: 0 8px 24px -10px rgb(28 21 72 / 0.5);
  transition: transform 0.2s, background-color 0.2s;
}
.slide-nav:hover { transform: scale(1.08); background: #fff; }
.pg-btn {
  display: inline-grid;
  place-items: center;
  min-width: 2.5rem;
  height: 2.5rem;
  padding: 0 0.6rem;
  border-radius: 9999px;
  border: 1px solid var(--color-line);
  background: #fff;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-ink);
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}
.pg-btn:hover:not(.is-on) { border-color: var(--color-brand-700); }
.pg-btn.is-on { background: var(--color-brand-800); border-color: var(--color-brand-800); color: #fff; }
</style>
