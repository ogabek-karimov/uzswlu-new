<script setup lang="ts">
import type { CabinetAdminLink } from '#shared/types/api'

const { t } = useI18n()
const NuxtLinkComp = resolveComponent('NuxtLink')
const { open, root } = useDropdown()

// Kirgan xodimning admin paneldagi bo'limlari («Mening bo'limlarim»): menyu birinchi ochilganda so'raladi (sessiya cookie'si httpOnly —
// kirgan-kirmaganini faqat server biladi). Kirmagan mehmonda hech narsa chiqmaydi. Bo'limga bosilganda 60 soniyalik bir martalik havola olinadi.
const mine = ref<CabinetAdminLink | null>(null)
// Xodim kirgan bo'lsa (sayt serveri `signedIn` beradi; mehmonda false) menyu «Dashboardlar» ro'yxatiga aylanadi (kirish havolalari o'rniga)
const signedIn = computed(() => mine.value?.signedIn === true)
const opening = ref('')
let asked = false
watch(open, async (isOpen) => {
  if (!isOpen || asked) return
  asked = true
  try {
    mine.value = await $fetch<CabinetAdminLink>('/api/me/admin-link', { query: { list: 1 } })
  }
  catch {
    asked = false // tarmoq xatosi — keyingi ochilishda yana urinadi
  }
})
// Saytning o'zida (kabinetda) ishlaydigan bo'limlar: yangilik/e'lon/tadbirga YOZISH ruxsati bo'lsa kabinetdagi «Yangiliklar» menyusi ochiladi.
// Qolganlari (hozircha) admin panelning o'sha sahifasiga o'tadi.
const POST_KEYS = ['news', 'announcements', 'events']
const inSite = (s: { key: string, level: string }) => POST_KEYS.includes(s.key) && s.level === 'write'
const localePath = useLocalePath()
const siteLink = (key: string) => localePath({ path: '/dashboard', query: { bolim: 'news', tur: key } })
async function goPanel(key = '') {
  opening.value = key || '/'
  try {
    const link = await $fetch<CabinetAdminLink>('/api/me/admin-link', { query: key ? { next: key } : {} })
    if (link.url) window.location.assign(link.url)
  }
  finally {
    opening.value = ''
  }
}

// Hozirgi saytdagi kirish manzillari (HEMIS va KPI)
const groups = [
  {
    title: 'auth.staff',
    items: [
      { label: 'auth.hemisStaff', href: 'https://hemis.uzswlu.uz/dashboard/login', icon: 'lucide:database' },
      { label: 'auth.kpi', href: 'https://kpi.uzswlu.uz', icon: 'lucide:gauge' },
    ],
  },
  {
    title: 'auth.students',
    items: [
      { label: 'auth.hemisStudent', href: 'https://student.uzswlu.uz/dashboard/login', icon: 'lucide:graduation-cap' },
    ],
  },
]

const host = (url: string) => new URL(url).host

// Kirgan xodimning dashboardlari: o'z saytimizdagi kabinet, admin panel (rol bo'lsa) va universitetning boshqa tizimlari
const dashboards = computed(() => [
  { key: 'site', label: t('auth.dash.site'), sub: 'uzswlu.uz', icon: 'lucide:layout-grid', to: localePath('/dashboard') },
  { key: 'hemis', label: t('auth.dash.hemis'), sub: 'hemis.uzswlu.uz', icon: 'lucide:database', href: 'https://hemis.uzswlu.uz/dashboard/login' },
  { key: 'kpi', label: t('auth.dash.kpi'), sub: 'kpi.uzswlu.uz', icon: 'lucide:gauge', href: 'https://kpi.uzswlu.uz' },
])
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="grid size-10 place-items-center rounded-full border transition-colors"
      :class="open ? 'border-ink bg-ink text-white' : 'border-ink/15 text-ink hover:border-ink hover:bg-ink hover:text-white'"
      :aria-expanded="open"
      aria-haspopup="true"
      aria-controls="login-menu"
      :aria-label="t('auth.login')"
      :title="t('auth.login')"
      @click="open = !open"
    >
      <Icon name="lucide:user-round" class="size-5" />
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <div
        v-if="open"
        id="login-menu"
        class="absolute top-full right-0 z-[60] mt-2 w-72 rounded-2xl border border-line bg-white p-2 shadow-[0_24px_48px_-20px_rgba(19,17,47,0.4)]"
      >
        <div v-if="signedIn" class="mb-1 border-b border-line pb-2">
          <p class="px-3 pt-2 pb-1 text-[11px] font-semibold tracking-[0.14em] text-muted uppercase">{{ t('auth.dash.title') }}</p>
          <ul>
            <li v-for="d in dashboards" :key="d.key">
              <component
                :is="d.to ? NuxtLinkComp : 'a'" :to="d.to" :href="d.href" :rel="d.href ? 'noopener' : undefined"
                class="group flex items-center gap-3 rounded-xl px-3 py-2 transition-colors hover:bg-brand-50" @click="open = false"
              >
                <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-700 transition-colors group-hover:bg-brand-800 group-hover:text-accent-400"><Icon :name="d.icon" class="size-4" /></span>
                <span class="min-w-0 flex-1"><span class="block text-sm font-semibold text-ink">{{ d.label }}</span><span class="block truncate text-xs text-muted">{{ d.sub }}</span></span>
                <Icon v-if="d.href" name="lucide:arrow-up-right" class="size-3.5 shrink-0 text-muted" />
              </component>
            </li>
            <li v-if="mine?.available">
              <button type="button" class="group flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left transition-colors hover:bg-brand-50 disabled:opacity-60" :disabled="!!opening" @click="goPanel()">
                <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-accent-100 text-accent-700 transition-colors group-hover:bg-brand-800 group-hover:text-accent-400"><Icon name="lucide:shield-check" class="size-4" /></span>
                <span class="min-w-0 flex-1"><span class="block text-sm font-semibold text-ink">{{ t('auth.dash.admin') }}</span><span class="block truncate text-xs text-muted">{{ mine.role }}</span></span>
                <Icon name="lucide:arrow-up-right" class="size-3.5 shrink-0 text-muted" />
              </button>
            </li>
          </ul>
        </div>
        <div v-if="mine?.available" class="mb-1 border-b border-line pb-2">
          <p class="px-3 pt-2 text-[11px] font-semibold tracking-[0.14em] text-muted uppercase">{{ t('auth.mySections') }}</p>
          <p class="truncate px-3 pt-1 text-sm font-semibold text-ink">{{ mine.role }}</p>
          <ul class="max-h-56 overflow-y-auto">
            <li v-for="s in mine.sections" :key="s.key">
              <NuxtLink
                v-if="inSite(s)"
                :to="siteLink(s.key)"
                class="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-sm text-ink transition-colors hover:bg-brand-50"
                @click="open = false"
              >
                <span class="min-w-0 flex-1 truncate">{{ s.label }}</span>
                <span class="shrink-0 rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-semibold text-brand-700">{{ t('auth.levelWrite') }}</span>
              </NuxtLink>
              <button
                v-else
                type="button"
                class="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-sm text-ink transition-colors hover:bg-brand-50 disabled:opacity-60"
                :disabled="!!opening"
                :title="t('auth.inPanel')"
                @click="goPanel(s.key)"
              >
                <span class="min-w-0 flex-1 truncate">{{ s.label }}</span>
                <span class="shrink-0 rounded-full bg-line/60 px-2 py-0.5 text-[10px] font-semibold text-muted">{{ t(s.level === 'write' ? 'auth.levelWrite' : 'auth.levelRead') }}</span>
                <Icon name="lucide:arrow-up-right" class="size-3.5 shrink-0 text-muted" />
              </button>
            </li>
          </ul>
        </div>
        <a v-if="signedIn" href="/logout" class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-ink transition-colors hover:bg-[#fdecec] hover:text-[#8e1b1b]">
          <Icon name="lucide:log-out" class="size-4" />{{ t('cabinet.menu.logout') }}
        </a>
        <template v-else>
        <p class="flex items-center gap-2 px-3 pt-2 pb-1 text-sm font-semibold text-ink">
          <Icon name="lucide:log-in" class="size-4 text-brand-600" />
          {{ t('auth.login') }}
        </p>
        <div v-for="group in groups" :key="group.title" class="mt-1 border-t border-line first-of-type:border-t-0">
          <p class="px-3 pt-3 pb-1 text-[11px] font-semibold tracking-[0.14em] text-muted uppercase">{{ t(group.title) }}</p>
          <ul>
            <li v-for="item in group.items" :key="item.href">
              <a :href="item.href" rel="noopener" class="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-brand-50">
                <span class="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-700 transition-colors group-hover:bg-brand-800 group-hover:text-accent-400">
                  <Icon :name="item.icon" class="size-[18px]" />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block text-sm font-semibold text-ink">{{ t(item.label) }}</span>
                  <span class="block truncate text-xs text-muted">{{ host(item.href) }}</span>
                </span>
                <Icon name="lucide:arrow-up-right" class="size-4 shrink-0 text-muted transition-colors group-hover:text-brand-700" />
              </a>
            </li>
          </ul>
        </div>
        </template>
      </div>
    </Transition>
  </div>
</template>
