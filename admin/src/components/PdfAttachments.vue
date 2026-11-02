<script setup lang="ts">
import { ref } from 'vue'
import { type I18n, uploadMedia } from '@/lib/api'
import { type Lang, LANGS, PDF_MODES } from '@/lib/constants'
import { fileSize } from '@/lib/format'
import type { Attachment } from '@/lib/posts'
import Icon from './Icon.vue'

// Biriktirilgan PDF'lar: har biri uchun saytda ko'rinishi
// (ichi ko'rinadi / bosib ochiladi / yuklab olish / matn-havola — masalan, avtoreferat)
const props = defineProps<{ lang: Lang }>()
const list = defineModel<Attachment[]>({ required: true })
const input = ref<HTMLInputElement>()
const busy = ref(false)
let preset: { title: I18n; display: Attachment['display'] } | null = null

const AUTOREFERAT: I18n = { uz: 'AVTOREFERAT', ru: 'АВТОРЕФЕРАТ', en: 'ABSTRACT', zh: '论文摘要' }

function pick(withPreset: typeof preset) {
  preset = withPreset
  input.value?.click()
}

async function onFile(e: Event) {
  const files = [...((e.target as HTMLInputElement).files ?? [])]
  busy.value = true
  try {
    for (const file of files) {
      const media = await uploadMedia(file, { folder: 'docs' })
      const title = preset?.title ?? { uz: file.name.replace(/\.pdf$/i, '') }
      list.value = [...list.value, { file: media, title: { uz: '', ru: '', en: '', zh: '', ...title }, display: preset?.display ?? 'open', height: 680 }]
    }
  }
  finally {
    busy.value = false
    preset = null
    if (input.value) input.value.value = ''
  }
}

const name = (a: Attachment) => (typeof a.file === 'object' ? a.file.filename : '') ?? ''
const meta = (a: Attachment) => (typeof a.file === 'object' ? fileSize(a.file.filesize) : '')
const remove = (i: number) => { list.value = list.value.filter((_, k) => k !== i) }
const langLabel = () => LANGS.find(l => l.code === props.lang)!.short
</script>

<template>
  <div>
    <input ref="input" type="file" accept="application/pdf" multiple class="hidden" @change="onFile">
    <div class="flex flex-wrap items-baseline justify-between gap-2.5">
      <h2 class="text-base font-bold">Fayllar (PDF)</h2>
      <span class="flex gap-3.5">
        <button type="button" class="text-[13px] font-semibold text-brand-700" title="Dissertatsiya e’lonlari uçun: PDF tanlanadi, nomi 4 tilda öz-özidan yoziladi" :disabled="busy" @click="pick({ title: AUTOREFERAT, display: 'link' })">+ Avtoreferat</button>
        <button type="button" class="text-[13px] font-semibold text-brand-700" :disabled="busy" @click="pick(null)">{{ busy ? 'Yuklanmoqda…' : '+ PDF qöşiş' }}</button>
      </span>
    </div>
    <p v-if="!list.length" class="mt-3 text-[13px] text-subtle">Hali fayl yöq. Masalan: dastur, buyruq, hisobot yoki avtoreferat.</p>
    <div v-for="(a, i) in list" :key="i" class="mt-3.5 flex flex-wrap items-center gap-3 rounded-[14px] border border-line p-3">
      <span class="grid h-10 w-8 shrink-0 place-items-center rounded-md bg-red-50 text-[9px] font-extrabold text-red-700">PDF</span>
      <span class="min-w-0 flex-[1_1_220px] leading-snug">
        <span class="flex items-center gap-1.5">
          <span class="chip shrink-0 bg-brand-100 px-1.5! py-0.5! text-[10px]! text-brand-800">{{ langLabel() }}</span>
          <input v-model="a.title![lang]" class="min-w-0 flex-1 bg-transparent text-sm font-bold outline-none" :aria-label="`Fayl nomi (${langLabel()})`" :placeholder="a.title?.uz || name(a)">
        </span>
        <span class="text-xs text-subtle">{{ name(a) }} · {{ meta(a) }}</span>
      </span>
      <div role="radiogroup" aria-label="Saytda körinişi" class="grid flex-[1_1_380px] grid-cols-4 gap-1 rounded-xl bg-canvas p-1">
        <button
          v-for="m in PDF_MODES" :key="m.value" type="button" role="radio" :aria-checked="a.display === m.value" :title="m.note"
          class="min-h-9 rounded-[9px] px-1.5 text-xs font-semibold" :class="a.display === m.value ? 'bg-white text-ink shadow-sm' : 'text-muted'"
          @click="a.display = m.value"
        >{{ m.label }}</button>
      </div>
      <button type="button" class="grid size-9 place-items-center rounded-lg text-muted hover:bg-red-50 hover:text-red-700" aria-label="Faylni olib taşlaş" @click="remove(i)"><Icon name="x" :size="16" /></button>
      <div v-if="a.display === 'embed'" class="flex w-full flex-wrap items-center gap-1.5 pl-11 text-xs text-muted">
        Ramka balandligi:
        <button
          v-for="h in [480, 680, 880]" :key="h" type="button" :aria-pressed="(a.height ?? 680) === h"
          class="h-7 rounded-full px-2.5 font-semibold" :class="(a.height ?? 680) === h ? 'bg-ink text-white' : 'border border-field bg-white text-[#3D3958]'"
          @click="a.height = h"
        >{{ h }}px</button>
      </div>
      <p v-else class="w-full pl-11 text-xs text-subtle">{{ PDF_MODES.find(m => m.value === a.display)?.note }}</p>
    </div>
    <p v-if="list.length" class="mt-2 text-xs text-subtle">Fayl nomi har til uçun alohida — tepadagi til tablarida almaştiring.</p>
  </div>
</template>
