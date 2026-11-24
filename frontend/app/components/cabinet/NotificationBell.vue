<script setup lang="ts">
import type { CabinetNotification, CabinetNotifications } from '#shared/types/api'

// Qo'ng'iroqcha — sayt sarlavhasida, profil belgisi yonida: faqat kabinetga kirgan xodimga (mehmonda umuman chiqmaydi).
// O'qilmaganlar soni belgi ustida, bosilsa — oxirgi bildirishnomalar (faqat o'zi: rol o'zgardi, postini boshqa odam o'zgartirdi…).
// Rolsiz xodimda ro'yxat bo'sh. Kirgan bo'lsa har 60 soniyada va sahifaga qaytilganda yangilanadi.
const { t } = useI18n()
const { open, root } = useDropdown()
const data = ref<CabinetNotifications>({ unread: 0, docs: [] })
const ICON: Record<CabinetNotification['kind'], string> = { role: 'lucide:shield-check', post: 'lucide:newspaper', application: 'lucide:file-text', system: 'lucide:bell' }

async function load() {
  try {
    data.value = await $fetch<CabinetNotifications>('/api/me/notifications')
  }
  catch { /* jim */ }
}
async function read(ids?: number[]) {
  await $fetch('/api/me/notifications', { method: 'POST', body: ids ? { ids } : {} }).catch(() => null)
  const set = ids ? new Set(ids) : null
  data.value = { unread: set ? Math.max(0, data.value.unread - ids!.filter(i => data.value.docs.some(d => d.id === i && !d.read)).length) : 0, docs: data.value.docs.map(d => (!set || set.has(d.id) ? { ...d, read: true } : d)) }
}
watch(open, (o) => { if (o) load() })
const visible = () => { if (document.visibilityState === 'visible' && data.value.signedIn) load() }
let timer: ReturnType<typeof setInterval> | undefined
onMounted(async () => {
  await load()
  if (!data.value.signedIn) return // mehmon — bir marta tekshiriladi, keyin so'rov yuborilmaydi
  timer = setInterval(load, 60_000)
  document.addEventListener('visibilitychange', visible)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', visible)
})
const fmt = (iso: string) => new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
</script>

<template>
  <div v-if="data.signedIn" ref="root" class="relative">
    <button
      type="button" class="relative grid size-10 place-items-center rounded-full border border-ink/15 bg-white text-ink transition-colors hover:border-brand-700 hover:text-brand-700"
      :aria-label="data.unread ? t('cabinet.notes.labelNew', { n: data.unread }) : t('cabinet.notes.title')" :aria-expanded="open" @click="open = !open"
    >
      <Icon name="lucide:bell" class="size-5" />
      <span v-if="data.unread" class="absolute -top-1 -right-1 grid h-5 min-w-5 place-items-center rounded-full bg-[#e5484d] px-1 text-[11px] font-bold text-white ring-2 ring-white">{{ data.unread > 99 ? '99+' : data.unread }}</span>
    </button>
    <div v-if="open" class="absolute right-0 z-40 mt-2 w-[min(360px,calc(100vw-32px))] overflow-hidden rounded-2xl border border-line bg-white shadow-[0_24px_48px_-20px_rgba(19,17,47,0.4)]">
      <div class="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <b class="text-sm text-ink">{{ t('cabinet.notes.title') }}</b>
        <button v-if="data.unread" type="button" class="text-xs font-semibold text-brand-700 hover:underline" @click="read()">{{ t('cabinet.notes.readAll') }}</button>
      </div>
      <p v-if="!data.docs.length" class="px-4 py-8 text-center text-sm text-muted">{{ t('cabinet.notes.empty') }}</p>
      <ul v-else class="max-h-[60vh] overflow-y-auto">
        <li v-for="n in data.docs" :key="n.id">
          <button type="button" class="flex w-full gap-3 border-b border-line/60 px-4 py-3 text-left last:border-0 hover:bg-paper" :class="!n.read && 'bg-brand-50/60'" @click="!n.read && read([n.id])">
            <span class="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg" :class="n.read ? 'bg-paper text-muted' : 'bg-brand-100 text-brand-700'"><Icon :name="ICON[n.kind]" class="size-4" /></span>
            <span class="min-w-0 flex-1">
              <span class="block text-[13px] leading-snug text-ink" :class="!n.read && 'font-semibold'">{{ n.title }}</span>
              <span v-if="n.body" class="mt-0.5 block truncate text-xs text-muted">{{ n.body }}</span>
              <span class="mt-0.5 block text-[11px] text-muted">{{ fmt(n.createdAt) }}</span>
            </span>
            <span v-if="!n.read" class="mt-2 size-2 shrink-0 rounded-full bg-brand-700" />
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
