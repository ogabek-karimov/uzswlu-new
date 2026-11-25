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
const snap = () => JSON.stringify(cameras.value.map(c => [c.name.trim(), cameraUrl(c.url) || c.url.trim(), c.hidden]))
const dirty = computed(() => !loading.value && snap() !== initial.value)
const shown = computed(() => cameras.value.filter(c => !c.hidden).length)
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
  <div class="flex flex-col gap-[18px] pb-24">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Onlayn kameralar</h1>
        <p class="mt-1.5 max-w-3xl text-[15px] text-muted">«Online translatsiya» sahifasidagi jonli kameralar. <b class="text-ink">Köz</b> belgisi — kamerani saytda yaşiriş/körsatiş. Havola örniga rtsp.ru bergan iframe kodini ham qöyiş mumkin.</p>
      </div>
      <a :href="`${SITE_URL}/${SLUG}`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
    </div>
    <div v-if="page && !loading" class="flex flex-wrap gap-2 text-sm">
      <span class="rounded-full bg-white px-3.5 py-1.5 font-semibold">Jami: {{ cameras.length }}</span>
      <span class="rounded-full bg-emerald-50 px-3.5 py-1.5 font-semibold text-emerald-800">Saytda: {{ shown }}</span>
      <span v-if="cameras.length - shown" class="rounded-full bg-[#FEF3DC] px-3.5 py-1.5 font-semibold text-[#B54708]">Yaşirin: {{ cameras.length - shown }}</span>
    </div>
    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</p>
    <p v-if="loading" class="text-sm text-muted">Yuklanmoqda…</p>
    <p v-else-if="!page" class="text-sm text-muted">«Online translatsiya» sahifasi topilmadi.</p>
    <div v-else class="max-w-4xl rounded-2xl bg-white p-5"><CamerasField v-model="cameras" bare /></div>

    <!-- Saqlaş paneli: faqat özgariş bölganda -->
    <Transition enter-from-class="translate-y-4 opacity-0" leave-to-class="translate-y-4 opacity-0" enter-active-class="transition duration-200" leave-active-class="transition duration-150">
      <div v-if="dirty || saved" class="fixed inset-x-4 bottom-4 z-40 mx-auto flex max-w-xl flex-wrap items-center justify-between gap-3 rounded-2xl bg-ink px-4 py-3 text-white shadow-2xl" :role="saved && !dirty ? 'status' : undefined">
        <template v-if="dirty">
          <span class="text-sm font-semibold">Saqlanmagan özgarişlar bor</span>
          <span class="flex gap-2">
            <button type="button" class="h-10 rounded-xl px-4 text-sm font-semibold text-white/80 hover:bg-white/10" :disabled="saving" @click="reset">Bekor qiliş</button>
            <button type="button" class="inline-flex h-10 items-center gap-1.5 rounded-xl bg-mint px-4 text-sm font-bold text-ink" :disabled="saving" @click="save"><Icon name="check" :size="16" />{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
          </span>
        </template>
        <span v-else class="inline-flex items-center gap-2 text-sm font-semibold"><Icon name="check" :size="16" /> Saqlandi — saytda yangilandi</span>
      </div>
    </Transition>
  </div>
</template>
