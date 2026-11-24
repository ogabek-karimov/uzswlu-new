<script setup lang="ts">
import type { Attachment } from '#shared/types/api'

// Bir nechta «Içi körinadi» PDF: tepada hujjatlar röyxati, ostida bitta ko'rgiç — tanlansa faqat ko'rgiçdagi hujjat almaşadi
// (sahifa qayta yuklanmaydi). Masalan, PhD dasturlari (10 ta), Stipendiyalar (3 ta).
const props = defineProps<{ docs: Attachment[] }>()
const { t } = useI18n()
const active = ref(0)
const viewer = ref<HTMLElement>()
const current = computed(() => props.docs[active.value] ?? props.docs[0]!)

function pick(i: number) {
  if (i === active.value) return
  active.value = i
  nextTick(() => {
    const top = viewer.value?.getBoundingClientRect().top ?? 0
    if (top < 80 || top > window.innerHeight * 0.6) {
      viewer.value?.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
    }
  })
}
</script>

<template>
  <section class="flex flex-col gap-4" :aria-label="t('pdf.files')">
    <ol class="grid gap-2 sm:grid-cols-2">
      <li v-for="(doc, i) in docs" :key="doc.url">
        <button
          type="button"
          class="group flex h-full w-full items-start gap-3 rounded-2xl border p-3.5 text-left transition duration-200"
          :class="i === active ? 'border-brand-800 bg-brand-800 text-white shadow-[0_16px_34px_-22px_rgb(28_21_72/0.7)]' : 'border-line bg-white text-ink hover:-translate-y-0.5 hover:border-brand-300'"
          :aria-pressed="i === active"
          @click="pick(i)"
        >
          <span aria-hidden="true" class="grid size-9 shrink-0 place-items-center rounded-xl text-[13px] font-extrabold tabular-nums" :class="i === active ? 'bg-white/15 text-accent-400' : 'bg-red-50 text-red-600'">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="min-w-0 flex-1">
            <span class="block text-[15px] leading-snug font-semibold">{{ doc.title }}</span>
            <span v-if="doc.meta" class="mt-0.5 block text-[13px]" :class="i === active ? 'text-white/70' : 'text-muted'">{{ doc.meta }}</span>
          </span>
          <Icon :name="i === active ? 'lucide:eye' : 'lucide:file-text'" class="mt-1 shrink-0 text-base" :class="i === active ? 'text-accent-400' : 'text-muted'" />
        </button>
      </li>
    </ol>
    <div ref="viewer" class="scroll-mt-32">
      <PdfPager :key="current.url" :url="current.url" :title="current.title" />
    </div>
  </section>
</template>
