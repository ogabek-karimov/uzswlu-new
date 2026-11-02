<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import Icon from '@/components/Icon.vue'
import { api, type Paginated } from '@/lib/api'
import { dateTime, relative } from '@/lib/format'

type Entry = { id: number; userName: string; action: string; entity: string; entityId?: string; label?: string; changes?: Record<string, { before: unknown; after: unknown }>; ip?: string; createdAt: string }
type Version = { id: number; updatedAt: string; version: { title?: { uz?: string }; status?: string; hidden?: boolean } }

const VERB: Record<string, [string, string]> = {
  create: ['yaratdi', 'bg-brand-100 text-brand-800'], edit: ['tahrirladi', 'bg-brand-100 text-brand-800'], publish: ['naşr qildi', 'bg-[#DDFBF0] text-[#0B5A43]'],
  hide: ['yaşirdi', 'bg-[#EEF0F6] text-[#3D4466]'], show: ['qayta körsatdi', 'bg-[#DDFBF0] text-[#0B5A43]'], delete: ['savatga taşladi', 'bg-red-50 text-red-800'],
  restore: ['qaytardi', 'bg-[#FEF3DC] text-[#8A5A00]'], role: ['rol berdi', 'bg-[#FEF3DC] text-[#8A5A00]'], settings: ['sozlamalarni saqladi', 'bg-brand-100 text-brand-800'],
}
const FIELD: Record<string, string> = { status: 'Holati', hidden: 'Saytda yaşirilgan', publishedAt: 'Naşr vaqti', sdg: 'BRM', type: 'Turi', role: 'Rol' }

const kind = ref('all')
const page = ref(1)
const result = ref<Paginated<Entry> | null>(null)
const open = ref<number | null>(null)
const versions = ref<Version[]>([])
const message = ref('')

async function load() {
  const where = kind.value === 'all' ? undefined : { action: { equals: kind.value } }
  result.value = await api.get<Paginated<Entry>>('/activity', { where, sort: '-createdAt', limit: 40, page: page.value })
}
onMounted(load)
watch([kind, page], load)

const days = computed(() => {
  const groups: { label: string; items: Entry[] }[] = []
  for (const e of result.value?.docs ?? []) {
    const label = relative(e.createdAt).split(' · ')[0]!
    const g = groups.find(x => x.label === label)
    if (g) g.items.push(e)
    else groups.push({ label, items: [e] })
  }
  return groups
})

function fmt(key: string, v: unknown) {
  if (v === null || v === undefined || v === '') return '—'
  if (key === 'hidden') return v ? 'ha' : 'yöq'
  if (key === 'status') return v === 'published' ? 'naşr qilingan' : 'qoralama'
  if (key === 'publishedAt' && typeof v === 'string') return dateTime(v)
  return String(v)
}
const label = (key: string) => FIELD[key] ?? (key.startsWith('title.') ? `Sarlavha (${key.slice(6).toUpperCase()})` : key.startsWith('body.') ? `Matn (${key.slice(5).toUpperCase()})` : key)

async function toggle(e: Entry) {
  if (open.value === e.id) { open.value = null; return }
  open.value = e.id
  versions.value = []
  if (e.entity === 'posts' && e.entityId) {
    versions.value = (await api.get<Paginated<Version>>('/posts/versions', { where: { parent: { equals: e.entityId } }, sort: '-updatedAt', limit: 8 })).docs
  }
}

async function restore(v: Version) {
  if (!window.confirm(`Post ${dateTime(v.updatedAt)} dagi holatiga qaytarilsinmi? Hozirgi holat ham tarixda saqlanib qoladi.`)) return
  await api.post(`/posts/versions/${v.id}`)
  message.value = 'Oldingi holatga qaytarildi'
  setTimeout(() => (message.value = ''), 3000)
  await load()
  open.value = null
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Faollik jurnali</h1>
      <p class="mt-1.5 text-[15px] text-muted">Kim, qaçon va nimani özgartirgani. Xato özgarişni oldingi holatiga qaytariş mumkin.</p>
    </div>

    <div class="card flex flex-wrap gap-1.5 px-4 py-3.5">
      <button
        v-for="k in [['all', 'Hammasi'], ['edit', 'Tahrir'], ['publish', 'Naşr'], ['hide', 'Yaşiriş'], ['delete', 'Öçiriş'], ['role', 'Rollar'], ['settings', 'Sozlamalar']]" :key="k[0]" type="button"
        class="h-9 rounded-full px-3 text-[13px] font-semibold" :class="kind === k[0] ? 'bg-ink text-white' : 'border border-field bg-white text-[#3D3958]'"
        @click="kind = k[0]!; page = 1"
      >{{ k[1] }}</button>
    </div>

    <p v-if="result && !result.docs.length" class="text-muted">Hali yozuv yöq.</p>

    <section v-for="day in days" :key="day.label">
      <h2 class="mb-2.5 text-[13px] font-bold tracking-[0.12em] text-subtle uppercase">{{ day.label }}</h2>
      <ol class="flex flex-col gap-2.5">
        <li v-for="e in day.items" :key="e.id" class="card px-4 py-3.5">
          <div class="flex flex-wrap items-center gap-3">
            <span class="grid size-[38px] shrink-0 place-items-center rounded-full bg-brand-100 text-brand-700"><Icon name="activity" :size="16" /></span>
            <span class="min-w-0 flex-[1_1_320px] text-sm leading-relaxed">
              <b>{{ e.userName }}</b> <span class="chip" :class="VERB[e.action]?.[1]">{{ VERB[e.action]?.[0] ?? e.action }}</span> {{ e.label }}
              <span class="block text-xs text-subtle">{{ dateTime(e.createdAt).split(' · ')[1] }} · IP {{ e.ip }}</span>
            </span>
            <button v-if="(e.changes && Object.keys(e.changes).length) || e.entity === 'posts'" type="button" class="btn-ghost h-9! px-3! text-xs!" :aria-expanded="open === e.id" @click="toggle(e)">{{ open === e.id ? 'Yopiş' : 'Farqi va qaytariş' }}</button>
          </div>
          <div v-if="open === e.id" class="mt-3">
            <div v-for="(c, key) in e.changes" :key="key" class="mb-2 grid gap-2 text-[13px] sm:grid-cols-[160px_1fr_1fr]">
              <span class="font-semibold text-muted">{{ label(String(key)) }}</span>
              <span class="rounded-lg bg-red-50 px-3 py-1.5 text-red-900 line-through decoration-red-900/40">{{ fmt(String(key), c.before) }}</span>
              <span class="rounded-lg bg-[#DDFBF0] px-3 py-1.5 text-[#0B5A43]">{{ fmt(String(key), c.after) }}</span>
            </div>
            <div v-if="versions.length" class="mt-3 rounded-xl bg-[#FAF9FD] p-3">
              <p class="mb-2 text-xs font-bold tracking-[0.1em] text-subtle uppercase">Postning saqlangan holatlari</p>
              <div v-for="(v, i) in versions" :key="v.id" class="flex flex-wrap items-center gap-2.5 border-t border-line py-2 text-[13px] first:border-0">
                <span class="tabular-nums">{{ dateTime(v.updatedAt) }}</span>
                <span class="min-w-0 flex-1 truncate text-muted">{{ v.version.title?.uz }}</span>
                <span v-if="i === 0" class="chip bg-brand-100 text-brand-800">joriy</span>
                <button v-else type="button" class="btn-ghost h-8! px-3! text-xs!" @click="restore(v)"><Icon name="undo" :size="14" />Şu holatga qaytariş</button>
              </div>
            </div>
          </div>
        </li>
      </ol>
    </section>

    <div v-if="result && result.totalPages > 1" class="flex justify-end gap-2">
      <button type="button" class="btn-ghost h-9!" :disabled="page <= 1" @click="page--">← Oldingi</button>
      <button type="button" class="btn-ghost h-9!" :disabled="page >= result.totalPages" @click="page++">Keyingi →</button>
    </div>
    <div v-if="message" role="status" class="fixed right-6 bottom-6 z-50 rounded-2xl bg-night px-4 py-3 text-sm font-semibold text-white shadow-xl">{{ message }}</div>
  </div>
</template>
