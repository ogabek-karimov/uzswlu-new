<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { auth } from '@/lib/auth'
import { dateTime, fileSize } from '@/lib/format'
import { MEDIA_BASE } from '@/lib/constants'
import Icon from '@/components/Icon.vue'
import I18nFields from '@/components/I18nFields.vue'

// Media kutubxona: rasm, PDF va audio. Ishlatilayotgan faylni o'chirib bo'lmaydi.
type Media = MediaDoc & { folder?: string | null; originalSize?: number | null; createdAt?: string; uploadedBy?: { name?: string } | number | null }
type Stats = { total: number; folders: Record<string, number>; kinds: Record<'image' | 'pdf' | 'audio', number>; used: number; saved: number; disk: { total: number; free: number } | null }

const FOLDERS = [
  { key: 'all', label: 'Barça fayllar' },
  { key: 'posts', label: 'Yangiliklar' },
  { key: 'carousel', label: 'Karusel' },
  { key: 'docs', label: 'Hujjatlar (PDF)' },
  { key: 'staff', label: 'Xodimlar rasmlari' },
  { key: 'logos', label: 'Logotiplar' },
  { key: 'audio', label: 'Audio' },
]

const stats = ref<Stats | null>(null)
const folder = ref('all')
const kind = ref<'all' | 'image' | 'pdf' | 'audio'>('all')
const sort = ref<'new' | 'big' | 'unused'>('new')
const q = ref('')
const items = ref<Media[]>([])
const page = ref(1)
const more = ref(false)
const loading = ref(false)
const sel = ref<Media | null>(null)
const used = ref<string[] | null>(null)
const alt = ref<I18n>({})
const altSaved = ref(false)
const uploading = ref(0)
const dragOver = ref(false)
const input = ref<HTMLInputElement>()
const error = ref('')
const canDelete = computed(() => auth.user.value?.role === 'superadmin')

async function loadStats() {
  stats.value = await api.get<Stats>('/panel/media-stats')
}

async function load(reset = true) {
  if (reset) { page.value = 1 }
  loading.value = true
  const and: Record<string, unknown>[] = []
  if (folder.value !== 'all') and.push({ folder: { equals: folder.value } })
  if (kind.value === 'image') and.push({ mimeType: { like: 'image/' } })
  if (kind.value === 'pdf') and.push({ mimeType: { equals: 'application/pdf' } })
  if (kind.value === 'audio') and.push({ mimeType: { like: 'audio/' } })
  if (q.value.trim()) and.push({ or: [{ filename: { like: q.value.trim() } }, { 'alt.uz': { like: q.value.trim() } }] })
  if (sort.value === 'unused') {
    const { ids } = await api.get<{ ids: number[] }>('/panel/media-used')
    if (ids.length) and.push({ id: { not_in: ids } })
  }
  try {
    const res = await api.get<Paginated<Media>>('/media', { where: and.length ? { and } : undefined, sort: sort.value === 'big' ? '-filesize' : '-createdAt', limit: 40, page: page.value, depth: 1 })
    items.value = reset ? res.docs : [...items.value, ...res.docs]
    more.value = res.page < res.totalPages
    if (reset && !items.value.some(m => m.id === sel.value?.id)) select(items.value[0] ?? null)
  }
  finally {
    loading.value = false
  }
}

onMounted(() => { loadStats(); load() })
watch([folder, kind, sort], () => load())
let timer: ReturnType<typeof setTimeout> | undefined
watch(q, () => { clearTimeout(timer); timer = setTimeout(() => load(), 300) })

async function select(m: Media | null) {
  sel.value = m
  used.value = null
  altSaved.value = false
  error.value = ''
  alt.value = { ...(m?.alt ?? {}) }
  if (m) used.value = (await api.get<{ used: string[] }>(`/panel/media-usage/${m.id}`)).used
}

async function upload(files: File[]) {
  error.value = ''
  for (const f of files) {
    if (f.size > (f.type === 'application/pdf' ? 50 : 20) * 1024 * 1024) { error.value = `${f.name}: juda katta (rasm 20 MB gaça, PDF 50 MB gaça)`; continue }
    uploading.value++
    try {
      const target = folder.value !== 'all' ? folder.value : f.type === 'application/pdf' ? 'docs' : f.type.startsWith('audio/') ? 'audio' : 'posts'
      const m = await uploadMedia(f, { folder: target })
      items.value = [m as Media, ...items.value]
      select(m as Media)
    }
    catch (e) {
      error.value = `${f.name}: ${(e as Error).message}`
    }
    finally {
      uploading.value--
    }
  }
  loadStats()
}
function onPick(e: Event) {
  upload([...((e.target as HTMLInputElement).files ?? [])])
  if (input.value) input.value.value = ''
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  upload([...(e.dataTransfer?.files ?? [])])
}

async function saveAlt() {
  if (!sel.value) return
  const res = await api.patch<{ doc: Media }>(`/media/${sel.value.id}`, { alt: alt.value }, { depth: 1 })
  Object.assign(sel.value, { alt: res.doc.alt })
  altSaved.value = true
}

async function copyLink() {
  if (!sel.value?.url) return
  await navigator.clipboard.writeText(new URL(sel.value.url, MEDIA_BASE).href)
  copied.value = true
  setTimeout(() => (copied.value = false), 1800)
}
const copied = ref(false)

async function remove() {
  if (!sel.value || used.value?.length || !confirm(`${sel.value.filename} butunlay öçirilsinmi? Bu amalni qaytarib bölmaydi.`)) return
  try {
    await api.del(`/media/${sel.value.id}`)
    items.value = items.value.filter(m => m.id !== sel.value?.id)
    select(items.value[0] ?? null)
    loadStats()
  }
  catch (e) {
    error.value = (e as Error).message
  }
}

const isImage = (m: Media) => !!m.mimeType?.startsWith('image/')
const kindLabel = (m: Media) => (m.mimeType === 'application/pdf' ? 'PDF' : m.mimeType?.startsWith('audio/') ? 'MP3' : (m.filename?.split('.').pop() ?? '').toUpperCase())
const kindBg = (m: Media) => (m.mimeType === 'application/pdf' ? '#C5192D' : m.mimeType?.startsWith('audio/') ? '#0E7A5A' : '#382B85')
const thumb = (m: Media) => m.sizes?.thumb?.url ?? m.url ?? ''
const uploader = (m: Media) => (m.uploadedBy && typeof m.uploadedBy === 'object' ? m.uploadedBy.name : null)
const metaLine = (m: Media) => [m.width && m.height ? `${m.width} × ${m.height}` : null, m.createdAt ? dateTime(m.createdAt).slice(0, 10) : null, uploader(m)].filter(Boolean).join(' · ')
const saving = (m: Media) => {
  if (m.originalSize && m.filesize && m.originalSize > m.filesize * 1.05) return `Asl fayl ${fileSize(m.originalSize)} → ${isImage(m) ? 'WebP ' : ''}${fileSize(m.filesize)} (${Math.round((1 - m.filesize / m.originalSize) * 100)}% kiçik)`
  if (isImage(m)) return 'WebP formatida saqlangan'
  return `${kindLabel(m)} — özgarişsiz saqlangan`
}
const gb = (b: number) => `${(b / 1024 ** 3).toFixed(1).replace('.', ',')} GB`
const diskPct = computed(() => (stats.value?.disk ? Math.min(100, Math.round(((stats.value.disk.total - stats.value.disk.free) / stats.value.disk.total) * 100)) : 0))
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Media kutubxona</h1>
        <p class="mt-1.5 text-[15px] text-muted">Rasm, PDF va audio fayllar. Katta rasm yuklansa ham sayt sekinlaşmaydi — öz-özidan kiçraytiriladi.</p>
      </div>
      <input ref="input" type="file" multiple class="hidden" accept="image/*,application/pdf,audio/mpeg" @change="onPick">
      <button type="button" class="btn-primary h-[46px]" :disabled="uploading > 0" @click="input?.click()"><Icon name="upload" :size="16" />{{ uploading ? `Yuklanmoqda (${uploading})…` : 'Fayl yuklaş' }}</button>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <!-- Papkalar -->
      <aside class="card min-w-0 flex-[1_1_220px] p-3 xl:max-w-[250px]">
        <nav aria-label="Papkalar" class="flex flex-col gap-0.5">
          <button
            v-for="f in FOLDERS" :key="f.key" type="button" :aria-current="folder === f.key ? 'page' : undefined"
            class="flex h-10 items-center gap-2.5 rounded-[10px] px-2.5 text-[13px]" :class="folder === f.key ? 'bg-brand-50 font-semibold' : 'font-medium'" @click="folder = f.key"
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" :stroke="folder === f.key ? '#382B85' : '#8C88A0'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /></svg>
            <span class="flex-1 text-left">{{ f.label }}</span>
            <span class="text-xs text-subtle">{{ f.key === 'all' ? stats?.total ?? '' : stats?.folders[f.key] ?? 0 }}</span>
          </button>
        </nav>
        <div v-if="stats" class="mx-1.5 mt-3.5 mb-1 border-t border-[#F0EEF6] pt-3.5">
          <p class="flex justify-between text-xs text-muted"><span>Media fayllar</span><b class="text-ink">{{ fileSize(stats.used) || '0 KB' }}</b></p>
          <template v-if="stats.disk">
            <p class="mt-2 flex justify-between text-xs text-muted"><span>Disk</span><b class="text-ink">{{ gb(stats.disk.total - stats.disk.free) }} / {{ gb(stats.disk.total) }}</b></p>
            <div class="mt-2 h-2 overflow-hidden rounded-full bg-[#F0EEF6]" role="progressbar" :aria-valuenow="diskPct" aria-valuemin="0" aria-valuemax="100" aria-label="Disk bandligi"><div class="h-full rounded-full bg-brand-700" :style="{ width: `${diskPct}%` }" /></div>
          </template>
          <p v-if="stats.saved" class="mt-2 text-[11px] leading-normal text-subtle">WebP tufayli {{ fileSize(stats.saved) }} tejaldi</p>
        </div>
      </aside>

      <!-- Fayllar -->
      <section class="card min-w-0 flex-[999_1_460px] p-4">
        <div class="flex flex-wrap items-center gap-2.5">
          <label class="flex h-10 min-w-[200px] flex-[1_1_220px] items-center gap-2 rounded-[10px] border border-field px-3 text-muted">
            <Icon name="search" :size="15" />
            <input v-model="q" aria-label="Fayl qidiriş" placeholder="Fayl nomi yoki tavsifi…" class="min-w-0 flex-1 bg-transparent text-[13px] outline-none">
          </label>
          <select v-model="kind" class="field h-10! w-auto!" aria-label="Turi"><option value="all">Barça turlar</option><option value="image">Rasmlar</option><option value="pdf">PDF</option><option value="audio">Audio</option></select>
          <select v-model="sort" class="field h-10! w-auto!" aria-label="Saralaş"><option value="new">Yangilari birinçi</option><option value="big">Kattalari birinçi</option><option value="unused">Işlatilmaganlar</option></select>
        </div>
        <div
          class="mt-3.5 rounded-[14px] border-2 border-dashed p-[18px] text-center text-[13px] text-muted transition"
          :class="dragOver ? 'border-brand-700 bg-brand-50' : 'border-[#D3CFE3] bg-[#FAF9FD]'"
          @dragover.prevent="dragOver = true" @dragleave="dragOver = false" @drop.prevent="onDrop"
        >Fayllarni şu yerga tortib qöying yoki <button type="button" class="font-bold text-brand-700" @click="input?.click()">kompyuterdan tanlang</button> · rasm 20 MB gaça, PDF 50 MB gaça</div>
        <p v-if="error" class="mt-3 rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <p v-if="!loading && !items.length" class="py-10 text-center text-sm text-muted">Fayl topilmadi.</p>
        <ul class="mt-3.5 grid grid-cols-2 gap-3 sm:grid-cols-3 2xl:grid-cols-4">
          <li v-for="m in items" :key="m.id">
            <button type="button" class="block w-full rounded-[14px] p-2 text-left transition hover:-translate-y-0.5" :class="sel?.id === m.id ? 'border-2 border-brand-700 bg-brand-50' : 'border border-[#F0EEF6] bg-white'" :aria-pressed="sel?.id === m.id" @click="select(m)">
              <span class="grid aspect-[4/3] place-items-center overflow-hidden rounded-[10px] text-[13px] font-extrabold text-white" :style="{ background: kindBg(m) }">
                <img v-if="isImage(m)" :src="thumb(m)" alt="" class="size-full object-cover" loading="lazy">
                <template v-else>{{ kindLabel(m) }}</template>
              </span>
              <span class="mt-2 block truncate text-xs font-semibold">{{ m.filename }}</span>
              <span class="block text-[11px] text-subtle">{{ fileSize(m.filesize) }}</span>
            </button>
          </li>
        </ul>
        <div v-if="more" class="mt-4 text-center"><button type="button" class="btn-ghost h-10!" :disabled="loading" @click="page++; load(false)">{{ loading ? 'Yuklanmoqda…' : 'Yana körsatiş' }}</button></div>
      </section>

      <!-- Tanlangan fayl -->
      <aside v-if="sel" class="card flex min-w-0 flex-[1_1_300px] flex-col gap-3 p-4 xl:max-w-[340px]">
        <div class="grid aspect-[4/3] place-items-center overflow-hidden rounded-xl font-extrabold text-white" :style="{ background: kindBg(sel) }">
          <img v-if="isImage(sel)" :src="sel.sizes?.card?.url ?? sel.url ?? ''" :alt="sel.alt?.uz ?? ''" class="size-full object-contain">
          <template v-else>{{ kindLabel(sel) }}</template>
        </div>
        <audio v-if="sel.mimeType?.startsWith('audio/') && sel.url" :src="sel.url" controls class="w-full" />
        <div>
          <p class="text-[15px] font-bold break-all">{{ sel.filename }}</p>
          <p class="mt-1 text-xs text-muted">{{ metaLine(sel) }}</p>
        </div>
        <div class="rounded-xl bg-[#DDFBF0] px-3 py-2.5 text-xs leading-normal text-[#0B5A43]">{{ saving(sel) }}</div>
        <form v-if="isImage(sel)" class="flex flex-col gap-2" @submit.prevent="saveAlt">
          <I18nFields v-model="alt" label="Tavsif (alt matn)" layout="rows" />
          <span class="flex items-center justify-end gap-2"><span v-if="altSaved" class="text-xs font-semibold text-mint-text">Saqlandi ✓</span><button type="submit" class="btn-ghost h-9! text-xs!">Tavsifni saqlaş</button></span>
        </form>
        <div>
          <span class="label">Qayerda işlatilgan</span>
          <p v-if="used === null" class="text-[13px] text-subtle">Tekşirilmoqda…</p>
          <ul v-else class="flex flex-col gap-1.5 text-[13px]">
            <li v-if="!used.length" class="rounded-[10px] bg-canvas px-2.5 py-2 text-muted">Hali heç qayerda işlatilmagan</li>
            <li v-for="u in used" :key="u" class="rounded-[10px] bg-canvas px-2.5 py-2">{{ u }}</li>
          </ul>
        </div>
        <div class="flex gap-2">
          <button type="button" class="btn-ghost h-10! flex-1 text-[13px]!" @click="copyLink">{{ copied ? 'Nusxalandi ✓' : 'Havolani nusxalaş' }}</button>
          <a v-if="sel.url" :href="sel.url" target="_blank" rel="noopener" class="btn-ghost h-10! px-3! text-[13px]!" aria-label="Faylni oçiş"><Icon name="external" :size="15" /></a>
          <button
            v-if="canDelete" type="button" class="btn h-10! px-3.5! text-[13px]!"
            :class="used?.length ? 'cursor-not-allowed border border-line bg-canvas text-[#9B97AE]' : 'border border-[#F6C9C4] bg-white text-[#B42318] hover:bg-red-50'"
            :aria-disabled="!!used?.length" :title="used?.length ? 'Işlatilayotgan faylni öçirib bölmaydi — avval sahifalardan olib taşlang' : 'Öçiriş'" @click="remove"
          >Öçiriş</button>
        </div>
      </aside>
    </div>
  </div>
</template>
