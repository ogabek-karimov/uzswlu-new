<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { api, API_BASE, type Paginated } from '@/lib/api'
import { dateTime } from '@/lib/format'
import { downloadXlsx } from '@/lib/xlsx'

// Xorijiy abituriyentlar arizalari (saytdagi «Xalqaro talabalar» → «Ariza şakli»). Faqat superadmin: pasport ma'lumotlari bor.
type Status = 'new' | 'in_progress' | 'accepted' | 'rejected'
type Application = {
  id: number; number: string; lastName: string; firstName: string; middleName?: string | null; passport: string; country: string; address: string
  gender: 'male' | 'female'; faculty: string; studyForm: 'day' | 'distance' | 'evening'; degree: 'bachelor' | 'master' | 'doctorate'; program: string
  phone: string; email: string; lang: string; files: { passport_file: string | null; diploma_file: string | null; photo_file: string | null }
  status: Status; note: string; ip?: string | null; createdAt: string
}

const STATUS: Record<Status, [string, string]> = {
  new: ['Yangi', 'bg-[#FEF3DC] text-[#8A5A00]'],
  in_progress: ['Körib çiqilmoqda', 'bg-brand-50 text-brand-800'],
  accepted: ['Qabul qilindi', 'bg-[#DDFBF0] text-[#0B5A43]'],
  rejected: ['Rad etildi', 'bg-red-50 text-red-800'],
}
const DEGREE = { bachelor: 'Bakalavriat', master: 'Magistratura', doctorate: 'Doktorantura' }
const FORM = { day: 'Kunduzgi', distance: 'Sirtqi', evening: 'Keçki' }
const FILES: [keyof Application['files'], string][] = [['passport_file', 'Pasport'], ['diploma_file', 'Diplom / sertifikat'], ['photo_file', '3×4 surat']]

const filters = reactive({ status: 'all' as 'all' | Status, q: '' })
const page = ref(1)
const result = ref<Paginated<Application> | null>(null)
const picked = ref<Application | null>(null)
const saving = ref(false)
const fileUrl = (name: string) => `${API_BASE}/private/${name}`
const fullName = (a: Application) => [a.lastName, a.firstName, a.middleName].filter(Boolean).join(' ')

function whereOf() {
  const and: Record<string, unknown>[] = []
  if (filters.status !== 'all') and.push({ status: { equals: filters.status } })
  const q = filters.q.trim()
  if (q) and.push({ or: [{ lastName: { like: q } }, { firstName: { like: q } }, { number: { like: q } }, { email: { like: q } }, { country: { like: q } }] })
  return and.length ? { and } : undefined
}

async function load() {
  result.value = await api.get<Paginated<Application>>('/applications', { where: whereOf(), sort: '-createdAt', limit: 30, page: page.value })
  picked.value = result.value.docs.find(d => d.id === picked.value?.id) ?? result.value.docs[0] ?? null
}

async function save(a: Application, data: Partial<Pick<Application, 'status' | 'note'>>) {
  saving.value = true
  try {
    const res = await api.patch<{ doc: Application }>(`/applications/${a.id}`, data)
    Object.assign(a, res.doc)
  }
  finally {
    saving.value = false
  }
}

onMounted(load)
watch([() => filters.status, page], load)
let timer: ReturnType<typeof setTimeout> | undefined
watch(() => filters.q, () => { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; load() }, 350) })

const exporting = ref(false)
async function exportXlsx() {
  exporting.value = true
  try {
    const all = await api.get<Paginated<Application>>('/applications', { where: whereOf(), sort: '-createdAt', limit: 10000 })
    downloadXlsx(
      `arizalar-${new Date().toISOString().slice(0, 10)}`, 'Arizalar',
      ['Raqami', 'Sana', 'F.I.Ş.', 'Pasport', 'Mamlakat', 'Manzil', 'Jinsi', 'Daraja', 'Şakl', 'Fakultet', 'Yönaliş', 'Telefon', 'E-poçta', 'Holati', 'Izoh'],
      all.docs.map(a => [a.number, dateTime(a.createdAt), fullName(a), a.passport, a.country, a.address, a.gender === 'male' ? 'Erkak' : 'Ayol',
        DEGREE[a.degree], FORM[a.studyForm], a.faculty, a.program, a.phone, a.email, STATUS[a.status][0], a.note]),
      [15, 17, 30, 14, 16, 30, 8, 14, 10, 28, 34, 18, 26, 18, 30],
    )
  }
  finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Arizalar</h1>
        <p class="mt-1.5 max-w-[720px] text-[15px] leading-relaxed text-muted">Xorijiy abituriyentlar saytdagi «Xalqaro talabalar → Ariza şakli» orqali yuborgan arizalar. Fayllar yopiq saqlanadi va faqat şu yerdan yuklab olinadi.</p>
      </div>
      <button type="button" class="btn-ghost" :disabled="exporting" @click="exportXlsx">{{ exporting ? 'Tayyorlanmoqda…' : 'Excel’ga yuklab oliş' }}</button>
    </div>

    <section class="card overflow-hidden">
      <div class="flex flex-wrap items-center gap-2.5 px-5 py-4">
        <h2 class="mr-auto text-base font-bold">Barça arizalar <span v-if="result" class="text-muted">· {{ result.totalDocs }}</span></h2>
        <input v-model="filters.q" aria-label="Qidiriş" placeholder="F.I.Ş., raqam, e-poçta…" class="field h-10! w-56!">
        <div role="tablist" aria-label="Holati" class="flex flex-wrap gap-0.5 rounded-[11px] bg-canvas p-[3px]">
          <button v-for="t in [['all', 'Hammasi'], ...Object.entries(STATUS).map(([k, v]) => [k, v[0]])]" :key="t[0]" type="button" role="tab" :aria-selected="filters.status === t[0]" class="h-[34px] rounded-lg px-3 text-[13px] font-semibold" :class="filters.status === t[0] ? 'bg-white shadow-sm' : 'text-muted'" @click="filters.status = t[0] as typeof filters.status; page = 1">{{ t[1] }}</button>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[900px] border-collapse text-[13px]">
          <thead>
            <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
              <th class="px-5 py-3 font-semibold">Raqami</th><th class="px-3 py-3 font-semibold">F.I.Ş.</th><th class="px-3 py-3 font-semibold">Mamlakat</th>
              <th class="px-3 py-3 font-semibold">Daraja va yönaliş</th><th class="px-3 py-3 font-semibold">Sana</th><th class="px-5 py-3 font-semibold">Holati</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="result && !result.docs.length"><td colspan="6" class="px-5 py-10 text-center text-muted">Ariza yöq.</td></tr>
            <tr v-for="a in result?.docs" :key="a.id" class="border-t border-[#F0EEF6]" :class="picked?.id === a.id ? 'bg-brand-50 shadow-[inset_3px_0_0_var(--color-brand-700)]' : 'hover:bg-[#FAF9FD]'">
              <td class="px-5 py-3 whitespace-nowrap"><button type="button" class="font-medium text-brand-800 underline underline-offset-3 tabular-nums" @click="picked = a">{{ a.number }}</button></td>
              <td class="px-3 py-3"><b>{{ fullName(a) }}</b><span class="block text-xs text-subtle">{{ a.email }}</span></td>
              <td class="px-3 py-3 whitespace-nowrap">{{ a.country }}</td>
              <td class="px-3 py-3">{{ DEGREE[a.degree] }} · {{ FORM[a.studyForm] }}<span class="block text-xs text-subtle">{{ a.program }}</span></td>
              <td class="px-3 py-3 whitespace-nowrap tabular-nums">{{ dateTime(a.createdAt) }}</td>
              <td class="px-5 py-3 whitespace-nowrap"><span class="chip" :class="STATUS[a.status][1]">{{ STATUS[a.status][0] }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="picked" class="mx-5 mb-5 rounded-2xl border border-line bg-[#FAF9FD] px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-2.5">
          <p class="text-[15px] font-bold">{{ picked.number }} · {{ fullName(picked) }}</p>
          <select :value="picked.status" aria-label="Holati" class="field h-10! w-auto!" :disabled="saving" @change="save(picked!, { status: ($event.target as HTMLSelectElement).value as Status })">
            <option v-for="(v, k) in STATUS" :key="k" :value="k">{{ v[0] }}</option>
          </select>
        </div>
        <dl class="mt-3.5 grid gap-x-6 gap-y-3.5 text-[13px] sm:grid-cols-3">
          <div v-for="f in [['Pasport', picked.passport], ['Mamlakat', picked.country], ['Jinsi', picked.gender === 'male' ? 'Erkak' : 'Ayol'], ['Telefon', picked.phone], ['E-poçta', picked.email], ['Sayt tili', picked.lang.toUpperCase()], ['Ta’lim darajasi', DEGREE[picked.degree]], ['Ta’lim şakli', FORM[picked.studyForm]], ['Fakultet', picked.faculty], ['Yönaliş', picked.program], ['Manzil', picked.address], ['Yuborilgan', dateTime(picked.createdAt)]]" :key="f[0]">
            <dt class="text-subtle">{{ f[0] }}</dt><dd class="mt-0.5 font-semibold break-words">{{ f[1] }}</dd>
          </div>
        </dl>
        <div class="mt-4 flex flex-wrap gap-2">
          <template v-for="[k, label] in FILES" :key="k">
            <a v-if="picked.files[k]" :href="fileUrl(picked.files[k]!)" class="btn-ghost h-10!">⬇ {{ label }}</a>
          </template>
        </div>
        <label class="mt-4 block text-[13px] font-semibold text-muted" for="ap-note">Izoh (faqat adminlar köradi)</label>
        <textarea id="ap-note" :value="picked.note" rows="2" maxlength="2000" class="field mt-1.5 h-auto! py-2" @change="save(picked!, { note: ($event.target as HTMLTextAreaElement).value })" />
      </div>
      <div v-if="result && result.totalPages > 1" class="flex justify-end gap-1 border-t border-[#F0EEF6] px-5 py-3">
        <button type="button" class="btn-ghost h-9!" :disabled="page <= 1" @click="page--">← Oldingi</button>
        <button type="button" class="btn-ghost h-9!" :disabled="page >= result.totalPages" @click="page++">Keyingi →</button>
      </div>
    </section>
  </div>
</template>
