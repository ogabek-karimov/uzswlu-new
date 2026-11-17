<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type Paginated } from '@/lib/api'
import { SITE_URL } from '@/lib/constants'
import { useSortable } from '@/lib/sortable'
import I18nFields from '@/components/I18nFields.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Bosh sahifadagi «Tezkor xizmatlar»: kartalar shu yerda qöşiladi, tartiblanadi va yashiriladi
type Quick = { id: number; icon: string; url: string; title: I18n; text: I18n; order?: number | null; visible: boolean }

// Saytda ko‘rinadigan ikonkalar ro‘yxati backend (`apps/content/quick_links.py`) va sayt (`QuickLinks.vue`) bilan bir xil
const ICONS = [
  { value: 'lucide:message-square-text', label: 'Murojaat (xabar)' },
  { value: 'lucide:graduation-cap', label: 'Talaba (bosh kiyim)' },
  { value: 'lucide:database', label: 'Ma’lumotlar bazasi' },
  { value: 'lucide:mail', label: 'Poçta' },
  { value: 'lucide:briefcase-business', label: 'Karyera (portfel)' },
  { value: 'lucide:sprout', label: 'Maysa' },
  { value: 'lucide:book-a', label: 'Luğat (kitob)' },
  { value: 'lucide:smartphone', label: 'Mobil ilova' },
  { value: 'lucide:globe', label: 'Veb-sayt' },
  { value: 'lucide:calendar-days', label: 'Taqvim' },
  { value: 'lucide:file-text', label: 'Hujjat' },
  { value: 'lucide:library', label: 'Kutubxona' },
  { value: 'lucide:phone', label: 'Telefon' },
  { value: 'lucide:users', label: 'Odamlar' },
  { value: 'lucide:video', label: 'Video' },
  { value: 'lucide:map-pin', label: 'Manzil' },
  { value: 'lucide:award', label: 'Mukofot' },
  { value: 'lucide:life-buoy', label: 'Yordam' },
]

const items = ref<Quick[]>([])
const editing = ref<number | 'new'>('new')
const formEl = ref<HTMLElement>()
const empty = () => ({ icon: 'lucide:globe', url: '', title: {} as I18n, text: {} as I18n, visible: true })
const form = reactive(empty())
const saving = ref(false)
const error = ref('')
const loaded = ref(false)

const { bind, over } = useSortable(items, 'quick-links')

async function load() {
  const r = await api.get<Paginated<Quick>>('/quick-links', { sort: 'order', limit: 100 })
  items.value = r.docs
  loaded.value = true
}
onMounted(load)

async function edit(q: Quick | null) {
  editing.value = q ? q.id : 'new'
  error.value = ''
  Object.assign(form, empty(), q ? { icon: q.icon, url: q.url, title: { ...q.title }, text: { ...q.text }, visible: q.visible } : {})
  await nextTick()
  formEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function save() {
  const url = form.url.trim()
  if (!form.title.uz?.trim() || !url) { error.value = 'Nomi (özbekça) va havola majburiy'; return }
  if (!/^(\/(?!\/)|https?:\/\/)/.test(url)) { error.value = 'Havola «/yöl» (sayt içida) yoki «https://…» (tashqi) körinişida bölsin'; return }
  saving.value = true
  error.value = ''
  const data = { icon: form.icon, url, title: form.title, text: form.text, visible: form.visible }
  try {
    if (editing.value === 'new') await api.post('/quick-links', { ...data, order: items.value.length + 1 })
    else await api.patch(`/quick-links/${editing.value}`, data)
    await load()
    edit(null)
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

async function toggle(q: Quick) {
  await api.patch(`/quick-links/${q.id}`, { visible: !q.visible })
  await load()
}

async function remove() {
  if (typeof editing.value !== 'number' || !confirm('Karta saytdan olib taşlansinmi?')) return
  await api.del(`/quick-links/${editing.value}`)
  await load()
  edit(null)
}

const iconLabel = (v: string) => ICONS.find(i => i.value === v)?.label ?? v
const external = (u: string) => /^https?:/i.test(u)
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Tezkor xizmatlar</h1>
        <p class="mt-1.5 text-[15px] text-muted">Boş sahifadagi «Tezkor xizmatlar» kartalari. Qöşiş, tartiblaş (suriş) va yaşirış şu yerdan. Masalan, AKT luğati — Play Market havolasi bilan.</p>
      </div>
      <a :href="SITE_URL" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <form ref="formEl" class="card min-w-0 flex-[999_1_460px] px-5 py-[18px]" @submit.prevent="save">
        <div class="flex items-center justify-between gap-2">
          <h2 class="text-base font-bold">{{ editing === 'new' ? 'Karta qöşiş' : 'Kartani tahrirlaş' }}</h2>
          <button v-if="editing !== 'new'" type="button" class="text-xs font-semibold text-brand-700 underline" @click="edit(null)">+ yangi karta</button>
        </div>
        <div class="mt-3.5 grid gap-3.5">
          <div>
            <label for="ql-url" class="label">Havola</label>
            <input id="ql-url" v-model="form.url" class="field" placeholder="https://play.google.com/…  yoki  /career">
            <p class="mt-1 text-xs text-muted">Tashqi havola (https://…) yangi oynada ochiladi. Sayt içidagi sahifa uçun /yöl yozing (masalan /career).</p>
          </div>
          <I18nFields v-model="form.title" label="Nomi" layout="rows" id-prefix="ql-title" />
          <I18nFields v-model="form.text" label="Qisqa izoh" layout="rows" id-prefix="ql-text" />
          <div>
            <label for="ql-icon" class="label">Ikonka</label>
            <div class="flex items-center gap-3">
              <select id="ql-icon" v-model="form.icon" class="field flex-1">
                <option v-for="i in ICONS" :key="i.value" :value="i.value">{{ i.label }}</option>
              </select>
            </div>
          </div>
          <ToggleSwitch v-model="form.visible" label="Saytda körinadi" />
        </div>
        <p v-if="error" class="mt-3 text-sm font-semibold text-[#C5192D]" role="alert">{{ error }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button class="btn-primary h-[46px]" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
          <button v-if="editing !== 'new'" type="button" class="btn-ghost h-[46px] text-[#C5192D]" @click="remove">Öçirış</button>
        </div>
      </form>

      <section class="card min-w-0 flex-[1_1_360px] px-5 py-[18px]">
        <h2 class="text-base font-bold">Kartalar ({{ items.length }})</h2>
        <p class="mt-1 text-xs text-muted">Tartibini özgartirış uçun kartani suring.</p>
        <p v-if="loaded && !items.length" class="mt-4 text-sm text-muted">Hali karta yöq. Bo‘sh qolsa saytda blok körsatilmaydi.</p>
        <ul class="mt-3 flex flex-col gap-2">
          <li
            v-for="(q, i) in items"
            :key="q.id"
            v-bind="bind(i)"
            class="flex items-center gap-3 rounded-[14px] border px-3 py-2.5 transition"
            :class="[editing === q.id ? 'border-2 border-brand-700' : 'border-[#F0EEF6]', over === i && 'ring-2 ring-mint', !q.visible && 'opacity-60']"
          >
            <span class="cursor-grab select-none text-muted" aria-hidden="true">⠿</span>
            <button type="button" class="min-w-0 flex-1 text-left" @click="edit(q)">
              <span class="block truncate text-sm font-semibold">{{ q.title.uz }}<span v-if="external(q.url)" class="text-muted"> ↗</span></span>
              <span class="block truncate text-xs text-muted">{{ iconLabel(q.icon) }} · {{ q.url }}</span>
            </button>
            <button type="button" class="shrink-0 rounded-full border border-field px-3 py-1 text-xs font-semibold" :aria-pressed="q.visible" @click="toggle(q)">{{ q.visible ? 'Körinadi' : 'Yaşirin' }}</button>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
