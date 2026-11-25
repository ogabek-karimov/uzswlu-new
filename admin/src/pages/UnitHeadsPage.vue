<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated } from '@/lib/api'
import { SITE_URL } from '@/lib/constants'
import { mediaUrl } from '@/lib/posts'
import { useSortable } from '@/lib/sortable'
import Icon from '@/components/Icon.vue'
import I18nFields from '@/components/I18nFields.vue'
import ImageField from '@/components/ImageField.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Bo'limlar sahifasi (/bolimlar) kartalari: bo'lim/markaz rahbari — surat, F.I.Sh., lavozim, telefon, bo'lim sahifasiga havola
type Unit = { id: number; name: string; position: I18n; photo?: MediaDoc | number | null; phone: string; ext: string; email: string; url: string; order?: number | null; visible: boolean }

const items = ref<Unit[]>([])
const editing = ref<number | 'new' | null>(null)
const formEl = ref<HTMLElement>()
const empty = () => ({ name: '', position: {} as I18n, photo: null as MediaDoc | null, phone: '71-230-13-62', ext: '', email: '', url: '', visible: true })
const form = reactive(empty())
const saving = ref(false)
const error = ref('')
const query = ref('')

const { bind, over } = useSortable(items, 'unit-heads')

async function load() {
  const r = await api.get<Paginated<Unit>>('/unit-heads', { sort: 'order', limit: 500, depth: 1 })
  items.value = r.docs
}
onMounted(load)

const shown = computed(() => {
  const q = query.value.trim().toLowerCase()
  return items.value.map((u, i) => ({ u, i })).filter(({ u }) => !q || `${u.name} ${u.position.uz ?? ''}`.toLowerCase().includes(q))
})

// Kirganda tahrir oynasi yopiq: faqat «Yangi …» yoki röyxatdagi element bosilganda oçiladi; saqlangaç / öçirilgaç yana yopiladi
function close() {
  editing.value = null
  error.value = ''
}

async function edit(u: Unit | null) {
  editing.value = u ? u.id : 'new'
  error.value = ''
  Object.assign(form, empty(), u ? { name: u.name, position: { ...u.position }, photo: typeof u.photo === 'object' ? u.photo : null, phone: u.phone, ext: u.ext, email: u.email, url: u.url, visible: u.visible } : {})
  await nextTick()
  formEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function save() {
  if (!form.name.trim() || !form.position.uz?.trim()) { error.value = 'F.I.Sh. va lavozim (özbekça) majburiy'; return }
  saving.value = true
  error.value = ''
  const data = { name: form.name.trim(), position: form.position, photo: form.photo?.id ?? null, phone: form.phone.trim(), ext: form.ext.trim(), email: form.email.trim(), url: form.url.trim(), visible: form.visible }
  try {
    if (editing.value === 'new') await api.post('/unit-heads', { ...data, order: items.value.length + 1 })
    else await api.patch(`/unit-heads/${editing.value}`, data)
    await load()
    close()
  }
  catch (e) { error.value = (e as Error).message }
  finally { saving.value = false }
}

async function toggle(u: Unit) {
  await api.patch(`/unit-heads/${u.id}`, { visible: !u.visible })
  u.visible = !u.visible
}

async function remove() {
  if (typeof editing.value !== 'number' || !confirm('Karta öçirilsinmi?')) return
  await api.del(`/unit-heads/${editing.value}`)
  await load()
  close()
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Bölimlar</h1>
        <p class="mt-1.5 max-w-3xl text-[15px] text-muted">«Bölimlar» sahifasidagi kartalar: bölim va markaz rahbarlari. Surat yuklanmasa saytda belgi körinadi. Körinadigan sahifa: Sahifalar → «Bölimlar» («Matndan keyin bölimlar kartalari» yoqilgan).</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-primary h-[46px] gap-2" @click="edit(null)"><Icon name="plus" :size="18" /> Yangi karta</button>
        <a :href="`${SITE_URL}/bolimlar`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
      </div>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <form v-if="editing !== null" ref="formEl" class="card min-w-0 flex-[1_1_380px] px-5 py-[18px] lg:sticky lg:top-4" @submit.prevent="save">
        <div class="flex items-center justify-between gap-2">
          <h2 class="text-lg font-bold">{{ editing === 'new' ? 'Yangi karta' : 'Kartani tahrirlaş' }}</h2>
          <button type="button" class="btn-ghost h-10 gap-1.5 text-sm" @click="close"><Icon name="x" :size="16" /> Yopiş</button>
        </div>
        <div class="mt-3.5 flex gap-4">
          <div class="w-[96px] shrink-0"><ImageField v-model="form.photo" compact folder="staff" label="Rasm" /></div>
          <div class="min-w-0 flex-1">
            <label for="uh-name" class="label">F.I.Sh.</label>
            <input id="uh-name" v-model="form.name" class="field" placeholder="Familiya Ism Otasining ismi">
          </div>
        </div>
        <div class="mt-3.5 grid gap-3.5">
          <I18nFields v-model="form.position" label="Lavozimi (bölim nomi bilan)" layout="rows" textarea :rows="2" id-prefix="uh-pos" />
          <div class="grid gap-3.5 sm:grid-cols-2">
            <div><label for="uh-phone" class="label">Telefon</label><input id="uh-phone" v-model="form.phone" class="field"></div>
            <div><label for="uh-ext" class="label">Içki raqam</label><input id="uh-ext" v-model="form.ext" class="field"></div>
          </div>
          <div><label for="uh-email" class="label">E-poçta</label><input id="uh-email" v-model="form.email" class="field"></div>
          <div>
            <label for="uh-url" class="label">Bölim sahifasi (ixtiyoriy)</label>
            <input id="uh-url" v-model="form.url" class="field" placeholder="/xalqaro-aloqalar-bolimi yoki https://…">
            <p class="mt-1 text-xs text-muted">Kiritilsa — saytdagi karta bosiladigan bo‘ladi.</p>
          </div>
          <ToggleSwitch v-model="form.visible" label="Saytda körinadi" />
        </div>
        <p v-if="error" class="mt-3 text-sm font-semibold text-[#C5192D]" role="alert">{{ error }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button class="btn-primary h-[46px]" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
          <button v-if="editing !== 'new'" type="button" class="btn-ghost h-[46px] text-[#C5192D]" @click="remove">Öçiriş</button>
        </div>
      </form>

      <section class="card min-w-0 flex-[2_1_520px] px-5 py-[18px]">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-lg font-bold">Röyxat ({{ items.length }})</h2>
          <input v-model="query" type="search" class="field h-10 w-full sm:w-64" placeholder="Qidiriş: ism, lavozim">
        </div>
        <p class="mt-1 text-xs text-muted">Tartibni özgartiriş uçun qatorni suring (qidiruv bo‘ş bölganda).</p>
        <ul class="mt-3 flex flex-col gap-1.5">
          <li
            v-for="{ u, i } in shown"
            :key="u.id"
            v-bind="query ? {} : bind(i)"
            class="flex items-center gap-3 rounded-[12px] border px-3 py-2 transition"
            :class="[editing === u.id ? 'border-2 border-brand-700' : 'border-[#F0EEF6]', over === i && 'ring-2 ring-mint', !u.visible && 'opacity-55']"
          >
            <span v-if="!query" class="cursor-grab select-none text-muted" aria-hidden="true">⠿</span>
            <img v-if="mediaUrl(u.photo)" :src="mediaUrl(u.photo)!" alt="" class="size-11 shrink-0 rounded-full object-cover" draggable="false">
            <span v-else class="grid size-11 shrink-0 place-items-center rounded-full bg-[#F1F0F5] text-muted"><Icon name="staff" :size="18" /></span>
            <button type="button" class="min-w-0 flex-1 text-left" @click="edit(u)">
              <span class="block truncate text-[15px] font-semibold">{{ u.name }}</span>
              <span class="block truncate text-[13px] text-muted">{{ u.position.uz }}</span>
            </button>
            <button
              type="button"
              class="grid size-9 shrink-0 place-items-center rounded-full transition-colors"
              :class="u.visible ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#F1F0F5] text-muted'"
              :title="u.visible ? 'Saytda körinadi — yaşiriş uçun bosing' : 'Yaşirilgan — körsatiş uçun bosing'"
              @click="toggle(u)"
            >
              <Icon :name="u.visible ? 'eye' : 'eyeOff'" :size="17" />
            </button>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
