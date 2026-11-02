<script setup lang="ts">
import { ref } from 'vue'
import { type MediaDoc, uploadMedia } from '@/lib/api'
import { fileSize } from '@/lib/format'
import MediaPicker from './MediaPicker.vue'

// Bitta tildagi PDF: kompyuterdan yuklash, serverdan tanlash, almashtirish, olib tashlash
const props = defineProps<{ modelValue: MediaDoc | null; lang: string; note?: string; accept?: string; kind?: 'pdf' | 'image' | 'all' }>()
const emit = defineEmits<{ 'update:modelValue': [MediaDoc | null] }>()
const input = ref<HTMLInputElement>()
const busy = ref(false)
const error = ref('')
const picker = ref(false)

async function onFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  busy.value = true
  error.value = ''
  try {
    emit('update:modelValue', await uploadMedia(file, { folder: file.type.startsWith('audio/') ? 'audio' : 'docs' }))
  }
  catch (err) {
    error.value = (err as Error).message || 'Yuklab bölmadi'
  }
  finally {
    busy.value = false
    if (input.value) input.value.value = ''
  }
}
</script>

<template>
  <div class="min-w-0">
    <input ref="input" type="file" :accept="accept ?? 'application/pdf'" class="hidden" @change="onFile">
    <div v-if="modelValue" class="flex min-h-[74px] flex-col justify-between gap-1.5 rounded-xl border border-[#BFEBDB] bg-[#F2FCF8] p-2.5">
      <span class="flex items-start gap-2">
        <span class="grid h-9 w-7 shrink-0 place-items-center rounded bg-[#FDECEA] text-[8px] font-extrabold text-[#B42318]">{{ (modelValue.mimeType ?? '').includes('pdf') ? 'PDF' : 'FAYL' }}</span>
        <span class="min-w-0 text-[11px] leading-tight"><b class="block text-[12px]">{{ lang }}</b><span class="block truncate text-muted" :title="modelValue.filename ?? ''">{{ modelValue.filename }}</span><span class="text-subtle">{{ fileSize(modelValue.filesize) }}</span></span>
      </span>
      <span class="flex gap-1">
        <button type="button" class="h-7 flex-1 rounded-lg border border-field bg-white text-[11px] font-semibold" :disabled="busy" @click="input?.click()">{{ busy ? '…' : 'Almaştiriş' }}</button>
        <button type="button" class="h-7 rounded-lg border border-field bg-white px-2 text-[11px] font-semibold text-red-700" :aria-label="`${lang} faylini olib taşlaş`" @click="emit('update:modelValue', null)">✕</button>
      </span>
    </div>
    <div v-else class="flex min-h-[74px] flex-col items-stretch justify-center gap-1 rounded-xl border-2 border-dashed border-[#D3CFE3] bg-[#FAF9FD] p-2 text-center">
      <button type="button" class="text-xs leading-normal font-semibold text-brand-700" :disabled="busy" @click="input?.click()">
        {{ busy ? 'Yuklanmoqda…' : `${kind === 'all' ? 'Fayl' : 'PDF'} · ${lang}` }}<br><span class="font-normal text-subtle">{{ note }}</span>
      </button>
      <button type="button" class="text-[11px] font-semibold text-muted underline" @click="picker = true">serverdan tanlaş</button>
    </div>
    <p v-if="error" class="mt-1 text-[11px] text-red-700">{{ error }}</p>
    <MediaPicker :open="picker" :kind="kind ?? 'pdf'" @close="picker = false" @pick="m => { emit('update:modelValue', m); picker = false }" />
  </div>
</template>
