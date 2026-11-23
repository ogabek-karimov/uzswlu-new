<script setup lang="ts">
// PDF ko'rgiç (pdf.js): bir vaqtda bitta varaq, ostida ← 1 2 3 … → — bosilsa faqat varaq almaşadi, sahifa joyida qoladi.
// Klaviatura: ← / → (ko'rgiç fokusda bo'lsa). Telefonda ham işlaydi (brauzerning PDF ko'rgiçiga bog'liq emas).
// pdf.js faqat brauzerda yuklanadi (SSR'da — yuklanish holati).
import type { PDFDocumentProxy, RenderTask } from 'pdfjs-dist'

const props = defineProps<{ url: string; title?: string }>()
const { t } = useI18n()

const host = ref<HTMLElement>()
const canvas = ref<HTMLCanvasElement>()
const page = ref(1)
const total = ref(0)
const state = ref<'loading' | 'ready' | 'error'>('loading')
const busy = ref(false)
const minHeight = ref(0) // varaq almaşganda sahifa sakramasin

let pdf: PDFDocumentProxy | null = null
let task: RenderTask | null = null
let observer: ResizeObserver | undefined
let lastWidth = 0

async function render(n: number) {
  if (!pdf || !canvas.value || !host.value) return
  busy.value = true
  try {
    task?.cancel()
    const p = await pdf.getPage(n)
    const width = host.value.clientWidth
    const base = p.getViewport({ scale: 1 })
    const scale = width / base.width
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5)
    const viewport = p.getViewport({ scale: scale * dpr })
    const c = canvas.value
    c.width = Math.floor(viewport.width)
    c.height = Math.floor(viewport.height)
    c.style.width = `${Math.floor(width)}px`
    c.style.height = `${Math.floor(viewport.height / dpr)}px`
    task = p.render({ canvasContext: c.getContext('2d')!, viewport })
    await task.promise
    minHeight.value = Math.max(minHeight.value, viewport.height / dpr)
    lastWidth = width
  }
  catch (e) {
    if ((e as { name?: string })?.name !== 'RenderingCancelledException') state.value = 'error'
  }
  finally {
    busy.value = false
  }
}

function go(n: number) {
  if (n < 1 || n > total.value || n === page.value) return
  page.value = n
  render(n)
  // Pastdagi raqam bosilganda — yangi varaq boşidan öqiladi: ko'rgiç tepasi ekrandan çiqib ketgan bo'lsa, faqat unga qadar ko'tariladi
  const top = host.value?.getBoundingClientRect().top ?? 0
  if (top < 90) host.value?.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowRight') { e.preventDefault(); go(page.value + 1) }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); go(page.value - 1) }
}

// 1 … 4 5 6 … 20 — ko'p varaqli hujjatda ham bitta qatorga sig'adi
const pages = computed<(number | '…')[]>(() => {
  const n = total.value
  const c = page.value
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

onMounted(async () => {
  try {
    const pdfjs = await import('pdfjs-dist')
    const worker = (await import('pdfjs-dist/build/pdf.worker.min.mjs?url')).default
    pdfjs.GlobalWorkerOptions.workerSrc = worker
    pdf = await pdfjs.getDocument({ url: props.url }).promise
    total.value = pdf.numPages
    state.value = 'ready'
    await nextTick()
    await render(1)
    // Kenglik özgarsa (oyna, şrift) — varaq qayta çiziladi
    observer = new ResizeObserver(() => {
      if (host.value && Math.abs(host.value.clientWidth - lastWidth) > 8) {
        minHeight.value = 0
        render(page.value)
      }
    })
    if (host.value) observer.observe(host.value)
  }
  catch {
    state.value = 'error'
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
  task?.cancel()
  pdf?.destroy()
})
</script>

<template>
  <figure class="pdf-pager overflow-hidden rounded-[22px] border border-line bg-white">
    <figcaption v-if="title" class="flex items-center gap-3 border-b border-line px-4 py-3 sm:px-5">
      <span aria-hidden="true" class="grid size-9 shrink-0 place-items-center rounded-xl bg-red-50 text-red-600"><Icon name="lucide:file-text" class="text-lg" /></span>
      <span class="min-w-0 flex-1 leading-snug font-semibold text-ink">{{ title }}</span>
      <a :href="url" download class="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-full bg-brand-800 px-3.5 text-[13px] font-semibold text-white transition-colors hover:bg-brand-700">
        <Icon name="lucide:download" class="text-sm" /><span class="hidden sm:inline">{{ t('page.download') }}</span>
      </a>
    </figcaption>

    <div
      ref="host"
      class="relative scroll-mt-32 bg-[#f4f3f8] outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      :style="{ minHeight: minHeight ? `${minHeight}px` : '320px' }"
      tabindex="0"
      :aria-label="t('pdf.viewer', { title: title || 'PDF' })"
      @keydown="onKey"
    >
      <canvas v-show="state === 'ready'" ref="canvas" class="block transition-opacity duration-200" :class="busy && 'opacity-60'" :aria-label="t('pdf.pageOf', { n: page, total })" role="img" />
      <div v-if="state === 'loading'" class="absolute inset-0 grid place-items-center text-sm text-muted">
        <span class="flex items-center gap-2"><Icon name="lucide:loader-circle" class="animate-spin text-lg" />{{ t('pdf.loading') }}</span>
      </div>
      <div v-else-if="state === 'error'" class="absolute inset-0 grid place-items-center p-6 text-center text-sm text-muted">
        <p>{{ t('pdf.error') }} <a :href="url" target="_blank" rel="noopener" class="font-semibold text-brand-700 underline">{{ t('page.download') }}</a></p>
      </div>
    </div>

    <!-- Varaqlar: ← 1 2 3 … → -->
    <nav v-if="state === 'ready' && total > 1" class="flex flex-wrap items-center justify-center gap-1.5 border-t border-line px-3 py-3" :aria-label="t('pdf.pages')">
      <button type="button" class="pdf-btn" :disabled="page === 1" :aria-label="t('pdf.prev')" @click="go(page - 1)"><Icon name="lucide:chevron-left" /></button>
      <template v-for="(p, i) in pages" :key="i">
        <span v-if="p === '…'" class="px-1 text-muted" aria-hidden="true">…</span>
        <button v-else type="button" class="pdf-btn tabular-nums" :class="p === page && 'is-on'" :aria-current="p === page ? 'page' : undefined" :aria-label="t('pdf.pageOf', { n: p, total })" @click="go(p)">{{ p }}</button>
      </template>
      <button type="button" class="pdf-btn" :disabled="page === total" :aria-label="t('pdf.next')" @click="go(page + 1)"><Icon name="lucide:chevron-right" /></button>
    </nav>
  </figure>
</template>

<style scoped>
.pdf-btn {
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
  transition: background-color 0.2s, color 0.2s, border-color 0.2s, transform 0.2s;
}
.pdf-btn:hover:not(:disabled):not(.is-on) { border-color: var(--color-brand-700); transform: translateY(-1px); }
.pdf-btn.is-on { background: var(--color-brand-800); border-color: var(--color-brand-800); color: #fff; }
.pdf-btn:disabled { opacity: 0.35; cursor: not-allowed; }
</style>
