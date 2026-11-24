<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { api } from '@/lib/api'
import Icon from './Icon.vue'

// HEMIS xodimini ism (yoki ID) bo'yicha qidirib tanlash — HEMIS ID qo'lda yozilmaydi, xato/mavjud bo'lmagan raqam kiritilmaydi.
// Ro'yxat — admin panelning /panel/hemis javobi (HEMIS nusxasi); bir marta yuklanadi.
type Staff = { id: string; name: string; employments: { department: { name?: string } | string; position: string }[] }
const props = defineProps<{ open: boolean; taken?: string[]; current?: string | null }>()
const emit = defineEmits<{ 'update:open': [boolean]; pick: [{ id: string; name: string } | null] }>()

let cache: Staff[] | null = null
const staff = ref<Staff[]>([])
const q = ref('')
const loading = ref(false)
const error = ref('')
const input = ref<HTMLInputElement>()

watch(() => props.open, async (o) => {
  if (!o) return
  q.value = ''
  await nextTick()
  input.value?.focus()
  if (cache) { staff.value = cache; return }
  loading.value = true
  try {
    cache = (await api.get<{ staff: Staff[] }>('/panel/hemis')).staff
    staff.value = cache
  }
  catch { error.value = 'HEMIS ro‘yxatini yuklab bölmadi' }
  finally { loading.value = false }
})

const fold = (s: string) => s.toLowerCase().replace(/[ʻʼ'‘’`]/g, '').replace(/ö/g, 'o').replace(/ğ/g, 'g').replace(/ş/g, 'sh').replace(/ç/g, 'ch')
const position = (s: Staff) => {
  const e = s.employments[0]
  if (!e) return ''
  const dep = typeof e.department === 'string' ? e.department : e.department?.name ?? ''
  return [e.position, dep].filter(Boolean).join(' · ')
}
const found = computed(() => {
  const words = fold(q.value.trim()).split(/\s+/).filter(Boolean)
  if (!words.length) return staff.value.slice(0, 30)
  return staff.value.filter(s => words.every(w => fold(`${s.name} ${s.id}`).includes(w))).slice(0, 30)
})
const close = () => emit('update:open', false)
function choose(s: Staff | null) {
  emit('pick', s ? { id: s.id, name: s.name } : null)
  close()
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 grid place-items-center bg-night/40 p-4" @click.self="close" @keydown.esc="close">
    <div role="dialog" aria-modal="true" aria-label="HEMIS xodimini tanlaş" class="flex max-h-[80vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
      <div class="flex items-center gap-3 border-b border-line px-4 py-3">
        <Icon name="search" :size="16" class="text-muted" />
        <input ref="input" v-model="q" class="min-w-0 flex-1 text-sm outline-none" placeholder="Familiya, ism yoki HEMIS ID…" aria-label="HEMIS xodimini qidiriş">
        <button type="button" aria-label="Yopiş" class="grid size-8 place-items-center rounded-full text-muted hover:bg-canvas" @click="close"><Icon name="x" :size="15" /></button>
      </div>
      <p v-if="error" class="px-4 py-3 text-sm text-red-700">{{ error }}</p>
      <p v-else-if="loading" class="px-4 py-3 text-sm text-muted">Yuklanmoqda…</p>
      <ul v-else class="overflow-y-auto py-1">
        <li v-for="s in found" :key="s.id">
          <button
            type="button" :disabled="taken?.includes(s.id) && s.id !== current"
            class="flex w-full items-center gap-3 px-4 py-2.5 text-left hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-45"
            :class="s.id === current && 'bg-brand-50'" @click="choose(s)"
          >
            <span class="min-w-0 flex-1"><b class="block truncate text-sm">{{ s.name }}</b><span class="block truncate text-xs text-muted">{{ position(s) || '—' }}</span></span>
            <span class="shrink-0 text-right text-xs tabular-nums text-subtle">ID {{ s.id }}<span v-if="taken?.includes(s.id) && s.id !== current" class="block">band</span></span>
          </button>
        </li>
        <li v-if="!found.length" class="px-4 py-6 text-center text-sm text-muted">HEMIS’da topilmadi</li>
      </ul>
      <div v-if="current" class="border-t border-line px-4 py-2.5 text-right">
        <button type="button" class="text-xs font-semibold text-red-700 hover:underline" @click="choose(null)">HEMIS bilan boğlanişni olib taşlaş</button>
      </div>
    </div>
  </div>
</template>
