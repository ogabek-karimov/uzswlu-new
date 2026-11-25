<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { auth, roleLabel } from '@/lib/auth'
import { siteSettings } from '@/lib/settings'
import { SITE_URL } from '@/lib/constants'
import Icon, { type ICONS } from './Icon.vue'
import TelegramIcon from './TelegramIcon.vue'

defineProps<{ open: boolean }>()
defineEmits<{ close: [] }>()

type Item = { to: string; label: string; icon: keyof typeof ICONS; section?: string; superOnly?: boolean; soon?: boolean }
const route = useRoute()

// Muharrir (kichik admin) faqat o'ziga ruxsat berilgan bo'limlarni ko'radi
const groups: { label: string; items: Item[] }[] = [
  { label: 'Asosiy', items: [
    { to: '/', label: 'Boşqaruv paneli', icon: 'dashboard', section: 'dashboard' },
    { to: '/statistika', label: 'Statistika', icon: 'stats', superOnly: true },
    { to: '/arizalar', label: 'Arizalar', icon: 'docs', superOnly: true },
  ] },
  { label: 'Kontent', items: [
    { to: '/postlar/news', label: 'Yangiliklar', icon: 'news', section: 'news' },
    { to: '/postlar/announcements', label: 'E’lonlar', icon: 'announcements', section: 'announcements' },
    { to: '/postlar/events', label: 'Tadbirlar', icon: 'events', section: 'events' },
    { to: '/sahifalar', label: 'Sahifalar', icon: 'pages', section: 'pages' },
    { to: '/tezkor-xizmatlar', label: 'Tezkor xizmatlar', icon: 'quick', section: 'quick-links' },
    { to: '/telefonlar', label: 'Telefonlar', icon: 'phone', section: 'phones' },
    { to: '/qabul-yillari', label: 'Qabul yillari', icon: 'calendar', section: 'admission' },
    { to: '/bolimlar', label: 'Bölimlar', icon: 'staff', section: 'units' },
    { to: '/haqoratli-sozlar', label: 'Haqoratli sözlar', icon: 'shield', section: 'rude-words' },
    { to: '/karusel', label: 'Boş sahifa karuseli', icon: 'carousel', superOnly: true },
    { to: '/media', label: 'Media kutubxona', icon: 'media', section: 'media' },
    { to: '/hujjatlar', label: 'Hujjatlar', icon: 'docs', section: 'documents' },
    { to: '/video', label: 'Video darsliklar', icon: 'video', section: 'videos' },
    { to: '/onlayn-kameralar', label: 'Onlayn kameralar', icon: 'cctv', section: 'pages' },
  ] },
  { label: 'Tuzilma', items: [
    { to: '/fakultetlar', label: 'Fakultetlar', icon: 'faculties', section: 'faculties' },
    { to: '/kafedralar', label: 'Kafedralar', icon: 'departments', section: 'departments' },
    { to: '/rahbariyat', label: 'Rahbariyat', icon: 'leaders', section: 'leaders' },
    { to: '/xodimlar', label: 'Xodimlar', icon: 'staff', section: 'staff' },
    { to: '/brm', label: 'BRM', icon: 'sdg', section: 'sdg' },
    { to: '/ramzlar', label: 'Ramzlar', icon: 'symbols', superOnly: true },
  ] },
  { label: 'Tizim', items: [
    { to: '/rollar', label: 'Rollar va ruxsatlar', icon: 'users', superOnly: true },
    { to: '/ruxsatlar', label: 'Ruxsatlar kutubxonasi', icon: 'shield', superOnly: true },
    { to: '/foydalanuvchilar', label: 'Foydalanuvçilar va rollar', icon: 'users', superOnly: true },
    { to: '/kirish-tarixi', label: 'Kiriş tarixi', icon: 'logins', superOnly: true },
    { to: '/faollik', label: 'Faollik jurnali', icon: 'activity', superOnly: true },
    { to: '/sozlamalar', label: 'Sayt sozlamalari', icon: 'settings', superOnly: true },
  ] },
]

const visible = computed(() => {
  const isSuper = auth.isSuper.value
  const ok = (i: Item) => isSuper || (!i.superOnly && (!i.section || auth.can(i.section)))
  return groups
    .map(g => ({ ...g, items: g.items.filter(ok) }))
    .filter(g => g.items.length)
})

function active(to: string) {
  if (to === '/') return route.path === '/'
  return route.path === to || route.path.startsWith(`${to}/`)
}
</script>

<template>
  <!-- Telefonda: ustiga chiqadigan menyu -->
  <div v-if="open" class="fixed inset-0 z-30 bg-night/50 lg:hidden" aria-hidden="true" @click="$emit('close')" />
  <aside
    class="fixed inset-y-0 left-0 z-40 flex w-[272px] flex-col gap-1 overflow-y-auto bg-night px-3.5 pt-5 pb-6 text-white/72 transition-transform lg:sticky lg:top-0 lg:h-dvh lg:translate-x-0"
    :class="open ? 'translate-x-0' : '-translate-x-full'"
  >
    <RouterLink to="/" class="flex items-center gap-3 border-b border-white/8 px-2.5 pb-[18px] text-white">
      <img src="/mark.webp" alt="" class="size-[42px] object-contain">
      <span class="leading-tight">
        <span class="block text-base font-bold">ÖzDJTU</span>
        <span class="block text-xs text-white/55">Boşqaruv paneli</span>
      </span>
    </RouterLink>

    <template v-for="group in visible" :key="group.label">
      <p class="mx-3 mt-[18px] mb-1.5 text-[11px] font-bold tracking-[0.14em] text-white/38 uppercase">{{ group.label }}</p>
      <nav class="flex flex-col gap-0.5">
        <RouterLink
          v-for="item in group.items"
          :key="item.to"
          :to="item.to"
          class="flex h-10 items-center gap-3 rounded-xl px-3 text-sm transition hover:bg-white/6 hover:text-white"
          :class="active(item.to) ? 'bg-mint/12 font-semibold text-white' : 'font-medium'"
          @click="$emit('close')"
        >
          <Icon :name="item.icon" :class="active(item.to) ? 'text-mint' : 'text-white/55'" />
          <span class="flex-1">{{ item.label }}</span>
          <span v-if="item.soon" class="rounded-full bg-white/8 px-1.5 py-0.5 text-[10px] font-semibold text-white/45">tez orada</span>
        </RouterLink>
      </nav>
    </template>

    <div class="mt-auto pt-[22px]">
      <a
        v-if="siteSettings.showInAdmin"
        :href="siteSettings.supportUrl"
        target="_blank"
        rel="noopener"
        class="mb-2.5 flex items-center gap-3 rounded-2xl border border-tg/35 bg-gradient-to-br from-tg/22 to-tg/8 px-3.5 py-3 text-white"
      >
        <span class="grid size-9 shrink-0 place-items-center rounded-full bg-white"><TelegramIcon :size="36" /></span>
        <span class="leading-snug">
          <span class="block text-sm font-bold">{{ siteSettings.supportText }}</span>
          <span class="block text-xs text-white/65">Muammo bölsa — Telegram’da yozing</span>
        </span>
      </a>
      <div class="rounded-2xl border border-white/8 bg-white/5 p-3.5">
        <p class="text-xs text-white/50">Sizning rolingiz</p>
        <p class="mt-1 text-sm font-bold text-white">{{ roleLabel(auth.user.value) }}</p>
      </div>
      <a :href="SITE_URL" target="_blank" rel="noopener" class="mt-2.5 flex h-10 items-center justify-center gap-2 rounded-xl border border-white/14 text-[13px] font-semibold text-white">Saytni oçiş ↗</a>
    </div>
  </aside>
</template>
