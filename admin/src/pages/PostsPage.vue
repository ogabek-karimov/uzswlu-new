<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import { api, type Paginated } from '@/lib/api'
import { LANGS, POST_TYPES, type PostType, SDG_COLORS, SDG_NAMES, SITE_URL } from '@/lib/constants'
import { dateTime } from '@/lib/format'
import { langFill, mediaUrl, type Post, postState, STATE_BADGE } from '@/lib/posts'

const route = useRoute()
const router = useRouter()
const type = computed(() => (route.params.type as PostType) ?? 'news')
const meta = computed(() => POST_TYPES.find(t => t.value === type.value)!)

const filters = reactive({ q: '', state: '', sdg: typeof route.query.sdg === 'string' ? route.query.sdg : '', trash: false })
const page = ref(1)
const result = ref<Paginated<Post> | null>(null)
const counts = ref<Record<string, number>>({})
const loading = ref(false)
const picked = ref<Set<number>>(new Set())
const message = ref('')

function where() {
  const and: Record<string, unknown>[] = [{ type: { equals: type.value } }]
  if (filters.q.trim()) and.push({ or: [{ 'title.uz': { like: filters.q.trim() } }, { 'title.ru': { like: filters.q.trim() } }, { 'title.en': { like: filters.q.trim() } }, { 'title.zh': { like: filters.q.trim() } }] })
  const now = new Date().toISOString()
  if (filters.state === 'draft') and.push({ status: { equals: 'draft' } })
  if (filters.state === 'published') and.push({ status: { equals: 'published' } }, { publishedAt: { less_than_equal: now } })
  if (filters.state === 'scheduled') and.push({ status: { equals: 'published' } }, { publishedAt: { greater_than: now } })
  if (filters.state === 'hidden') and.push({ hidden: { equals: true } })
  if (filters.sdg === '0') and.push({ sdg: { equals: 0 } })
  else if (filters.sdg) and.push({ sdg: { equals: Number(filters.sdg) } })
  if (filters.trash) and.push({ deletedAt: { exists: true } })
  return { and }
}

async function load() {
  loading.value = true
  try {
    result.value = await api.get<Paginated<Post>>('/posts', { where: where(), sort: '-publishedAt', limit: 20, page: page.value, depth: 1, trash: filters.trash ? 'true' : undefined })
    picked.value = new Set()
    const [n, a, e] = await Promise.all(POST_TYPES.map(t => api.get<{ totalDocs: number }>('/posts/count', { where: { type: { equals: t.value } } })))
    counts.value = { news: n!.totalDocs, announcements: a!.totalDocs, events: e!.totalDocs }
  }
  finally {
    loading.value = false
  }
}

watch([type, () => filters.state, () => filters.sdg, () => filters.trash, page], load, { immediate: true })
let timer: ReturnType<typeof setTimeout> | undefined
watch(() => filters.q, () => { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; load() }, 350) })
watch(type, () => { page.value = 1; filters.trash = false })

function toggle(id: number) {
  const s = new Set(picked.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  picked.value = s
}
const allPicked = computed(() => !!result.value?.docs.length && result.value.docs.every(d => picked.value.has(d.id)))
function toggleAll() {
  picked.value = allPicked.value ? new Set() : new Set(result.value?.docs.map(d => d.id))
}

async function setHidden(p: Post) {
  await api.patch(`/posts/${p.id}`, { hidden: !p.hidden })
  p.hidden = !p.hidden
  flash(p.hidden ? 'Saytdan vaqtinça yaşirildi' : 'Saytda yana körinadi')
}

async function bulk(data: Record<string, unknown>, done: string) {
  const ids = [...picked.value]
  if (!ids.length) return
  await api.patch('/posts', data, { where: { id: { in: ids.join(',') } } })
  flash(done)
  await load()
}

async function bulkTrash() {
  const ids = [...picked.value]
  if (!ids.length || !confirm(`${ids.length} ta post savatga taşlansinmi? 30 kun içida qaytariş mumkin.`)) return
  await api.del('/posts', { where: { id: { in: ids.join(',') } } })
  flash('Savatga taşlandi')
  await load()
}

async function restore(p: Post) {
  await api.patch(`/posts/${p.id}`, { deletedAt: null }, { trash: 'true' })
  flash('Savatdan qaytarildi')
  await load()
}

function flash(text: string) {
  message.value = text
  setTimeout(() => { if (message.value === text) message.value = '' }, 2600)
}

const siteLink = (p: Post) => `${SITE_URL}/${meta.value.path}/${p.slug}`
const authorName = (p: Post) => (p.author && typeof p.author === 'object' ? p.author.name : '—')
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Yangiliklar, e’lonlar va tadbirlar</h1>
        <p class="mt-1.5 text-[15px] text-muted">Saytdagi barça postlar. Öçirilgani savatda turadi — qaytariş mumkin.</p>
      </div>
      <RouterLink :to="`/postlar/${type}/yangi`" class="btn-primary h-[46px]"><Icon name="plus" :size="16" />{{ meta.label }} qöşiş</RouterLink>
    </div>

    <section class="card overflow-hidden">
      <div role="tablist" aria-label="Post turi" class="flex flex-wrap gap-1 border-b border-line px-4 pt-2.5">
        <button
          v-for="t in POST_TYPES" :key="t.value" type="button" role="tab" :aria-selected="t.value === type && !filters.trash"
          class="-mb-px h-[46px] px-4 text-sm font-semibold" :class="t.value === type && !filters.trash ? 'text-ink shadow-[inset_0_-3px_0_var(--color-brand-700)]' : 'text-muted'"
          @click="filters.trash = false; router.push(`/postlar/${t.value}`)"
        >
          {{ t.plural }} <span class="ml-1.5 rounded-full px-1.5 py-0.5 text-xs" :class="t.value === type && !filters.trash ? 'bg-brand-700 text-white' : 'bg-[#F0EEF6] text-muted'">{{ counts[t.value] ?? '…' }}</span>
        </button>
        <button type="button" role="tab" :aria-selected="filters.trash" class="-mb-px h-[46px] px-4 text-sm font-semibold" :class="filters.trash ? 'text-ink shadow-[inset_0_-3px_0_var(--color-brand-700)]' : 'text-muted'" @click="filters.trash = true">Savat</button>
      </div>

      <div class="flex flex-wrap items-center gap-2.5 p-4">
        <label class="flex h-10 min-w-[220px] flex-1 items-center gap-2 rounded-[10px] border border-field px-3 text-muted">
          <Icon name="search" :size="15" />
          <input v-model="filters.q" aria-label="Sarlavha böyiça qidiriş" placeholder="Sarlavha böyiça qidiriş (4 tilda)…" class="min-w-0 flex-1 bg-transparent text-[13px] outline-none">
        </label>
        <select v-model="filters.state" aria-label="Holati" class="field h-10! w-auto!">
          <option value="">Barça holatlar</option>
          <option value="published">Naşr qilingan</option>
          <option value="draft">Qoralama</option>
          <option value="scheduled">Rejalaştirilgan</option>
          <option value="hidden">Yaşirilgan</option>
        </select>
        <select v-model="filters.sdg" aria-label="BRM" class="field h-10! w-auto!">
          <option value="">BRM: hammasi</option>
          <option value="0">BRMga kirmaydi</option>
          <option v-for="(n, i) in SDG_NAMES" :key="i" :value="String(i + 1)">BRM {{ i + 1 }} — {{ n }}</option>
        </select>
      </div>

      <div v-if="picked.size" class="mx-4 mb-3 flex flex-wrap items-center gap-2.5 rounded-xl bg-night px-3.5 py-2.5 text-sm text-white">
        <b class="mr-auto">{{ picked.size }} ta tanlandi</b>
        <button type="button" class="h-[34px] rounded-[9px] bg-mint px-3 text-[13px] font-bold text-night" @click="bulk({ status: 'published' }, 'Naşr qilindi')">Naşr qiliş</button>
        <button type="button" class="h-[34px] rounded-[9px] border border-white/25 px-3 text-[13px] font-semibold" @click="bulk({ status: 'draft' }, 'Qoralamaga ötkazildi')">Qoralamaga</button>
        <button type="button" class="h-[34px] rounded-[9px] border border-white/25 px-3 text-[13px] font-semibold" @click="bulk({ hidden: true }, 'Saytdan yaşirildi')">Saytdan yaşiriş</button>
        <button type="button" class="h-[34px] rounded-[9px] border border-white/25 px-3 text-[13px] font-semibold" @click="bulk({ hidden: false }, 'Saytda yana körinadi')">Qayta körsatiş</button>
        <button type="button" class="h-[34px] rounded-[9px] border border-white/25 px-3 text-[13px] font-semibold" @click="bulkTrash">Savatga</button>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[1120px] border-collapse text-sm">
          <thead>
            <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
              <th class="w-11 py-3 pl-4"><input type="checkbox" class="size-[18px] accent-brand-800" :checked="allPicked" aria-label="Hammasini tanlaş" @change="toggleAll"></th>
              <th class="px-3 py-3 font-semibold">Post</th>
              <th class="px-3 py-3 font-semibold">BRM</th>
              <th class="px-3 py-3 font-semibold">Tillar</th>
              <th class="px-3 py-3 font-semibold">Muallif</th>
              <th class="px-3 py-3 font-semibold">Holati</th>
              <th class="px-3 py-3 font-semibold">Saytda</th>
              <th class="px-3 py-3 font-semibold">Naşr vaqti</th>
              <th class="py-3 pr-4 pl-3"><span class="sr-only">Amallar</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !result"><td colspan="9" class="px-4 py-10 text-center text-muted">Yuklanmoqda…</td></tr>
            <tr v-else-if="result && !result.docs.length"><td colspan="9" class="px-4 py-10 text-center text-muted">{{ filters.trash ? 'Savat böş.' : 'Heç narsa topilmadi.' }}</td></tr>
            <tr v-for="p in result?.docs" :key="p.id" class="border-t border-[#F0EEF6] hover:bg-[#FAF9FD]" :class="picked.has(p.id) && 'bg-[#F7F6FD]'">
              <td class="py-3 pl-4"><input type="checkbox" class="size-[18px] accent-brand-800" :checked="picked.has(p.id)" :aria-label="`Tanlaş: ${p.title.uz}`" @change="toggle(p.id)"></td>
              <td class="max-w-[440px] px-3 py-3">
                <span class="flex items-center gap-3" :class="p.hidden && 'opacity-55'">
                  <span class="h-11 w-16 shrink-0 overflow-hidden rounded-lg bg-brand-100">
                    <img v-if="mediaUrl(p.cover)" :src="mediaUrl(p.cover)!" alt="" class="size-full object-cover">
                  </span>
                  <span class="min-w-0">
                    <RouterLink :to="`/postlar/${p.type}/${p.id}`" class="line-clamp-2 leading-snug font-semibold">{{ p.title.uz || p.title.ru || p.title.en || p.title.zh }}</RouterLink>
                    <span class="mt-0.5 block text-xs text-subtle">{{ p.category && typeof p.category === 'object' ? p.category.name.uz : '' }}</span>
                  </span>
                </span>
              </td>
              <td class="px-3 py-3">
                <span v-if="p.sdg" :title="`BRM ${p.sdg} — ${SDG_NAMES[p.sdg - 1]}`" class="grid size-7 place-items-center rounded-lg text-xs font-bold text-white" :style="{ background: SDG_COLORS[p.sdg - 1] }">{{ p.sdg }}</span>
                <span v-else class="text-subtle">—</span>
              </td>
              <td class="px-3 py-3 whitespace-nowrap">
                <span class="flex gap-[3px]">
                  <span
                    v-for="l in LANGS" :key="l.code" :title="`${l.label}: ${['böş', 'qisman', 'töliq'][langFill(p, l.code) * 2]}`"
                    class="rounded-md px-1.5 py-0.5 text-[11px] font-bold"
                    :class="langFill(p, l.code) === 1 ? 'bg-[#DDFBF0] text-[#0B5A43]' : langFill(p, l.code) ? 'bg-[#FEF3DC] text-[#8A5A00]' : 'bg-canvas text-[#B8B4C8]'"
                  >{{ l.short }}</span>
                </span>
              </td>
              <td class="px-3 py-3 text-[13px] whitespace-nowrap">{{ authorName(p) }}</td>
              <td class="px-3 py-3 whitespace-nowrap"><span class="chip" :class="STATE_BADGE[postState(p)].cls">{{ STATE_BADGE[postState(p)].label }}</span></td>
              <td class="px-3 py-3 whitespace-nowrap">
                <button
                  type="button" :aria-pressed="!!p.hidden" :title="p.hidden ? 'Saytda qayta körsatiş' : 'Saytdan vaqtinça yaşiriş'"
                  class="inline-flex h-8 items-center gap-1.5 rounded-full px-2.5 text-xs font-semibold"
                  :class="p.hidden ? 'border border-[#C7CCDD] bg-[#EEF0F6] text-[#3D4466]' : 'border border-[#BFEBDD] bg-white text-[#0B5A43]'"
                  :disabled="filters.trash" @click="setHidden(p)"
                >
                  <Icon :name="p.hidden ? 'eyeOff' : 'eye'" :size="15" />{{ p.hidden ? 'Yaşirilgan' : 'Körinadi' }}
                </button>
              </td>
              <td class="px-3 py-3 text-[13px] whitespace-nowrap text-muted tabular-nums">{{ dateTime(p.publishedAt) }}</td>
              <td class="py-3 pr-4 pl-3 text-right whitespace-nowrap">
                <template v-if="filters.trash">
                  <button type="button" class="btn-ghost h-8! px-3! text-xs!" @click="restore(p)">Qaytariş</button>
                </template>
                <template v-else>
                  <RouterLink :to="`/postlar/${p.type}/${p.id}`" class="inline-grid size-[34px] place-items-center rounded-[9px] border border-line text-muted hover:border-brand-700 hover:text-brand-700" aria-label="Tahrirlaş"><Icon name="edit" :size="15" /></RouterLink>
                  <a v-if="postState(p) === 'published' && !p.hidden" :href="siteLink(p)" target="_blank" rel="noopener" class="ml-1 inline-grid size-[34px] place-items-center rounded-[9px] border border-line text-muted hover:border-brand-700 hover:text-brand-700" aria-label="Saytda köriş"><Icon name="external" :size="15" /></a>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="result && result.totalPages > 1" class="flex flex-wrap items-center justify-between gap-2.5 border-t border-[#F0EEF6] px-4 py-3.5 text-[13px] text-muted">
        <span>{{ (result.page - 1) * result.limit + 1 }}–{{ Math.min(result.page * result.limit, result.totalDocs) }} / {{ result.totalDocs }}</span>
        <nav aria-label="Sahifalar" class="flex gap-1">
          <button
            v-for="n in result.totalPages" :key="n" type="button" :aria-current="n === page ? 'page' : undefined"
            class="grid h-[34px] min-w-[34px] place-items-center rounded-[9px] px-2 font-semibold" :class="n === page ? 'bg-brand-800 text-white' : 'border border-field text-ink'"
            @click="page = n"
          >{{ n }}</button>
        </nav>
      </div>
    </section>

    <div v-if="message" role="status" class="fixed right-6 bottom-6 z-50 rounded-2xl bg-night px-4 py-3 text-sm font-semibold text-white shadow-xl">{{ message }}</div>
  </div>
</template>
