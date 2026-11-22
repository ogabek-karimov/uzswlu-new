<script setup lang="ts">
import { computed, ref } from 'vue'
import I18nFields from '@/components/I18nFields.vue'
import Icon from '@/components/Icon.vue'
import type { I18n } from '@/lib/api'
import { useHemis } from '@/lib/hemis'

// Sahifadagi xodimlar (masalan, «Axborot-resurs markazi»):
// 1) HEMIS bölimi — xodimlari saytga HEMIS profili orqali kirgaç sahifada özi çiqadi (rahbar birinçi);
// 2) zaxira — admin HEMIS röyxatidan qölda qöşadigan xodimlar (bölim xodimlaridan keyin, şu tartibda).
const department = defineModel<string>('department', { required: true })
const extra = defineModel<string[]>('extra', { required: true })
// Kartadagi telefon / e-poçta (kiritilmasa saytda körinmaydi) va umumiy qabul kunlari
const contacts = defineModel<Record<string, { phone?: string; email?: string }>>('contacts', { required: true })
const hours = defineModel<I18n>('hours', { required: true })

const hemis = useHemis()
const query = ref('')
const fold = (s: string) => s.toLowerCase().replace(/[‘’ʻʼ`']/g, '').replace(/ö/g, 'o').replace(/ğ/g, 'g').replace(/ş/g, 'sh').replace(/ç/g, 'ch')

const departments = computed(() => [...(hemis.value?.staffDepartments ?? [])].sort((a, b) => a.name.localeCompare(b.name)))
// Nom bilan yozilgan qiymat (masalan, köçirişda «Axborot-resurs markazi») — röyxatda ID bölmasa ham körinsin
const customDept = computed(() => department.value && !departments.value.some(d => d.id === department.value) ? department.value : '')
const staffById = computed(() => new Map((hemis.value?.staff ?? []).map(p => [String(p.id), p])))
const deptCount = computed(() => {
  const d = department.value
  if (!d) return 0
  const id = departments.value.find(x => x.id === d || fold(x.name) === fold(d))?.id
  return (hemis.value?.staff ?? []).filter(p => p.employments.some(e => e.department.id === id)).length
})

// Sahifada çiqadigan xodimlar (avtomatik + zaxira) — har biriga telefon / e-poçta kiritiş uçun
const deptId = computed(() => departments.value.find(x => x.id === department.value || fold(x.name) === fold(department.value))?.id)
const onPage = computed(() => {
  const auto = deptId.value ? (hemis.value?.staff ?? []).filter(p => p.employments.some(e => e.department.id === deptId.value)) : []
  const ids = new Set(auto.map(p => String(p.id)))
  const added = extra.value.filter(id => !ids.has(id)).map(id => staffById.value.get(id)).filter(p => !!p)
  return [...auto.sort((a, b) => a.name.localeCompare(b.name)), ...added]
})
function setContact(id: string | number, field: 'phone' | 'email', value: string) {
  const key = String(id)
  contacts.value = { ...contacts.value, [key]: { ...(contacts.value[key] ?? {}), [field]: value } }
}

const results = computed(() => {
  const words = fold(query.value).split(/\s+/).filter(Boolean)
  if (!words.length) return []
  return (hemis.value?.staff ?? [])
    .filter(p => !extra.value.includes(String(p.id)) && words.every(w => fold(p.name).includes(w)))
    .slice(0, 8)
})

function add(id: string | number) {
  extra.value = [...extra.value, String(id)]
  query.value = ''
}
function remove(id: string) {
  extra.value = extra.value.filter(x => x !== id)
}
function move(i: number, d: -1 | 1) {
  const list = [...extra.value]
  const j = i + d
  if (j < 0 || j >= list.length) return
  ;[list[i], list[j]] = [list[j]!, list[i]!]
  extra.value = list
}
const jobs = (p: { employments: { department: { name: string }; position: string }[] }) => p.employments.map(e => `${e.position} — ${e.department.name}`).join('; ')
</script>

<template>
  <fieldset class="rounded-2xl border border-line bg-[#FAF9FD] px-4 py-3.5">
    <legend class="px-1 text-sm font-bold">Sahifadagi xodimlar <span class="font-normal text-muted">(matndan oldin, HEMIS’dan)</span></legend>

    <label for="ps-dept" class="label">HEMIS bölimi — xodimlari avtomatik çiqadi</label>
    <select id="ps-dept" v-model="department" class="field">
      <option value="">— bölim tanlanmagan —</option>
      <option v-if="customDept" :value="customDept">{{ customDept }} (nomi böyiça)</option>
      <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }} · {{ d.count }} xodim</option>
    </select>
    <p class="mt-1 text-xs text-muted">
      <template v-if="department">Hozir {{ deptCount }} xodim. Yangi xodim saytga HEMIS profili orqali kirgaç şu yerda özi paydo böladi; rahbar birinçi turadi.</template>
      <template v-else>Bölim tanlansa, uning xodimlari sahifada kartoçka bölib çiqadi.</template>
    </p>

    <div class="mt-3.5">
      <label for="ps-search" class="label">Zaxira: xodimni qölda qöşiş (HEMIS röyxatidan)</label>
      <div class="relative">
        <input id="ps-search" v-model="query" type="search" class="field" placeholder="F.I.Sh. böyiça qidiriş…" autocomplete="off">
        <ul v-if="results.length" class="absolute inset-x-0 top-full z-10 mt-1 max-h-72 overflow-auto rounded-xl border border-line bg-white py-1 shadow-lg">
          <li v-for="p in results" :key="p.id">
            <button type="button" class="block w-full px-3.5 py-2 text-left hover:bg-[#F4F3FA]" @click="add(p.id)">
              <span class="block text-sm font-semibold">{{ p.name }}</span>
              <span class="block truncate text-xs text-muted">{{ jobs(p) }}</span>
            </button>
          </li>
        </ul>
        <p v-else-if="query.trim() && hemis" class="mt-1 text-xs text-muted">Topilmadi.</p>
      </div>
      <p class="mt-1 text-xs text-muted">HEMIS’da boşqa bölimga yozilgan yoki bölimi topilmagan xodim uçun. Bölim xodimlaridan keyin, şu tartibda çiqadi; takrorlanmaydi.</p>

      <ul v-if="extra.length" class="mt-2.5 flex flex-col gap-1.5">
        <li v-for="(id, i) in extra" :key="id" class="flex items-center gap-2 rounded-[12px] border border-[#F0EEF6] bg-white px-3 py-2">
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-semibold">{{ staffById.get(id)?.name ?? `HEMIS ID ${id}` }}</span>
            <span class="block truncate text-xs" :class="staffById.get(id) ? 'text-muted' : 'text-[#C5192D]'">{{ staffById.get(id) ? jobs(staffById.get(id)!) : 'HEMIS’da topilmadi (işdan ketgan yoki yaşirilgan) — saytda çiqmaydi' }}</span>
          </span>
          <button type="button" class="grid size-8 place-items-center rounded-full text-muted hover:bg-[#F1F0F5] disabled:opacity-30" :disabled="i === 0" aria-label="Yuqoriga" @click="move(i, -1)">↑</button>
          <button type="button" class="grid size-8 place-items-center rounded-full text-muted hover:bg-[#F1F0F5] disabled:opacity-30" :disabled="i === extra.length - 1" aria-label="Pastga" @click="move(i, 1)">↓</button>
          <button type="button" class="grid size-8 place-items-center rounded-full text-[#C5192D] hover:bg-red-50" :aria-label="`${staffById.get(id)?.name ?? id} — olib taşlaş`" @click="remove(id)"><Icon name="x" :size="16" /></button>
        </li>
      </ul>
    </div>

    <div v-if="onPage.length" class="mt-4">
      <p class="label">Kartadagi telefon va e-poçta <span class="font-normal">— kiritilmasa saytda körinmaydi; böş qolsa xodim öz kabinetida kiritgani çiqadi</span></p>
      <ul class="flex flex-col gap-1.5">
        <li v-for="p in onPage" :key="p.id" class="grid gap-2 rounded-[12px] border border-[#F0EEF6] bg-white px-3 py-2 sm:grid-cols-[minmax(0,1fr)_170px_200px] sm:items-center">
          <span class="min-w-0">
            <span class="block truncate text-sm font-semibold">{{ p.name }}</span>
            <span class="block truncate text-xs text-muted">{{ jobs(p) }}</span>
          </span>
          <input class="field h-10!" type="tel" :aria-label="`${p.name} — telefon`" placeholder="Telefon" :value="contacts[String(p.id)]?.phone ?? ''" @input="setContact(p.id, 'phone', ($event.target as HTMLInputElement).value)">
          <input class="field h-10!" type="email" :aria-label="`${p.name} — e-poçta`" placeholder="E-poçta" :value="contacts[String(p.id)]?.email ?? ''" @input="setContact(p.id, 'email', ($event.target as HTMLInputElement).value)">
        </li>
      </ul>
    </div>

    <div class="mt-4">
      <I18nFields v-model="hours" label="Qabul kunlari (barça kartalarda)" layout="rows" :placeholders="{ uz: 'Duşanbadan jumagaça, 8:30 dan 16:30 gaça' }" />
      <p class="mt-1 text-xs text-muted">Böş qolsa kartada körinmaydi.</p>
    </div>
  </fieldset>
</template>
