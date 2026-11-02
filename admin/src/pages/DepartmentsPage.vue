<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, type I18n, type MediaDoc, type Paginated } from '@/lib/api'
import { LANGS, type Lang } from '@/lib/constants'
import { hemisBadge, useHemis } from '@/lib/hemis'
import ImageField from '@/components/ImageField.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Kafedralar: nomi, mudiri va xodimlar soni HEMIS'dan; ta'rif, rasm, aloqa va tarjimalar — shu yerda
type Dept = { id: number; hemisId: string; faculty?: string | null; name?: I18n; image?: MediaDoc | number | null; about?: I18n; room?: string | null; ext?: string | null; showStaff?: boolean }

const route = useRoute()
const hemis = useHemis()
const badge = computed(() => hemisBadge(hemis.value))
const own = ref<Dept[]>([])
const faculty = ref('all')
const tab = ref<'all' | 'done' | 'todo'>('all')
const sel = ref<string | null>(null)
const lang = ref<Lang>('uz')
const saving = ref(false)
const saved = ref(false)
const error = ref('')
const form = reactive({ name: {} as I18n, image: null as MediaDoc | null, about: {} as I18n, room: '', ext: '', showStaff: true })

async function load() {
  own.value = (await api.get<Paginated<Dept>>('/departments', { limit: 1000, depth: 1 })).docs
}
onMounted(load)

// HEMIS'dagi barcha kafedralar (fakultet bilan)
const all = computed(() => (hemis.value?.faculties ?? []).flatMap(f => f.departments.map(d => ({ ...d, faculty: f.slug, facultyName: f.name }))))
const ownOf = (id: string) => own.value.find(d => d.hemisId === id)
const filled = (id: string) => !!ownOf(id)?.about?.uz?.trim()
const rows = computed(() => all.value.filter(d =>
  (faculty.value === 'all' || d.faculty === faculty.value)
  && (tab.value === 'all' || (tab.value === 'done' ? filled(d.id) : !filled(d.id)))))
const counts = computed(() => {
  const base = all.value.filter(d => faculty.value === 'all' || d.faculty === faculty.value)
  return { all: base.length, done: base.filter(d => filled(d.id)).length, todo: base.filter(d => !filled(d.id)).length }
})
const current = computed(() => all.value.find(d => d.id === sel.value) ?? null)

function pick(id: string) {
  sel.value = id
  saved.value = false
  error.value = ''
  const d = ownOf(id)
  Object.assign(form, { name: { ...(d?.name ?? {}) }, image: d?.image && typeof d.image === 'object' ? d.image : null, about: { ...(d?.about ?? {}) }, room: d?.room ?? '', ext: d?.ext ?? '', showStaff: d?.showStaff !== false })
}

// Fakultetlar sahifasidagi "Ta'rif →" havolasi: ?d=<kafedra>
watch([all, () => route.query.d], () => {
  const q = String(route.query.d ?? '')
  if (q && all.value.some(d => d.id === q) && sel.value !== q) { faculty.value = all.value.find(d => d.id === q)!.faculty; pick(q) }
  else if (!sel.value && all.value[0]) pick(all.value[0].id)
}, { immediate: true })

async function save() {
  if (!current.value) return
  saving.value = true
  error.value = ''
  const data = {
    hemisId: current.value.id, faculty: current.value.faculty,
    name: { ...form.name, uz: current.value.name },
    image: form.image?.id ?? null, about: form.about, room: form.room.trim() || null, ext: form.ext.trim() || null, showStaff: form.showStaff,
  }
  try {
    const existing = ownOf(current.value.id)
    if (existing) await api.patch(`/departments/${existing.id}`, data)
    else await api.post('/departments', data)
    await load()
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Kafedralar</h1>
        <p class="mt-1.5 max-w-[700px] text-[15px] leading-normal text-muted">Kafedralar, mudirlar va xodimlar soni HEMIS’dan olinadi. Siz ta’rif, rasm va aloqa ma’lumotini töldirasiz.</p>
      </div>
      <span class="flex items-center gap-2 rounded-full px-3 py-2 text-[13px] font-semibold" :class="badge.ok ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#FEF3DC] text-[#8A5A00]'">
        <span class="size-[7px] rounded-full" :class="badge.ok ? 'bg-[#12B76A]' : 'bg-[#F79009]'" />{{ badge.text }}
      </span>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <section class="card min-w-0 flex-[999_1_560px] overflow-hidden p-0!">
        <div class="flex flex-wrap items-center gap-2.5 px-[18px] py-3.5">
          <select v-model="faculty" class="field h-10! w-auto! max-w-full" aria-label="Fakultet">
            <option value="all">Barça fakultetlar</option>
            <option v-for="f in hemis?.faculties ?? []" :key="f.slug" :value="f.slug">{{ f.name }}</option>
          </select>
          <div role="tablist" aria-label="Holati" class="flex gap-1">
            <button v-for="t in ([['all', 'Hammasi'], ['done', 'Töldirilgan'], ['todo', 'Töldiriş kerak']] as const)" :key="t[0]" type="button" role="tab" :aria-selected="tab === t[0]" class="h-9 rounded-full px-3 text-xs font-semibold" :class="tab === t[0] ? 'bg-ink text-white' : 'border border-field text-[#3D3958]'" @click="tab = t[0]">{{ t[1] }} <span class="opacity-70">{{ counts[t[0]] }}</span></button>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[760px] border-collapse text-sm">
            <thead>
              <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
                <th scope="col" class="px-[18px] py-3 font-semibold">Kafedra</th>
                <th scope="col" class="px-3 py-3 font-semibold">Mudir (HEMIS)</th>
                <th scope="col" class="px-3 py-3 font-semibold">Fakultet</th>
                <th scope="col" class="py-3 pr-[18px] pl-3 font-semibold">Ta’rif</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!rows.length"><td colspan="4" class="px-5 py-10 text-center text-muted">Kafedra topilmadi.</td></tr>
              <tr v-for="d in rows" :key="d.id" class="cursor-pointer border-t border-[#F0EEF6] hover:bg-[#FAF9FD]" :class="sel === d.id && 'bg-brand-50'" @click="pick(d.id)">
                <td class="px-[18px] py-3"><button type="button" class="text-left font-bold" :aria-pressed="sel === d.id" @click.stop="pick(d.id)">{{ d.name }}</button><span class="block text-[11px] text-subtle">HEMIS ID {{ d.id }}</span></td>
                <td class="px-3 py-3 text-[13px] text-muted">{{ d.head || '—' }}</td>
                <td class="max-w-[220px] px-3 py-3 text-[13px] text-muted">{{ d.facultyName }}</td>
                <td class="py-3 pr-[18px] pl-3"><span class="chip text-[11px]!" :class="filled(d.id) ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#FEF3DC] text-[#8A5A00]'">{{ filled(d.id) ? 'Töldirilgan' : 'Böş' }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <form v-if="current" class="card flex min-w-0 flex-[1_1_360px] flex-col gap-3 px-5 py-[18px]" @submit.prevent="save">
        <div>
          <h2 class="text-base font-bold">{{ current.name }}</h2>
          <p class="mt-0.5 text-xs text-muted">{{ current.facultyName }} · HEMIS ID {{ current.id }}</p>
        </div>
        <ImageField v-model="form.image" folder="logos" label="+ Kafedra rasmi" />
        <fieldset>
          <legend class="label">Nomi tarjimalari <span class="font-normal">— HEMIS’da faqat özbekça</span></legend>
          <div class="flex flex-col gap-2">
            <label v-for="l in LANGS.filter(x => x.code !== 'uz')" :key="l.code" class="flex items-center gap-2">
              <span class="w-[30px] shrink-0 text-xs font-bold text-subtle">{{ l.short }}</span>
              <input v-model="form.name[l.code]" class="field" :aria-label="`Nomi · ${l.label}`">
            </label>
          </div>
        </fieldset>
        <div>
          <div class="mb-1.5 flex items-center justify-between gap-2">
            <span class="label mb-0!">Kafedra haqida</span>
            <div role="tablist" aria-label="Til" class="flex gap-1">
              <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
            </div>
          </div>
          <textarea v-model="form.about[lang]" rows="5" class="field h-auto! py-2.5 leading-relaxed" :aria-label="`Kafedra haqida · ${lang}`" />
        </div>
        <div class="grid grid-cols-2 gap-2.5">
          <div><label for="dp-room" class="label">Xona</label><input id="dp-room" v-model="form.room" class="field"></div>
          <div><label for="dp-ext" class="label">Içki telefon</label><input id="dp-ext" v-model="form.ext" class="field" inputmode="numeric"></div>
        </div>
        <div class="flex items-center justify-between gap-3 text-[13px] text-[#3D3958]">
          <span>Xodimlar röyxatini sahifada körsatiş (HEMIS’dan)</span>
          <ToggleSwitch v-model="form.showStaff" label="Xodimlar röyxatini körsatiş" />
        </div>
        <p class="rounded-[10px] bg-brand-50 px-3 py-2.5 text-xs leading-normal text-brand-800">Tarjimalar saytdagi fakultet sahifasida kafedralar röyxatida körinadi. Kafedraning alohida sahifasi dizayni hali tayyor emas — ta’rif va rasm shu sahifa uçun saqlanadi.</p>
        <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <p v-else-if="saved" class="rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi.</p>
        <div class="flex justify-end"><button type="submit" class="btn-primary h-[42px]!" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button></div>
      </form>
    </div>
  </div>
</template>
