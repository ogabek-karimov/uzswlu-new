<script setup lang="ts">
import { reactive, ref } from 'vue'
import { type I18n, type MediaDoc, uploadMedia } from '@/lib/api'
import { type Lang, PDF_MODES } from '@/lib/constants'
import { DOC_ACCEPT, docTone, extOf, isDocFile, titleFromName } from '@/lib/files'
import { fileSize } from '@/lib/format'
import Collapsible from './Collapsible.vue'
import Icon from './Icon.vue'
import MediaPicker from './MediaPicker.vue'

// Sahifa hujjatlari (admin → Sahifalar): PDF, Word, Excel, PowerPoint va havolalar — saytda matndan keyin çiqadi.
export type Att = { file?: MediaDoc | number | null; url?: string | null; title: I18n; meta?: I18n; display: 'embed' | 'open' | 'download' | 'link'; height?: number | null }
defineProps<{ lang: Lang; langLabel?: string }>()
const list = defineModel<Att[]>({ required: true })
const obj = (v: unknown) => (v && typeof v === 'object' ? v as MediaDoc : null)

// Hujjatlar (PDF, Word, Excel, PowerPoint) va havolalar: bir neçta faylni birdan tanlaş yoki sudrab taşlaş mumkin —
// navbat bilan yuklanadi (jarayon körinib turadi), xato bölgan fayl alohida körsatiladi, qolganlari yuklanaveradi.
const picker = ref(false)
const attInput = ref<HTMLInputElement>()
const uploadState = reactive({ done: 0, total: 0, current: '', errors: [] as string[] })
const dragOver = ref(false)
function newAtt(m: MediaDoc, name: string, single: boolean): Att {
  // Bitta PDF — «Içi körinadi», bir neçtasi — karta (sahifa juda uzun bölmasin); Word/Excel — yuklab olinadi
  const pdf = extOf(name) === 'pdf'
  return { file: m, title: { uz: titleFromName(name) }, meta: {}, display: pdf ? (single ? 'embed' : 'open') : 'download', height: 680 }
}
async function addFiles(picked: FileList | File[] | null | undefined) {
  const files = Array.from(picked ?? [])
  if (!files.length) return
  const bad = files.filter(f => !isDocFile(f.name))
  uploadState.errors = bad.map(f => `${f.name}: faqat PDF, Word, Excel yoki PowerPoint fayl yuklaş mumkin`)
  const good = files.filter(f => isDocFile(f.name))
  uploadState.done = 0
  uploadState.total = good.length
  const single = good.length === 1 && !list.value.some(a => a.display === 'embed')
  for (const f of good) {
    uploadState.current = f.name
    try {
      list.value.push(newAtt(await uploadMedia(f, { folder: 'docs' }), f.name, single))
    }
    catch (err) {
      uploadState.errors.push(`${f.name}: ${(err as Error)?.message || 'yuklanmadi'}`)
    }
    uploadState.done++
  }
  uploadState.total = 0
  uploadState.current = ''
}
async function onAttach(e: Event) {
  const input = e.target as HTMLInputElement
  await addFiles(input.files)
  input.value = ''
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  addFiles(e.dataTransfer?.files)
}
function moveAtt(i: number, d: number) {
  const j = i + d
  if (j < 0 || j >= list.value.length) return
  const [it] = list.value.splice(i, 1)
  list.value.splice(j, 0, it!)
}
const attName = (a: Att) => obj(a.file)?.filename ?? a.url ?? ''
const attExt = (a: Att) => (obj(a.file) ? extOf(obj(a.file)?.filename) || 'pdf' : 'url')
// «Saytda qanday körinadi» izohi — sahifalarda «Içi körinadi» PDF ko'rgiçda (varaqlar 1 2 3 …) oçiladi
const PAGE_PDF_NOTE: Record<string, string> = {
  embed: 'PDF sahifada oçilib turadi: birinçi varaq körinadi, ostida 1 2 3 … — bosilganda faqat varaq almaşadi. Telefonda ham işlaydi.',
  open: 'Karta körinişida; bosilganda PDF yangi oynada oçiladi.',
  download: 'Karta körinişida; bosilganda fayl yuklab olinadi.',
  link: 'Matn ostida faqat nomi (havola); bosilganda PDF oçiladi.',
}
</script>

<template>
  <Collapsible id="page-pdf" title="Hujjatlar (PDF, Word, Excel, PowerPoint)" hint="Matndan keyin çiqadi. Bir neçta faylni birdan tanlaş yoki şu yerga sudrab taşlaş mumkin." :count="list.length">
    <template #actions>
      <button type="button" class="btn-ghost h-9! text-xs!" :disabled="uploadState.total > 0" @click="attInput?.click()">+ Fayl yuklaş</button>
      <button type="button" class="btn-ghost h-9! text-xs!" @click="picker = true">Serverdan tanlaş</button>
      <button type="button" class="btn-ghost h-9! text-xs!" @click="list.push({ file: null, url: '', title: {}, meta: {}, display: 'open' })">+ Havola</button>
    </template>
    <input ref="attInput" type="file" :accept="DOC_ACCEPT" multiple class="hidden" @change="onAttach">
    <MediaPicker :open="picker" kind="pdf" @close="picker = false" @pick="m => { list.push(newAtt(m, m.filename ?? 'fayl.pdf', !list.length)); picker = false }" />
    <!-- Sudrab taşlaş maydoni: fayllar şu yerga taşlansa — navbat bilan yuklanadi -->
    <div
      class="rounded-[14px] border-2 border-dashed px-4 py-5 text-center text-sm transition-colors"
      :class="dragOver ? 'border-[#00C48C] bg-[#E8FBF4] text-ink' : 'border-line text-muted'"
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop.prevent="onDrop"
    >
      <template v-if="uploadState.total">
        <p class="font-semibold text-ink">Yuklanmoqda: {{ uploadState.done + 1 }} / {{ uploadState.total }}</p>
        <p class="mt-1 truncate text-xs">{{ uploadState.current }}</p>
        <span class="mx-auto mt-3 block h-1.5 max-w-xs overflow-hidden rounded-full bg-line"><span class="block h-full rounded-full bg-[#00C48C] transition-all" :style="{ width: `${(uploadState.done / uploadState.total) * 100}%` }" /></span>
      </template>
      <template v-else>
        <Icon name="upload" :size="20" class="mx-auto mb-1.5" />
        Fayllarni şu yerga sudrab taşlang yoki <button type="button" class="font-semibold text-ink underline underline-offset-2" @click="attInput?.click()">kompyuterdan tanlang</button>
        <span class="mt-1 block text-xs">PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX · har biri 50 MB gaça</span>
      </template>
    </div>
    <ul v-if="uploadState.errors.length" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-xs text-red-700" role="alert">
      <li v-for="(e, i) in uploadState.errors" :key="i">{{ e }}</li>
    </ul>
    <div v-for="(a, i) in list" :key="i" class="rounded-[14px] border border-line p-3.5">
      <div class="flex items-start gap-3">
        <span aria-hidden="true" class="grid h-11 w-10 shrink-0 place-items-center rounded-md text-[9px] font-extrabold uppercase" :style="{ background: docTone(attExt(a)).bg, color: docTone(attExt(a)).fg }">{{ attExt(a) }}</span>
        <div class="grid min-w-0 flex-1 gap-2 sm:grid-cols-2">
          <input v-model="a.title[lang]" class="field" :aria-label="`Nomi · ${lang}`" :placeholder="`Nomi · ${langLabel}`">
          <input v-model="a.meta![lang]" class="field" :aria-label="`Izoh · ${lang}`" placeholder="Izoh (ixtiyoriy, masalan: 2023-yil)">
          <p v-if="obj(a.file)" class="truncate text-xs text-subtle sm:col-span-2" :title="attName(a)">{{ attName(a) }} · {{ fileSize(obj(a.file)?.filesize) }}</p>
          <input v-else v-model="a.url" class="field sm:col-span-2" aria-label="Havola" placeholder="https://…">
        </div>
        <div class="flex shrink-0 flex-col gap-0.5">
          <button type="button" class="grid size-8 place-items-center rounded-lg text-subtle hover:bg-canvas hover:text-ink disabled:opacity-30" :disabled="i === 0" aria-label="Yuqoriga" @click="moveAtt(i, -1)"><Icon name="chevronUp" :size="14" /></button>
          <button type="button" class="grid size-8 place-items-center rounded-lg text-subtle hover:bg-canvas hover:text-ink disabled:opacity-30" :disabled="i === list.length - 1" aria-label="Pastga" @click="moveAtt(i, 1)"><Icon name="chevronDown" :size="14" /></button>
          <button type="button" class="grid size-8 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" aria-label="Hujjatni olib taşlaş" @click="list.splice(i, 1)"><Icon name="trash" :size="14" /></button>
        </div>
      </div>
      <div v-if="obj(a.file) && attExt(a) === 'pdf'" class="mt-3">
        <p class="mb-1.5 text-[13px] font-semibold">Saytda qanday körinadi:</p>
        <div role="radiogroup" aria-label="Saytda qanday körinadi" class="grid grid-cols-2 gap-1 rounded-xl bg-canvas p-1 sm:grid-cols-4">
          <button v-for="m in PDF_MODES" :key="m.value" type="button" role="radio" :aria-checked="a.display === m.value" class="min-h-9 rounded-[9px] px-1.5 text-xs font-semibold" :class="a.display === m.value ? 'bg-white text-ink shadow-sm' : 'text-muted'" @click="a.display = m.value">{{ m.label }}</button>
        </div>
        <!-- Tanlangan körinişning izohi (sahifalar uçun) -->
        <p class="mt-1.5 text-xs text-muted">{{ PAGE_PDF_NOTE[a.display] }}</p>
      </div>
      <p v-else-if="obj(a.file)" class="mt-2 text-xs text-muted">Saytda karta körinişida; bosilganda fayl yuklab olinadi (Word/Excel/PowerPoint brauzerda oçilmaydi).</p>
    </div>
  </Collapsible>
</template>
