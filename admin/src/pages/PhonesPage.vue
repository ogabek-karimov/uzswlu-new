<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type Paginated } from '@/lib/api'
import { SITE_URL } from '@/lib/constants'
import { useSortable } from '@/lib/sortable'
import Icon from '@/components/Icon.vue'
import I18nFields from '@/components/I18nFields.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Aloqa sahifasidagi telefonlar ma'lumotnomasi: bo'lim sarlavhalari va xodim qatorlari. Qo'shish, tartiblash (surish), yashirish
type Phone = { id: number; isSection: boolean; name: string; position: I18n; ext: string; phone: string; order?: number | null; visible: boolean }

const items = ref<Phone[]>([])
const editing = ref<number | 'new' | null>(null)
const formEl = ref<HTMLElement>()
const empty = () => ({ isSection: false, name: '', position: {} as I18n, ext: '', phone: '71-230-13-62', visible: true })
const form = reactive(empty())
const saving = ref(false)
const error = ref('')
const loaded = ref(false)
const query = ref('')

const { bind, over } = useSortable(items, 'phones')

async function load() {
  const r = await api.get<Paginated<Phone>>('/phones', { sort: 'order', limit: 1000 })
  items.value = r.docs
  loaded.value = true
}
onMounted(load)

const shown = computed(() => {
  const q = query.value.trim().toLowerCase()
  return items.value.map((p, i) => ({ p, i })).filter(({ p }) => !q || `${p.name} ${p.position.uz ?? ''} ${p.ext} ${p.phone}`.toLowerCase().includes(q))
})

// Kirganda tahrir oynasi yopiq: faqat «Yangi …» yoki röyxatdagi element bosilganda oçiladi; saqlangaç / öçirilgaç yana yopiladi
function close() {
  editing.value = null
  error.value = ''
}

async function edit(p: Phone | null) {
  editing.value = p ? p.id : 'new'
  error.value = ''
  Object.assign(form, empty(), p ? { isSection: p.isSection, name: p.name, position: { ...p.position }, ext: p.ext, phone: p.phone, visible: p.visible } : {})
  await nextTick()
  formEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function save() {
  if (!form.position.uz?.trim()) { error.value = form.isSection ? 'Bölim nomi (özbekça) majburiy' : 'Lavozimi (özbekça) majburiy'; return }
  saving.value = true
  error.value = ''
  const data = { isSection: form.isSection, name: form.isSection ? '' : form.name.trim(), position: form.position, ext: form.isSection ? '' : form.ext.trim(), phone: form.isSection ? '' : form.phone.trim(), visible: form.visible }
  try {
    if (editing.value === 'new') await api.post('/phones', { ...data, order: items.value.length + 1 })
    else await api.patch(`/phones/${editing.value}`, data)
    await load()
    close()
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

async function toggle(p: Phone) {
  await api.patch(`/phones/${p.id}`, { visible: !p.visible })
  p.visible = !p.visible
}

async function remove() {
  if (typeof editing.value !== 'number' || !confirm('Qator öçirilsinmi?')) return
  await api.del(`/phones/${editing.value}`)
  await load()
  close()
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Rahbariyat va bölinmalar bilan aloqa</h1>
        <p class="mt-1.5 max-w-3xl text-[15px] text-muted">«Aloqa» sahifasidagi jadval. Röyxatdagi qatorni bosing — çapda tahrirlaş oçiladi. <b class="text-ink">Köz</b> belgisi — qatorni saytda yaşiriş/körsatiş, <b class="text-ink">⠿</b> — surib tartibini özgartiriş.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-primary h-[46px] gap-2" @click="edit(null)"><Icon name="plus" :size="18" /> Yangi qator qöşiş</button>
        <a :href="`${SITE_URL}/aloqa`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
      </div>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <form v-if="editing !== null" ref="formEl" class="card min-w-0 flex-[1_1_380px] px-5 py-[18px] lg:sticky lg:top-4" @submit.prevent="save">
        <div class="flex items-center justify-between gap-2">
          <h2 class="text-lg font-bold">{{ editing === 'new' ? 'Yangi qator qöşiş' : 'Qatorni tahrirlaş' }}</h2>
          <button type="button" class="btn-ghost h-10 gap-1.5 text-sm" @click="close"><Icon name="x" :size="16" /> Yopiş</button>
        </div>
        <div class="mt-3.5 grid gap-3.5">
          <div>
            <p class="label">Qator turi</p>
            <div class="grid grid-cols-2 gap-2">
              <button type="button" class="rounded-[12px] border-2 px-3 py-2.5 text-left text-sm font-semibold transition" :class="!form.isSection ? 'border-brand-700 bg-brand-50 text-brand-800' : 'border-[#ECEAF3] text-muted'" @click="form.isSection = false">Xodim<span class="block text-xs font-normal">F.I.Sh., lavozim, raqamlar</span></button>
              <button type="button" class="rounded-[12px] border-2 px-3 py-2.5 text-left text-sm font-semibold transition" :class="form.isSection ? 'border-brand-700 bg-brand-50 text-brand-800' : 'border-[#ECEAF3] text-muted'" @click="form.isSection = true">Bölim sarlavhasi<span class="block text-xs font-normal">Masalan: «Rektorat»</span></button>
            </div>
          </div>
          <div v-if="!form.isSection">
            <label for="ph-name" class="label">F.I.Sh. (bo‘ş bölsa — faqat lavozim, masalan «Qabulxona»)</label>
            <input id="ph-name" v-model="form.name" class="field" placeholder="Familiya Ism Otasining ismi">
          </div>
          <I18nFields v-model="form.position" :label="form.isSection ? 'Bölim nomi' : 'Lavozimi'" layout="rows" id-prefix="ph-pos" />
          <div v-if="!form.isSection" class="grid gap-3.5 sm:grid-cols-2">
            <div>
              <label for="ph-ext" class="label">Ichki raqami</label>
              <input id="ph-ext" v-model="form.ext" class="field" placeholder="1009">
            </div>
            <div>
              <label for="ph-phone" class="label">Ish telefoni</label>
              <input id="ph-phone" v-model="form.phone" class="field" placeholder="71-230-13-62">
            </div>
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
          <input v-model="query" type="search" class="field h-10 w-full sm:w-64" placeholder="Qidiriş: ism, lavozim, raqam">
        </div>
        <p class="mt-1 text-xs text-muted">Tartibni özgartiriş uçun qatorni suring (qidiruv bo‘ş bölganda).</p>
        <p v-if="loaded && !items.length" class="mt-4 text-sm text-muted">Hali qator yöq. Bo‘ş bölsa saytda rahbariyat jadvali körsatiladi.</p>
        <ul class="mt-3 flex flex-col gap-1.5">
          <li
            v-for="{ p, i } in shown"
            :key="p.id"
            v-bind="query ? {} : bind(i)"
            class="flex items-center gap-3 rounded-[12px] border px-3 py-2 transition"
            :class="[editing === p.id ? 'border-2 border-brand-700' : 'border-[#F0EEF6]', over === i && 'ring-2 ring-mint', !p.visible && 'opacity-55', p.isSection && 'bg-[#F5F3FE]']"
          >
            <span v-if="!query" class="cursor-grab select-none text-muted" aria-hidden="true">⠿</span>
            <button type="button" class="min-w-0 flex-1 text-left" @click="edit(p)">
              <span v-if="p.isSection" class="block truncate text-[15px] font-bold text-brand-800">{{ p.position.uz }}</span>
              <template v-else>
                <span class="block truncate text-[15px] font-semibold">{{ p.name || p.position.uz }}</span>
                <span class="block truncate text-[13px] text-muted">{{ p.name ? p.position.uz : '' }}<template v-if="p.ext || p.phone"> · {{ p.ext }} · {{ p.phone }}</template></span>
              </template>
            </button>
            <button
              type="button"
              class="grid size-9 shrink-0 place-items-center rounded-full transition-colors"
              :class="p.visible ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#F1F0F5] text-muted'"
              :aria-pressed="p.visible"
              :title="p.visible ? 'Saytda körinadi — yaşiriş uçun bosing' : 'Yaşirilgan — körsatiş uçun bosing'"
              @click="toggle(p)"
            >
              <Icon :name="p.visible ? 'eye' : 'eyeOff'" :size="17" />
            </button>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
