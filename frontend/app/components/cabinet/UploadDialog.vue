<script setup lang="ts">
import type { CabinetDocSection, CabinetDocument } from '#shared/types/api'

// Hujjat yuklash oynasi (oldingi saytdagi yakuniy holat): kompyuterda keng, ikki ustun —
// chapda fayl (yoki video havolasi) va 4 tildagi nom, "Yuklash" doim ko'rinadi; o'ngda qidiruv va "Yuklanganlar".
// Fayl tanlangan holda yopilsa — ogohlantirish: "Yuklash" / "Yuklamasdan yopish". O'chirish — qator ichida tasdiq bilan.
const section = defineModel<CabinetDocSection | null>('section', { required: true })
const emit = defineEmits<{ changed: [] }>()

const { t, locale } = useI18n()
const formatDate = useFormatDate()

const COLORS: Record<CabinetDocSection, string> = { cv: '#d64545', books: '#2f6fd6', presentations: '#e07a1f', articles: '#1f9d66', videos: '#e53935' }
const TYPES: Record<CabinetDocSection, string[]> = { cv: ['pdf', 'doc', 'docx'], books: ['pdf', 'doc', 'docx'], articles: ['pdf', 'doc', 'docx'], presentations: ['ppt', 'pptx', 'pdf'], videos: [] }
const MAX = 20 * 1024 * 1024
const LANGS = ['uz', 'ru', 'en', 'zh'] as const

const open = computed({ get: () => !!section.value, set: (v) => { if (!v) section.value = null } })
const isLink = computed(() => section.value === 'videos')
const color = computed(() => (section.value ? COLORS[section.value] : '#1c1548'))
const accept = computed(() => (section.value ? TYPES[section.value].map(x => `.${x}`).join(',') : ''))

// Ro'yxat
const items = ref<CabinetDocument[]>([])
const loading = ref(false)
const query = ref('')
const confirmId = ref<string | null>(null)
async function load() {
  if (!section.value) return
  loading.value = true
  try {
    items.value = await $fetch<CabinetDocument[]>(`/api/me/documents/${section.value}`)
  }
  finally {
    loading.value = false
  }
}
const titleOf = (d: CabinetDocument) => docTitleFor(d.title, locale.value)
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return q ? items.value.filter(d => LANGS.some(l => d.title[l].toLowerCase().includes(q))) : items.value
})

// Forma
const file = shallowRef<File | null>(null)
const link = ref('')
const names = reactive({ uz: '', ru: '', en: '', zh: '' })
const error = ref('')
const uploading = ref(false)
const dragOver = ref(false)
const warn = ref(false)
const fileInput = ref<HTMLInputElement>()

function reset() {
  file.value = null
  link.value = ''
  Object.assign(names, { uz: '', ru: '', en: '', zh: '' })
  error.value = ''
  warn.value = false
  query.value = ''
  confirmId.value = null
}
watch(section, (s) => {
  reset()
  items.value = []
  if (s) load()
})

function pick(f: File | undefined | null) {
  if (!f || !section.value) return
  const ext = f.name.split('.').pop()?.toLowerCase() ?? ''
  if (!TYPES[section.value].includes(ext) || f.size > MAX) {
    error.value = t('cabinet.upload.badFile')
    return
  }
  error.value = ''
  file.value = f
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  pick(e.dataTransfer?.files?.[0])
}

const pending = computed(() => (isLink.value ? !!link.value.trim() : !!file.value))

async function upload() {
  if (!section.value) return
  error.value = ''
  warn.value = false
  if (!names.uz.trim()) {
    error.value = t('cabinet.upload.nameRequired')
    return
  }
  if (isLink.value && !/^https:\/\/\S+$/i.test(link.value.trim())) {
    error.value = t('cabinet.upload.badLink')
    return
  }
  if (!isLink.value && !file.value) {
    error.value = t('cabinet.upload.badFile')
    return
  }
  const form = new FormData()
  for (const l of LANGS) form.append(`title_${l}`, names[l].trim())
  if (isLink.value) form.append('url', link.value.trim())
  else form.append('file', file.value!)
  uploading.value = true
  try {
    await $fetch(`/api/me/documents/${section.value}`, { method: 'POST', body: form })
    emit('changed')
    // Muvaffaqiyatli yuklangach oyna yopiladi (oldingi saytdagidek)
    section.value = null
  }
  catch {
    error.value = t('cabinet.upload.error')
  }
  finally {
    uploading.value = false
  }
}

async function remove(id: string) {
  if (!section.value) return
  try {
    await $fetch(`/api/me/documents/${section.value}/${encodeURIComponent(id)}`, { method: 'DELETE' })
    confirmId.value = null
    await load()
    emit('changed')
  }
  catch {
    error.value = t('cabinet.upload.error')
  }
}

// Fon, X yoki Esc: tanlangan fayl/havola bo'lsa — yopilmaydi, ogohlantirish chiqadi
function beforeClose() {
  if (uploading.value) return false
  if (warn.value) {
    warn.value = false
    return false
  }
  if (pending.value) {
    warn.value = true
    return false
  }
  return true
}
const dialog = ref<{ requestClose: () => void }>()
</script>

<template>
  <AppDialog
    ref="dialog"
    v-model:open="open"
    :title="section ? t(`cabinet.docs.sections.${section}`) : ''"
    hide-title
    :before-close="beforeClose"
    class="lg:h-[90dvh] lg:max-h-[900px] lg:max-w-[1400px]"
    body-class="flex h-full flex-col"
  >
    <template v-if="section">
      <!-- Sarlavha -->
      <div class="flex items-center gap-4 border-b border-line bg-paper px-5 py-4 sm:px-7 sm:py-5">
        <span class="grid size-13 shrink-0 place-items-center rounded-2xl text-white" :style="{ background: color }">
          <Icon name="lucide:upload" class="size-6" />
        </span>
        <span class="min-w-0 flex-1">
          <b class="block text-xl text-ink sm:text-[22px]">{{ t(`cabinet.docs.sections.${section}`) }}</b>
          <span class="text-sm text-muted">{{ isLink ? t('cabinet.upload.linkRules') : t('cabinet.upload.rules', { types: TYPES[section].map(x => x.toUpperCase()).join(', ') }) }}</span>
        </span>
        <button type="button" :aria-label="t('cabinet.close')" class="grid size-11 shrink-0 place-items-center rounded-full text-ink transition-colors hover:bg-white" @click="dialog?.requestClose()">
          <Icon name="lucide:x" class="size-6" />
        </button>
      </div>

      <div class="relative grid min-h-0 flex-1 gap-7 p-5 sm:px-7 lg:grid-cols-[5fr_7fr]">
        <!-- Chap: yuklash -->
        <form class="flex min-h-0 flex-col" @submit.prevent="upload">
          <div class="min-h-0 flex-1 overflow-y-auto px-1 pb-2">
            <label
              v-if="!isLink"
              class="flex cursor-pointer flex-col items-center rounded-[20px] border-2 border-dashed px-6 py-6 text-center transition-colors"
              :class="dragOver || file ? 'bg-paper' : 'border-[#cfcbd8] bg-paper hover:border-accent-500'"
              :style="dragOver || file ? { borderColor: color } : undefined"
              @dragover.prevent="dragOver = true"
              @dragleave="dragOver = false"
              @drop.prevent="onDrop"
            >
              <input ref="fileInput" type="file" :accept="accept" class="sr-only" @change="pick(($event.target as HTMLInputElement).files?.[0])">
              <Icon :name="file ? 'lucide:file-check' : 'lucide:cloud-upload'" class="size-10" :style="{ color }" />
              <b class="mt-2 block text-base break-all text-ink">{{ file ? file.name : t('cabinet.upload.drop') }}</b>
              <span class="mt-1 block text-[13px] text-muted">{{ file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : t('cabinet.upload.dropSub') }}</span>
            </label>
            <label v-else class="block text-[13px] text-muted">
              {{ t('cabinet.upload.link') }}
              <input v-model="link" type="url" placeholder="https://youtube.com/watch?v=…" class="mt-1.5 block h-12 w-full rounded-[14px] border border-line bg-white px-3.5 text-[15px] text-ink outline-none focus:border-accent-600 focus:ring-4 focus:ring-accent-600/15">
            </label>

            <label v-for="l in LANGS" :key="l" class="mt-3 block text-[13px] text-muted">
              {{ t('cabinet.upload.name', { lang: l === 'zh' ? 'cn' : l }) }}
              <input
                v-model="names[l]"
                maxlength="255"
                :required="l === 'uz'"
                :placeholder="l === 'zh' ? t('cabinet.upload.zhHint') : ''"
                class="mt-1.5 block h-12 w-full rounded-[14px] border border-line bg-white px-3.5 text-[15px] text-ink outline-none focus:border-accent-600 focus:ring-4 focus:ring-accent-600/15"
              >
            </label>
            <p v-if="error" role="alert" class="mt-3 rounded-xl bg-[#fdecec] px-3.5 py-2.5 text-sm text-[#8e1b1b]">{{ error }}</p>
          </div>
          <!-- "Yuklash" pastda qotirilgan — scroll'siz ko'rinadi -->
          <button
            type="submit"
            :disabled="uploading"
            class="mt-3 flex h-13 shrink-0 items-center justify-center gap-2 rounded-2xl text-base font-bold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            :style="{ background: color }"
          >
            <Icon :name="uploading ? 'lucide:loader-circle' : 'lucide:upload'" class="size-[18px]" :class="uploading && 'animate-spin'" />
            {{ uploading ? t('cabinet.upload.uploading') : t('cabinet.upload.submit') }}
          </button>
        </form>

        <!-- O'ng: qidiruv, keyin "Yuklanganlar" -->
        <div class="flex min-h-0 flex-col">
          <label class="flex h-12.5 shrink-0 items-center gap-2.5 rounded-[14px] border border-line bg-paper px-4 focus-within:border-accent-600">
            <Icon name="lucide:search" class="size-[18px] text-muted" />
            <span class="sr-only">{{ t('cabinet.upload.search') }}</span>
            <input v-model="query" type="search" autocomplete="off" :placeholder="t('cabinet.upload.search')" class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none">
          </label>
          <p class="mt-4.5 flex shrink-0 items-center gap-2.5 text-xs font-bold tracking-[0.18em] text-muted uppercase">
            {{ t('cabinet.upload.uploaded') }}
            <span class="rounded-full bg-brand-50 px-2.5 py-0.5 tracking-normal text-brand-700">{{ items.length }}</span>
          </p>
          <ul class="mt-3 grid min-h-0 flex-1 content-start gap-2.5 overflow-y-auto pr-1" :aria-busy="loading">
            <li v-for="d in filtered" :key="d.id" class="rounded-2xl border p-3.5 transition-colors" :class="confirmId === d.id ? 'border-[#f5c2c2] bg-[#fffafa]' : 'border-line bg-white'">
              <span class="flex items-center gap-3">
                <Icon :name="isLink ? 'lucide:link' : 'lucide:file-text'" class="size-5 shrink-0 text-muted" />
                <span class="min-w-0 flex-1">
                  <b class="line-clamp-3 block text-ink">{{ titleOf(d) }}</b>
                  <span class="text-[13px] text-muted">{{ formatDate(d.createdAt) }}</span>
                </span>
                <a :href="d.url" target="_blank" rel="noopener" class="inline-flex h-9 shrink-0 items-center rounded-[10px] border border-line px-3.5 text-[13px] font-semibold text-ink transition-colors hover:border-accent-500">{{ t('cabinet.upload.open') }}</a>
                <button type="button" class="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-[10px] border border-[#f5c2c2] bg-white px-3.5 text-[13px] font-semibold text-[#c62828] transition-colors hover:bg-[#fdecec]" @click="confirmId = d.id">
                  <Icon name="lucide:trash-2" class="size-3.5" />
                  {{ t('cabinet.remove') }}
                </button>
              </span>
              <span v-if="confirmId === d.id" class="mt-3 block rounded-xl bg-[#fdecec] px-3.5 py-3 text-sm text-[#8e1b1b]">
                <b>{{ t('cabinet.upload.deleteTitle') }}</b> {{ t('cabinet.upload.deleteText') }}
                <span class="mt-2.5 flex gap-2">
                  <button type="button" class="h-9 rounded-[10px] bg-[#c62828] px-3.5 text-[13px] font-bold text-white" @click="remove(d.id)">{{ t('cabinet.upload.deleteYes') }}</button>
                  <button type="button" class="h-9 rounded-[10px] border border-line bg-white px-3.5 text-[13px] font-semibold text-ink" @click="confirmId = null">{{ t('cabinet.cancel') }}</button>
                </span>
              </span>
            </li>
            <li v-if="!loading && !filtered.length" class="px-1 text-muted">{{ items.length ? t('cabinet.upload.notFound') : t('cabinet.upload.empty') }}</li>
          </ul>
        </div>

        <!-- Fayl tanlangan holda yopishga urinsa: faqat ikki tugma -->
        <div v-if="warn" class="absolute inset-0 z-10 grid place-items-center bg-white/85 p-4">
          <div role="alertdialog" class="w-full max-w-[420px] rounded-[22px] border border-line bg-white p-6 text-center shadow-[0_30px_60px_-30px_rgba(17,12,46,0.5)]">
            <span class="mx-auto grid size-13 place-items-center rounded-2xl bg-[#fff6db] text-[#a66b00]"><Icon name="lucide:triangle-alert" class="size-6" /></span>
            <p class="mt-3 text-[17px] font-bold">{{ isLink ? t('cabinet.upload.warnLink') : t('cabinet.upload.warnFile') }}</p>
            <div class="mt-4 grid grid-cols-2 gap-2.5">
              <button type="button" class="h-12 rounded-[14px] font-bold text-white" :style="{ background: color }" @click="upload">{{ t('cabinet.upload.submit') }}</button>
              <button type="button" class="h-12 rounded-[14px] border border-line bg-white font-semibold text-ink" @click="warn = false; reset(); section = null">{{ t('cabinet.upload.closeAnyway') }}</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </AppDialog>
</template>
