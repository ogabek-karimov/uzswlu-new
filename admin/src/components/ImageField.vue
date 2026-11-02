<script setup lang="ts">
import { ref } from 'vue'
import { type MediaDoc, uploadMedia } from '@/lib/api'
import { fileSize } from '@/lib/format'
import Icon from './Icon.vue'

// Bitta rasm: yuklash, almashtirish, o'chirish. Rasm serverda WebP'ga o'giriladi.
// badge berilsa — plitka ko'rinishi (masalan "UZ · asosiy"), tugmalar rasm ustida.
const props = defineProps<{ modelValue: MediaDoc | null; label?: string; compact?: boolean; badge?: string; folder?: string }>()
const emit = defineEmits<{ 'update:modelValue': [MediaDoc | null] }>()
const input = ref<HTMLInputElement>()
const busy = ref(false)
const error = ref('')

async function onFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  busy.value = true
  error.value = ''
  try {
    emit('update:modelValue', await uploadMedia(file, { folder: props.folder ?? 'posts' }))
  }
  catch (err) {
    error.value = (err as Error).message || 'Yuklab bölmadi'
  }
  finally {
    busy.value = false
    if (input.value) input.value.value = ''
  }
}

const url = (m: MediaDoc) => m.sizes?.card?.url ?? m.url ?? ''
const pick = () => input.value?.click()
</script>

<template>
  <div>
    <input ref="input" type="file" accept="image/*" class="hidden" @change="onFile">

    <!-- Plitka: til belgisi va rasm ustidagi tugmalar -->
    <template v-if="badge">
      <div v-if="modelValue" class="relative aspect-[4/3] overflow-hidden rounded-xl bg-brand-800">
        <img :src="url(modelValue)" alt="" class="size-full object-cover">
        <span class="chip absolute top-2 left-2 bg-white text-[11px]! font-extrabold text-ink">{{ badge }}</span>
        <span class="absolute inset-x-2 bottom-2 flex gap-1.5">
          <button type="button" class="h-[30px] flex-1 rounded-lg bg-white/92 text-[11px] font-bold text-ink" :disabled="busy" @click="pick">{{ busy ? 'Yuklanmoqda…' : 'Almaştiriş' }}</button>
          <button type="button" :aria-label="`${badge} rasmini öçiriş`" class="grid size-[30px] place-items-center rounded-lg bg-night/70 text-white" @click="emit('update:modelValue', null)"><Icon name="x" :size="13" /></button>
        </span>
      </div>
      <button
        v-else type="button" :disabled="busy"
        class="flex aspect-[4/3] w-full flex-col items-center justify-center gap-1.5 rounded-xl border-2 border-dashed border-[#D3CFE3] bg-[#FAF9FD] text-xs font-bold text-brand-700"
        @click="pick"
      >
        <span class="chip bg-brand-100 text-[11px]! font-extrabold">{{ badge }}</span>
        {{ busy ? 'Yuklanmoqda…' : '+ Rasm yuklaş' }}
      </button>
    </template>

    <template v-else>
      <div v-if="modelValue" class="relative overflow-hidden rounded-[14px] bg-brand-800" :class="compact ? 'aspect-square' : 'aspect-video'">
        <img :src="url(modelValue)" :alt="modelValue.alt?.uz ?? ''" class="size-full object-cover">
        <span v-if="!compact" class="absolute bottom-3 left-3 rounded-full bg-night/70 px-2.5 py-1 text-xs text-white">{{ modelValue.filename }} · {{ fileSize(modelValue.filesize) }} · WebP</span>
      </div>
      <button
        v-else type="button" :disabled="busy"
        class="flex w-full flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-[#D3CFE3] bg-[#FAF9FD] text-xs font-semibold text-brand-700"
        :class="compact ? 'aspect-square' : 'aspect-video'"
        @click="pick"
      >
        <Icon name="upload" :size="compact ? 16 : 22" />
        {{ busy ? 'Yuklanmoqda…' : (label ?? 'Rasm yuklaş') }}
      </button>
      <div v-if="modelValue && !compact" class="mt-2.5 flex gap-2">
        <button type="button" class="btn-ghost h-10! flex-1 text-[13px]!" :disabled="busy" @click="pick">{{ busy ? 'Yuklanmoqda…' : 'Almaştiriş' }}</button>
        <button type="button" class="btn-ghost h-10! text-[13px]!" @click="emit('update:modelValue', null)">Öçiriş</button>
      </div>
    </template>

    <p v-if="error" class="mt-1.5 text-xs text-red-700">{{ error }}</p>
  </div>
</template>
