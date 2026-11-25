<script setup lang="ts">
// Admin paneldagi umumiy qidiruv (sarlavhada doim turadi, Ctrl+K / «/»): bölimlar, sahifalar, yangilik/e’lon/tadbirlar, xodimlar.
// Faqat foydalanuvçining ruxsati bor bölimlar qidiriladi.
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, type I18n, type Paginated } from '@/lib/api'
import { auth } from '@/lib/auth'
import { groups } from '@/lib/nav'
import Icon, { type ICONS } from './Icon.vue'

type Hit = { group: string; label: string; hint?: string; to: string; icon: keyof typeof ICONS }
const router = useRouter()
const q = ref('')
const open = ref(false)
const loading = ref(false)
const active = ref(0)
const remote = ref<Hit[]>([])
const input = ref<HTMLInputElement | null>(null)
const root = ref<HTMLElement | null>(null)

const fold = (s: string) => s.toLowerCase().replace(/[‘’'`ʻʼ]/g, '').replace(/ö/g, 'o').replace(/ğ/g, 'g').replace(/ş/g, 'sh').replace(/ç/g, 'ch')
const ok = (section?: string, superOnly?: boolean) => auth.isSuper.value || (!superOnly && (!section || auth.can(section)))
const title = (t?: I18n | null) => t?.uz || t?.ru || t?.en || ''

const navHits = computed<Hit[]>(() => {
  const w = fold(q.value.trim())
  if (!w) return []
  return groups.flatMap(g => g.items.filter(i => ok(i.section, i.superOnly) && fold(`${i.label} ${g.label}`).includes(w))
    .map(i => ({ group: 'Bölimlar', label: i.label, hint: g.label, to: i.to, icon: i.icon })))
    .slice(0, 6)
})
const hits = computed(() => [...navHits.value, ...remote.value])
const grouped = computed(() => {
  const m = new Map<string, (Hit & { i: number })[]>()
  hits.value.forEach((h, i) => { if (!m.has(h.group)) m.set(h.group, []); m.get(h.group)!.push({ ...h, i }) })
  return [...m.entries()]
})

const TYPES: Record<string, [string, keyof typeof ICONS]> = { news: ['Yangiliklar', 'news'], announcements: ['E’lonlar', 'announcements'], events: ['Tadbirlar', 'events'] }
let seq = 0
let timer: ReturnType<typeof setTimeout> | undefined
watch(q, v => {
  active.value = 0
  clearTimeout(timer)
  const s = v.trim()
  if (s.length < 2) { remote.value = []; loading.value = false; return }
  loading.value = true
  timer = setTimeout(() => search(s), 250)
})

async function search(s: string) {
  const my = ++seq
  const like = (f: string[]) => ({ or: f.map(k => ({ [k]: { like: s } })) })
  const titles = ['title.uz', 'title.ru', 'title.en', 'title.zh']
  const jobs: Promise<Hit[]>[] = []
  if (ok('pages')) {
    jobs.push(api.get<Paginated<{ id: number; title: I18n; slug?: string | null }>>('/pages', { where: like([...titles, 'slug']), limit: 6, depth: 0 })
      .then(r => r.docs.map(p => ({ group: 'Sahifalar', label: title(p.title), hint: p.slug ? `/${p.slug}` : undefined, to: `/sahifalar?id=${p.id}`, icon: 'pages' as const }))))
  }
  const types = Object.keys(TYPES).filter(t => ok(t))
  if (types.length) {
    jobs.push(api.get<Paginated<{ id: number; title: I18n; type: string }>>('/posts', { where: { and: [like(titles), { type: { in: types.join(',') } }] }, sort: '-publishedAt', limit: 8, depth: 0 })
      .then(r => r.docs.map(p => ({ group: TYPES[p.type]?.[0] ?? 'Postlar', label: title(p.title), to: `/postlar/${p.type}/${p.id}`, icon: TYPES[p.type]?.[1] ?? 'news' }))))
  }
  if (ok('staff')) {
    jobs.push(api.get<Paginated<{ id: number; name?: string | null }>>('/staff-profiles', { where: like(['name']), limit: 5, depth: 0 })
      .then(r => r.docs.filter(p => p.name).map(p => ({ group: 'Xodimlar', label: p.name!, to: `/xodimlar?q=${encodeURIComponent(p.name!)}`, icon: 'staff' as const }))))
  }
  const res = await Promise.allSettled(jobs)
  if (my !== seq) return
  remote.value = res.flatMap(r => (r.status === 'fulfilled' ? r.value : []))
  loading.value = false
}

function go(h?: Hit) {
  if (!h) return
  open.value = false
  q.value = ''
  input.value?.blur()
  router.push(h.to)
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown') { e.preventDefault(); active.value = Math.min(active.value + 1, hits.value.length - 1) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); active.value = Math.max(active.value - 1, 0) }
  else if (e.key === 'Enter') { e.preventDefault(); go(hits.value[active.value]) }
  else if (e.key === 'Escape') { open.value = false; input.value?.blur() }
}
watch(active, async i => { await nextTick(); root.value?.querySelector(`[data-i="${i}"]`)?.scrollIntoView({ block: 'nearest' }) })

function hotkey(e: KeyboardEvent) {
  const t = e.target as HTMLElement
  const typing = t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName)
  if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') || (e.key === '/' && !typing)) {
    e.preventDefault()
    input.value?.focus()
    open.value = true
  }
}
const outside = (e: MouseEvent) => { if (!root.value?.contains(e.target as Node)) open.value = false }
onMounted(() => { window.addEventListener('keydown', hotkey); document.addEventListener('mousedown', outside) })
onBeforeUnmount(() => { window.removeEventListener('keydown', hotkey); document.removeEventListener('mousedown', outside); clearTimeout(timer) })
</script>

<template>
  <div ref="root" class="relative min-w-0 flex-1 sm:max-w-[520px]">
    <label for="admin-search" class="sr-only">Admin panel böyiça qidiruv</label>
    <div class="flex h-[42px] items-center gap-2 rounded-xl border border-line bg-canvas px-3 transition focus-within:border-brand-300 focus-within:bg-white focus-within:ring-4 focus-within:ring-brand-100">
      <Icon name="search" :size="16" class="shrink-0 text-muted" />
      <input
        id="admin-search" ref="input" v-model="q" type="search" autocomplete="off" role="combobox"
        :aria-expanded="open && q.trim().length > 0" aria-controls="admin-search-list" aria-autocomplete="list"
        :aria-activedescendant="open && hits.length ? `as-${active}` : undefined"
        placeholder="Qidiruv: bölim, sahifa, yangilik, xodim…"
        class="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-subtle"
        @focus="open = true" @keydown="onKey"
      >
      <kbd class="hidden shrink-0 rounded-md border border-line bg-white px-1.5 py-0.5 text-[11px] font-semibold text-muted md:inline">Ctrl K</kbd>
    </div>
    <div v-if="open && q.trim()" id="admin-search-list" role="listbox" class="absolute inset-x-0 top-full z-40 mt-2 max-h-[min(70vh,520px)] overflow-y-auto rounded-2xl border border-line bg-white p-1.5 shadow-xl sm:min-w-[420px]">
      <template v-for="[g, items] in grouped" :key="g">
        <p class="px-3 pt-2.5 pb-1 text-[11px] font-bold tracking-wider text-subtle uppercase">{{ g }}</p>
        <button
          v-for="h in items" :id="`as-${h.i}`" :key="h.i" type="button" role="option" :data-i="h.i" :aria-selected="active === h.i"
          class="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm" :class="active === h.i ? 'bg-brand-50 text-brand-800' : 'hover:bg-canvas'"
          @mouseenter="active = h.i" @click="go(h)"
        >
          <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-canvas text-muted"><Icon :name="h.icon" :size="15" /></span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-semibold">{{ h.label }}</span>
            <span v-if="h.hint" class="block truncate text-xs text-muted">{{ h.hint }}</span>
          </span>
          <span v-if="active === h.i" aria-hidden="true" class="shrink-0 text-xs font-semibold">↵</span>
        </button>
      </template>
      <p v-if="loading" class="px-3 py-2.5 text-sm text-muted">Qidirilmoqda…</p>
      <p v-else-if="!hits.length" class="px-3 py-2.5 text-sm text-muted">«{{ q.trim() }}» böyiça hech narsa topilmadi.</p>
    </div>
  </div>
</template>
