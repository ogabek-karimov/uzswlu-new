<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { relative } from '@/lib/format'
import Icon from './Icon.vue'

// Qo'ng'iroqcha (har qanday rol): o'qilmaganlar soni belgi ustida, bosilsa — oxirgi bildirishnomalar.
// Faqat o'z bildirishnomalari (/panel/notifications). Har 60 soniyada va oyna qayta ochilganda yangilanadi.
type Note = { id: number; kind: 'role' | 'post' | 'application' | 'security' | 'system'; title: string; body: string | null; link: string | null; read: boolean; createdAt: string }
const router = useRouter()
const open = ref(false)
const unread = ref(0)
const docs = ref<Note[]>([])
const root = ref<HTMLElement>()
const ICON = { role: 'users', post: 'news', application: 'file', security: 'shield', system: 'settings' } as const

async function load() {
  try {
    const res = await api.get<{ unread: number; docs: Note[] }>('/panel/notifications', { limit: 15 })
    unread.value = res.unread
    docs.value = res.docs
  }
  catch { /* tarmoq xatosi — keyingi safar */ }
}
async function readAll() {
  await api.post('/panel/notifications', {})
  docs.value = docs.value.map(d => ({ ...d, read: true }))
  unread.value = 0
}
async function go(n: Note) {
  if (!n.read) {
    await api.post('/panel/notifications', { ids: [n.id] })
    n.read = true
    unread.value = Math.max(0, unread.value - 1)
  }
  open.value = false
  if (n.link) router.push(n.link)
}
function toggle() {
  open.value = !open.value
  if (open.value) load()
}
const outside = (e: MouseEvent) => { if (open.value && root.value && !root.value.contains(e.target as Node)) open.value = false }
const visible = () => { if (document.visibilityState === 'visible') load() }
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  load()
  timer = setInterval(load, 60_000)
  document.addEventListener('click', outside)
  document.addEventListener('visibilitychange', visible)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('click', outside)
  document.removeEventListener('visibilitychange', visible)
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button" class="relative grid size-[42px] place-items-center rounded-xl border border-line text-ink transition-colors hover:border-brand-700 hover:text-brand-700"
      :aria-label="unread ? `Bildirişnomalar: ${unread} ta yangi` : 'Bildirişnomalar'" :aria-expanded="open" @click.stop="toggle"
    >
      <svg viewBox="0 0 24 24" class="size-[19px]" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>
      <span v-if="unread" class="absolute -top-1.5 -right-1.5 grid h-5 min-w-5 place-items-center rounded-full bg-red-600 px-1 text-[11px] font-bold text-white ring-2 ring-white">{{ unread > 99 ? '99+' : unread }}</span>
    </button>
    <div v-if="open" class="absolute right-0 z-40 mt-2 w-[min(360px,calc(100vw-32px))] overflow-hidden rounded-2xl border border-line bg-white shadow-xl">
      <div class="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <b class="text-sm">Bildirişnomalar</b>
        <button v-if="unread" type="button" class="text-xs font-semibold text-brand-700 hover:underline" @click="readAll">Hammasi öqildi</button>
      </div>
      <p v-if="!docs.length" class="px-4 py-8 text-center text-sm text-muted">Hozirça bildirişnoma yöq</p>
      <ul v-else class="max-h-[60vh] overflow-y-auto">
        <li v-for="n in docs" :key="n.id">
          <button type="button" class="flex w-full gap-3 border-b border-[#F0EEF6] px-4 py-3 text-left last:border-0 hover:bg-canvas" :class="!n.read && 'bg-brand-50/60'" @click="go(n)">
            <span class="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg" :class="n.read ? 'bg-[#F1F0F5] text-muted' : 'bg-brand-100 text-brand-700'"><Icon :name="ICON[n.kind]" :size="15" /></span>
            <span class="min-w-0 flex-1">
              <span class="block text-[13px] leading-snug" :class="n.read ? 'text-ink' : 'font-semibold text-ink'">{{ n.title }}</span>
              <span v-if="n.body" class="mt-0.5 block truncate text-xs text-muted">{{ n.body }}</span>
              <span class="mt-0.5 block text-[11px] text-subtle">{{ relative(n.createdAt) }}</span>
            </span>
            <span v-if="!n.read" class="mt-2 size-2 shrink-0 rounded-full bg-brand-700" aria-label="yangi" />
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
