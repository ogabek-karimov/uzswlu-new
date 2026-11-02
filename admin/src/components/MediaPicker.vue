<script setup lang="ts">
import { ref, watch } from 'vue'
import { api, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { fileSize, relative } from '@/lib/format'
import Icon from './Icon.vue'

// "Serverdan tanlash": serverga yuklangan fayllar (media kutubxona) — eski admin'dagi "Browse Server" o'rnida.
// Ro'yxat, qidiruv, PDF/rasm filtri va kompyuterdan yangi fayl yuklash.
const props = defineProps<{ open: boolean; kind?: 'pdf' | 'image' | 'all' }>()
const emit = defineEmits<{ pick: [MediaDoc]; close: [] }>()

const filter = ref<'pdf' | 'image' | 'all'>('all')
const q = ref('')
const items = ref<MediaDoc[]>([])
const page = ref(1)
const more = ref(false)
const loading = ref(false)
const uploading = ref(false)
const selected = ref<MediaDoc | null>(null)
const input = ref<HTMLInputElement>()

async function load(reset = true) {
  if (reset) { page.value = 1; items.value = [] }
  loading.value = true
  const and: Record<string, unknown>[] = []
  if (filter.value === 'pdf') and.push({ mimeType: { equals: 'application/pdf' } })
  if (filter.value === 'image') and.push({ mimeType: { like: 'image/' } })
  if (q.value.trim()) and.push({ filename: { like: q.value.trim() } })
  try {
    const res = await api.get<Paginated<MediaDoc & { createdAt?: string }>>('/media', { where: and.length ? { and } : undefined, sort: '-createdAt', limit: 30, page: page.value, depth: 0 })
    items.value = reset ? res.docs : [...items.value, ...res.docs]
    more.value = res.page < res.totalPages
  }
  finally {
    loading.value = false
  }
}

watch(() => props.open, (o) => {
  if (!o) return
  filter.value = props.kind ?? 'all'
  selected.value = null
  load()
})
watch(filter, () => load())
let timer: ReturnType<typeof setTimeout> | undefined
watch(q, () => { clearTimeout(timer); timer = setTimeout(() => load(), 300) })

async function onFile(e: Event) {
  const files = [...((e.target as HTMLInputElement).files ?? [])]
  uploading.value = true
  try {
    for (const f of files) {
      const media = await uploadMedia(f, { folder: f.type === 'application/pdf' ? 'docs' : 'posts' })
      items.value = [media, ...items.value]
      selected.value = media
    }
  }
  finally {
    uploading.value = false
    if (input.value) input.value.value = ''
  }
}

const isPdf = (m: MediaDoc) => m.mimeType === 'application/pdf'
const thumb = (m: MediaDoc) => m.sizes?.thumb?.url ?? m.url ?? ''
function choose() {
  if (selected.value) emit('pick', selected.value)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-[70] grid place-items-center bg-night/55 p-4" @click.self="emit('close')" @keydown.esc="emit('close')">
      <section role="dialog" aria-modal="true" aria-label="Serverdagi fayllar" class="flex max-h-[86dvh] w-full max-w-[860px] flex-col overflow-hidden rounded-[22px] bg-white shadow-2xl">
        <header class="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <h2 class="text-base font-bold">Serverdagi fayllar</h2>
          <button type="button" aria-label="Yopiş" class="grid size-9 place-items-center rounded-full bg-canvas text-muted" @click="emit('close')"><Icon name="x" :size="16" /></button>
        </header>

        <div class="flex flex-wrap items-center gap-2 px-5 py-3">
          <label class="flex h-10 min-w-[200px] flex-1 items-center gap-2 rounded-[10px] border border-field px-3 text-muted">
            <Icon name="search" :size="15" />
            <input v-model="q" aria-label="Fayl qidiriş" placeholder="Fayl nomi böyiça qidiriş…" class="min-w-0 flex-1 bg-transparent text-[13px] outline-none">
          </label>
          <div role="tablist" aria-label="Fayl turi" class="flex gap-1">
            <button v-for="f in ([['all', 'Hammasi'], ['pdf', 'PDF'], ['image', 'Rasmlar']] as const)" :key="f[0]" type="button" role="tab" :aria-selected="filter === f[0]" class="h-9 rounded-full px-3 text-xs font-semibold" :class="filter === f[0] ? 'bg-ink text-white' : 'border border-field text-[#3D3958]'" @click="filter = f[0]">{{ f[1] }}</button>
          </div>
          <input ref="input" type="file" multiple class="hidden" :accept="filter === 'pdf' ? 'application/pdf' : filter === 'image' ? 'image/*' : 'application/pdf,image/*'" @change="onFile">
          <button type="button" class="h-9 rounded-[10px] border border-dashed border-[#C9C2F0] px-3 text-xs font-semibold text-brand-700" :disabled="uploading" @click="input?.click()">{{ uploading ? 'Yuklanmoqda…' : '+ Kompyuterdan yuklaş' }}</button>
        </div>

        <div class="min-h-[240px] flex-1 overflow-y-auto px-5 pb-4">
          <p v-if="!loading && !items.length" class="py-10 text-center text-sm text-muted">Fayl topilmadi. Kompyuterdan yuklang.</p>
          <ul class="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <li v-for="m in items" :key="m.id">
              <button
                type="button" :aria-pressed="selected?.id === m.id" class="flex w-full items-center gap-2.5 rounded-xl p-2 text-left text-xs"
                :class="selected?.id === m.id ? 'border-2 border-brand-700 bg-brand-50' : 'border border-line hover:border-brand-300'"
                @click="selected = m" @dblclick="selected = m; choose()"
              >
                <span v-if="isPdf(m)" class="grid h-10 w-8 shrink-0 place-items-center rounded-md bg-red-50 text-[9px] font-extrabold text-red-700">PDF</span>
                <img v-else :src="thumb(m)" alt="" class="size-10 shrink-0 rounded-md object-cover">
                <span class="min-w-0"><b class="block truncate">{{ m.filename }}</b><span class="text-subtle">{{ fileSize(m.filesize) }}<template v-if="(m as any).createdAt"> · {{ relative((m as any).createdAt) }}</template></span></span>
              </button>
            </li>
          </ul>
          <div v-if="more" class="mt-3 text-center"><button type="button" class="btn-ghost h-9!" :disabled="loading" @click="page++; load(false)">Yana körsatiş</button></div>
        </div>

        <footer class="flex flex-wrap items-center justify-between gap-2.5 border-t border-line px-5 py-3.5">
          <span class="min-w-0 truncate text-xs text-muted">{{ selected ? selected.filename : 'Faylni tanlang (ikki marta bossangiz ham böladi)' }}</span>
          <span class="flex gap-2">
            <button type="button" class="btn-ghost h-10!" @click="emit('close')">Bekor qiliş</button>
            <button type="button" class="btn-primary h-10!" :disabled="!selected" @click="choose">Tanlaş</button>
          </span>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
