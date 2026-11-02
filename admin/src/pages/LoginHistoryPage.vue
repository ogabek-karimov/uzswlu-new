<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api, type Paginated } from '@/lib/api'
import { dateTime } from '@/lib/format'
import { downloadXlsx } from '@/lib/xlsx'

type LoginEvent = {
  id: number
  user?: { id: number; name: string; role: string } | number | null
  username: string
  method: 'password' | 'hemis'
  result: 'success' | 'bad_password' | 'locked' | 'denied'
  ip: string
  network?: string
  browser?: string
  os?: string
  device?: string
  userAgent?: string
  createdAt: string
}

const RESULT: Record<LoginEvent['result'], [string, string]> = {
  success: ['Muvaffaqiyatli', 'bg-[#DDFBF0] text-[#0B5A43]'],
  bad_password: ['Notöğri parol', 'bg-red-50 text-red-800'],
  locked: ['Bloklangan', 'bg-red-600 text-white'],
  denied: ['Ruxsat yöq', 'bg-[#FEF3DC] text-[#8A5A00]'],
}

const filters = reactive({ tab: 'all' as 'all' | 'ok' | 'bad', q: '' })
const page = ref(1)
const result = ref<Paginated<LoginEvent> | null>(null)
const picked = ref<LoginEvent | null>(null)
const kpi = reactive({ today: 0, failed: 0, total: 0 })

function whereOf() {
  const and: Record<string, unknown>[] = []
  if (filters.tab === 'ok') and.push({ result: { equals: 'success' } })
  if (filters.tab === 'bad') and.push({ result: { not_equals: 'success' } })
  if (filters.q.trim()) and.push({ or: [{ username: { like: filters.q.trim() } }, { ip: { like: filters.q.trim() } }] })
  return and.length ? { and } : undefined
}

async function load() {
  result.value = await api.get<Paginated<LoginEvent>>('/login-events', { where: whereOf(), sort: '-createdAt', limit: 30, page: page.value, depth: 1 })
  if (!picked.value) picked.value = result.value.docs[0] ?? null
}

async function loadKpi() {
  const dayStart = new Date(); dayStart.setHours(0, 0, 0, 0)
  const dayAgo = new Date(Date.now() - 86400000).toISOString()
  const [t, f, all] = await Promise.all([
    api.get<{ totalDocs: number }>('/login-events/count', { where: { and: [{ result: { equals: 'success' } }, { createdAt: { greater_than_equal: dayStart.toISOString() } }] } }),
    api.get<{ totalDocs: number }>('/login-events/count', { where: { and: [{ result: { not_equals: 'success' } }, { createdAt: { greater_than_equal: dayAgo } }] } }),
    api.get<{ totalDocs: number }>('/login-events/count'),
  ])
  kpi.today = t.totalDocs; kpi.failed = f.totalDocs; kpi.total = all.totalDocs
}

onMounted(() => { load(); loadKpi() })
watch([() => filters.tab, page], load)
let timer: ReturnType<typeof setTimeout> | undefined
watch(() => filters.q, () => { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; load() }, 350) })

const who = (e: LoginEvent) => (e.user && typeof e.user === 'object' ? e.user.name : e.username || 'nomaʼlum')
const fields = computed(() => {
  const e = picked.value
  if (!e) return []
  return [
    ['IP manzil', e.ip, true], ['Tarmoq', e.network ?? '—'], ['Kiriş usuli', e.method === 'hemis' ? 'HEMIS' : 'Login va parol'],
    ['Qurilma', e.device ?? '—'], ['Operatsion tizim', e.os ?? '—'], ['Brauzer', e.browser ?? '—'],
    ['Kiritilgan login', e.username || '—'], ['Vaqt', dateTime(e.createdAt)], ['User-Agent', e.userAgent || '—', true],
  ] as [string, string, boolean?][]
})

// Excel (.xlsx): joriy filtr bo'yicha barcha yozuvlar (faqat ekrandagi 30 tasi emas)
const exporting = ref(false)
async function exportXlsx() {
  exporting.value = true
  try {
    const all = await api.get<Paginated<LoginEvent>>('/login-events', { where: whereOf(), sort: '-createdAt', limit: 10000, depth: 1 })
    const roleOf = (e: LoginEvent) => (e.user && typeof e.user === 'object' ? e.user.role : '')
    downloadXlsx(
      `kirish-tarixi-${new Date().toISOString().slice(0, 10)}`,
      'Kiriş tarixi',
      ['Vaqt', 'Foydalanuvçi', 'Rol', 'Kiritilgan login', 'Kiriş usuli', 'Natija', 'IP manzil', 'Tarmoq', 'Qurilma', 'Operatsion tizim', 'Brauzer', 'User-Agent'],
      all.docs.map(e => [dateTime(e.createdAt), who(e), roleOf(e), e.username, e.method === 'hemis' ? 'HEMIS' : 'Login va parol', RESULT[e.result][0], e.ip, e.network ?? '', e.device ?? '', e.os ?? '', e.browser ?? '', e.userAgent ?? '']),
      [19, 26, 12, 18, 15, 16, 16, 18, 14, 18, 18, 60],
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
        <h1 class="text-[28px] font-bold tracking-tight">Kiriş tarixi</h1>
        <p class="mt-1.5 max-w-[720px] text-[15px] leading-relaxed text-muted">Barça admin va superadminlarning har bir kiriş urinişi: vaqt, IP manzil, qurilma, brauzer va natija. 5 marta xato parol — hisob 15 daqiqaga bloklanadi.</p>
      </div>
      <button type="button" class="btn-ghost" :disabled="exporting" @click="exportXlsx">{{ exporting ? 'Tayyorlanmoqda…' : 'Excel’ga yuklab oliş' }}</button>
    </div>

    <div class="grid gap-4 sm:grid-cols-3">
      <div class="card p-5"><p class="text-[13px] text-muted">Bugungi kirişlar</p><p class="mt-2 text-[32px] leading-none font-bold">{{ kpi.today }}</p></div>
      <div class="card p-5"><p class="text-[13px] text-muted">Xato urinişlar (24 soat)</p><p class="mt-2 text-[32px] leading-none font-bold" :class="{ 'text-red-700': kpi.failed > 0 }">{{ kpi.failed }}</p></div>
      <div class="card p-5"><p class="text-[13px] text-muted">Jami yozuvlar</p><p class="mt-2 text-[32px] leading-none font-bold">{{ kpi.total }}</p></div>
    </div>

    <section class="card overflow-hidden">
      <div class="flex flex-wrap items-center gap-2.5 px-5 py-4">
        <h2 class="mr-auto text-base font-bold">Barça kirişlar</h2>
        <input v-model="filters.q" aria-label="Login yoki IP böyiça qidiriş" placeholder="Login yoki IP…" class="field h-10! w-48!">
        <div role="tablist" aria-label="Natija" class="flex gap-0.5 rounded-[11px] bg-canvas p-[3px]">
          <button v-for="t in [['all', 'Hammasi'], ['ok', 'Muvaffaqiyatli'], ['bad', 'Xato']] as const" :key="t[0]" type="button" role="tab" :aria-selected="filters.tab === t[0]" class="h-[34px] rounded-lg px-3 text-[13px] font-semibold" :class="filters.tab === t[0] ? 'bg-white shadow-sm' : 'text-muted'" @click="filters.tab = t[0]; page = 1">{{ t[1] }}</button>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[980px] border-collapse text-[13px]">
          <thead>
            <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
              <th class="px-5 py-3 font-semibold">Vaqt</th><th class="px-3 py-3 font-semibold">Foydalanuvçi</th><th class="px-3 py-3 font-semibold">IP manzil</th>
              <th class="px-3 py-3 font-semibold">Qurilma va brauzer</th><th class="px-5 py-3 font-semibold">Natija</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="result && !result.docs.length"><td colspan="5" class="px-5 py-10 text-center text-muted">Yozuv yöq.</td></tr>
            <tr v-for="e in result?.docs" :key="e.id" class="border-t border-[#F0EEF6]" :class="picked?.id === e.id ? 'bg-brand-50 shadow-[inset_3px_0_0_var(--color-brand-700)]' : 'hover:bg-[#FAF9FD]'">
              <td class="px-5 py-3 whitespace-nowrap"><button type="button" class="font-medium text-brand-800 underline underline-offset-3 tabular-nums" @click="picked = e">{{ dateTime(e.createdAt) }}</button></td>
              <td class="px-3 py-3 whitespace-nowrap"><b>{{ who(e) }}</b><span v-if="e.username && who(e) !== e.username" class="block text-xs text-subtle">{{ e.username }}</span></td>
              <td class="px-3 py-3 whitespace-nowrap"><span class="font-mono text-xs">{{ e.ip }}</span><span class="block text-[11px] text-subtle">{{ e.network }}</span></td>
              <td class="px-3 py-3 whitespace-nowrap">{{ e.device }} · {{ e.os }}<span class="block text-xs text-subtle">{{ e.browser }}</span></td>
              <td class="px-5 py-3 whitespace-nowrap"><span class="chip" :class="RESULT[e.result][1]">{{ RESULT[e.result][0] }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="picked" class="mx-5 mb-5 rounded-2xl border border-line bg-[#FAF9FD] px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-2.5">
          <p class="text-[15px] font-bold">Tafsilotlar · {{ who(picked) }} · {{ dateTime(picked.createdAt) }}</p>
          <span class="chip" :class="RESULT[picked.result][1]">{{ RESULT[picked.result][0] }}</span>
        </div>
        <dl class="mt-3.5 grid gap-x-6 gap-y-3.5 text-[13px] sm:grid-cols-3">
          <div v-for="f in fields" :key="f[0]"><dt class="text-subtle">{{ f[0] }}</dt><dd class="mt-0.5 font-semibold break-words" :class="f[2] && 'font-mono text-xs'">{{ f[1] }}</dd></div>
        </dl>
      </div>
      <div v-if="result && result.totalPages > 1" class="flex justify-end gap-1 border-t border-[#F0EEF6] px-5 py-3">
        <button type="button" class="btn-ghost h-9!" :disabled="page <= 1" @click="page--">← Oldingi</button>
        <button type="button" class="btn-ghost h-9!" :disabled="page >= result.totalPages" @click="page++">Keyingi →</button>
      </div>
    </section>
  </div>
</template>
