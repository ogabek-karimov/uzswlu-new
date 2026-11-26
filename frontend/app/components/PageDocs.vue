<script setup lang="ts">
import type { Attachment } from '#shared/types/api'

// Sahifa hujjatlari: «ichi ko'rinadi» PDF — ko'rgiçda (bitta — to'g'ridan-to'g'ri, bir nechta — tanlagiç bilan);
// qolganlari — karta: turi belgisi (PDF qizil, Word ko'k, Excel yaşil, PowerPoint to'q sariq), nomi, hajmi,
// «Köriş» (PDF, havola) va «Yuklab oliş» (fayl). Word/Excel/PowerPoint brauzerda oçilmaydi — faqat yuklab olinadi.
const props = defineProps<{ docs: Attachment[] }>()
const { t } = useI18n()

const embed = computed(() => props.docs.filter(f => f.kind === 'pdf' && f.display === 'embed'))
const list = computed(() => props.docs.filter(f => !(f.kind === 'pdf' && f.display === 'embed')))

const TONE: Record<string, string> = {
  PDF: 'from-red-50 to-red-100 text-red-600 [--badge:var(--color-red-600)]',
  DOC: 'from-sky-50 to-sky-100 text-sky-700 [--badge:var(--color-sky-700)]',
  XLS: 'from-emerald-50 to-emerald-100 text-emerald-700 [--badge:var(--color-emerald-700)]',
  PPT: 'from-orange-50 to-orange-100 text-orange-600 [--badge:var(--color-orange-600)]',
}
function tone(file: Attachment) {
  if (file.kind === 'link') return 'from-brand-50 to-brand-100 text-brand-700 [--badge:var(--color-brand-700)]'
  const ext = (file.ext ?? 'PDF').slice(0, 3)
  return TONE[ext] ?? TONE.PDF
}
function icon(file: Attachment) {
  if (file.kind === 'link') return 'lucide:link'
  const ext = (file.ext ?? '').slice(0, 3)
  return ext === 'XLS' ? 'lucide:file-spreadsheet' : ext === 'PPT' ? 'lucide:presentation' : 'lucide:file-text'
}
</script>

<template>
  <div class="flex flex-col gap-12">
    <PdfPager v-if="embed.length === 1" :url="embed[0]!.url" :title="embed[0]!.title" />
    <PdfDocs v-else-if="embed.length > 1" :docs="embed" />
    <ul v-if="list.length" class="flex flex-col gap-3">
      <li v-for="file in list" :key="file.url" class="group relative flex flex-col gap-4 rounded-3xl hover:z-10 focus-within:z-10 border border-line bg-white p-4 transition duration-300 hover:border-accent-500 hover:shadow-[0_20px_44px_-32px_rgb(28_21_72/0.5)] sm:flex-row sm:items-center sm:p-5">
        <span aria-hidden="true" class="relative grid size-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br transition-transform duration-300 group-hover:-rotate-6" :class="tone(file)">
          <Icon :name="icon(file)" class="size-7" />
          <span v-if="file.kind !== 'link'" class="absolute -right-1.5 -bottom-1.5 rounded-md bg-(--badge) px-1.5 py-0.5 text-[9px] font-extrabold tracking-wide text-white">{{ file.ext ?? 'PDF' }}</span>
        </span>
        <span class="min-w-0 flex-1">
          <a :href="file.url" target="_blank" rel="noopener" :download="file.kind === 'doc' ? '' : undefined" class="block leading-snug font-semibold [overflow-wrap:anywhere] text-ink hover:text-brand-700">{{ file.title }}</a>
          <span v-if="file.meta" class="mt-1 block text-[13px] text-muted">{{ file.meta }}</span>
        </span>
        <span class="flex shrink-0 gap-2">
          <a v-if="file.kind !== 'doc'" :href="file.url" target="_blank" rel="noopener" class="inline-flex h-11 items-center gap-2 rounded-full border border-line bg-paper px-4 text-sm font-semibold text-ink transition-colors hover:border-brand-700">
            <Icon name="lucide:eye" class="size-4" />{{ t('page.view') }}
          </a>
          <a v-if="file.kind !== 'link'" :href="file.url" download class="inline-flex h-11 items-center gap-2 rounded-full bg-brand-800 px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-700">
            <Icon name="lucide:download" class="size-4 transition-transform group-hover:translate-y-0.5" />{{ t('page.download') }}
          </a>
        </span>
      </li>
    </ul>
  </div>
</template>
