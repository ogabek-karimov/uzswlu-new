<script setup lang="ts">
// Onlayn kameralar — «Online translatsiya» sahifasidagi kameralarni tez tahrirlaş (Sahifalar → Online translatsiya bilan bir xil ma'lumot).
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import CamerasField from '@/components/CamerasField.vue'
import Icon from '@/components/Icon.vue'
import { api, type I18n, type Paginated } from '@/lib/api'
import { type Camera, camerasHtml, cameraUrl, parseCameras, stripCameras } from '@/lib/cameras'
import { LANGS, SITE_URL } from '@/lib/constants'

type PageDoc = { id: number; slug?: string | null; body?: I18n }
const SLUG = 'online-translatsiya'
const page = ref<PageDoc | null>(null)
const cameras = ref<Camera[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const saved = ref(false)
const initial = ref('[]')
// Faqat to'liq kiritilgan (nomi + tögri havola) kameralar hisoblanadi — yangi böş qator «özgariş» emas
const ready = computed(() => cameras.value.filter(c => c.name.trim() && cameraUrl(c.url)))
const snap = () => JSON.stringify(ready.value.map(c => [c.name.trim(), cameraUrl(c.url), c.hidden]))
const dirty = computed(() => !loading.value && snap() !== initial.value)
const shown = computed(() => ready.value.filter(c => !c.hidden).length)
let savedTimer: ReturnType<typeof setTimeout> | undefined
function reset() { cameras.value = JSON.parse(initial.value).map(([name, url, hidden]: [string, string, boolean]) => ({ name, url, hidden })) }
const warn = (e: BeforeUnloadEvent) => { if (dirty.value) e.preventDefault() }
onMounted(() => window.addEventListener('beforeunload', warn))
onBeforeUnmount(() => { window.removeEventListener('beforeunload', warn); clearTimeout(savedTimer) })
onBeforeRouteLeave(() => !dirty.value || confirm('Saqlanmagan özgarişlar bor. Sahifadan çiqilsinmi?'))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const docs = (await api.get<Paginated<PageDoc>>('/pages', { limit: 2000, depth: 0 })).docs
    page.value = docs.find(p => p.slug === SLUG) ?? null
    const body = page.value?.body ?? {}
    cameras.value = parseCameras(LANGS.map(l => body[l.code] ?? '').find(h => parseCameras(h).length) ?? '')
    initial.value = snap()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!page.value) return
  if (cameras.value.some(c => c.url && !cameraUrl(c.url))) { error.value = 'Havolasi noto‘ğri kamera bor (rtsp.ru/embed/… bölişi kerak).'; return }
  saving.value = true
  error.value = ''
  saved.value = false
  try {
    const body = page.value.body ?? {}
    const cams = camerasHtml(cameras.value)
    const next = Object.fromEntries(LANGS.map(l => [l.code, stripCameras(body[l.code] ?? '') + cams])) as I18n
    await api.patch(`/pages/${page.value.id}`, { body: next }, { depth: 0 })
    page.value.body = next
    cameras.value = parseCameras(cams)
    initial.value = snap()
    saved.value = true
    clearTimeout(savedTimer)
    savedTimer = setTimeout(() => (saved.value = false), 3000)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Onlayn kameralar</h1>
        <p class="mt-1.5 max-w-3xl text-[15px] text-muted">«Online translatsiya» sahifasidagi jonli kameralar. <b class="text-ink">Köz</b> belgisi — kamerani saytda yaşiriş/körsatiş. Havola örniga rtsp.ru bergan iframe kodini ham qöyiş mumkin.</p>
      </div>
      <a :href="`${SITE_URL}/${SLUG}`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
    </div>
    <div v-if="page && !loading" class="flex max-w-4xl flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-2 text-sm">
        <span class="rounded-full bg-white px-3.5 py-1.5 font-semibold">Jami: {{ ready.length }}</span>
        <span class="rounded-full bg-emerald-50 px-3.5 py-1.5 font-semibold text-emerald-800">Saytda: {{ shown }}</span>
        <span v-if="ready.length - shown" class="rounded-full bg-[#FEF3DC] px-3.5 py-1.5 font-semibold text-[#B54708]">Yaşirin: {{ ready.length - shown }}</span>
      </div>
      <div class="flex min-h-10 flex-wrap items-center gap-2">
        <span v-if="saved && !dirty" role="status" class="inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-700"><Icon name="check" :size="16" />Saqlandi</span>
        <template v-if="dirty">
          <span class="mr-1 text-sm text-muted">Saqlanmagan özgariş bor</span>
          <button type="button" class="btn-ghost h-10! text-sm!" :disabled="saving" @click="reset">Bekor qiliş</button>
          <button type="button" class="btn-primary h-10! gap-1.5 text-sm!" :disabled="saving" @click="save"><Icon name="check" :size="16" />{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
        </template>
      </div>
    </div>
    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</p>
    <p v-if="loading" class="text-sm text-muted">Yuklanmoqda…</p>
    <p v-else-if="!page" class="text-sm text-muted">«Online translatsiya» sahifasi topilmadi.</p>
    <div v-else class="max-w-4xl rounded-2xl bg-white p-5"><CamerasField v-model="cameras" bare /></div>

  </div>
</template>
