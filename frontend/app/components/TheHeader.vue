<script setup lang="ts">
import type { MenuGroup } from '#shared/types/api'

const { t } = useI18n()
const localePath = useLocalePath()
const route = useRoute()
const router = useRouter()
const { data: site } = await useSiteData()

const groups = computed<MenuGroup[]>(() => site.value?.menu ?? [])

// ── Ochiq menyu: bo'lim id'si, 'more' ("⋯") yoki null ─────────────────────
const open = ref<string | null>(null)
const mobileOpen = ref(false)
const scrolled = ref(false)
let closeTimer: ReturnType<typeof setTimeout> | undefined

function show(key: string) {
  clearTimeout(closeTimer)
  open.value = key
}
function scheduleClose() {
  clearTimeout(closeTimer)
  closeTimer = setTimeout(() => (open.value = null), 140)
}
function toggle(key: string) {
  clearTimeout(closeTimer)
  open.value = open.value === key ? null : key
}

// 4 tagacha havolali bo'lim — kichik ochiluvchi ro'yxat, kattasi — to'liq mega-panel
const isSmall = (g: MenuGroup) => g.links.length <= 4 && !g.links.some(l => l.sdg)
const activeMega = computed(() => {
  const g = groups.value.find(g => g.id === open.value)
  return g && !g.url && !isSmall(g) ? g : undefined
})

// ── "Priority+" navigatsiya: sig'maganlari "⋯" ichiga o'tadi ─────────────
const navEl = ref<HTMLElement>()
const measureEl = ref<HTMLElement>()
const visibleCount = ref(Number.POSITIVE_INFINITY)
const GAP = 2
const MORE_WIDTH = 48

const visibleGroups = computed(() => groups.value.slice(0, visibleCount.value))
const hiddenGroups = computed(() => groups.value.slice(visibleCount.value))

function measure() {
  const nav = navEl.value
  const ruler = measureEl.value
  if (!nav || !ruler) return
  const available = nav.clientWidth
  const widths = Array.from(ruler.children, el => (el as HTMLElement).offsetWidth)
  const total = widths.reduce((sum, w) => sum + w + GAP, 0)
  if (total <= available) {
    visibleCount.value = widths.length
    return
  }
  let used = MORE_WIDTH
  let count = 0
  for (const w of widths) {
    if (used + w + GAP > available) break
    used += w + GAP
    count++
  }
  visibleCount.value = count
}

let resizeObserver: ResizeObserver | undefined

function onScroll() {
  scrolled.value = window.scrollY > 8
}
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    open.value = null
    mobileOpen.value = false
  }
}

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('keydown', onKeydown)
  resizeObserver = new ResizeObserver(() => measure())
  if (navEl.value) resizeObserver.observe(navEl.value)
  // Shrift kattalashtirilganda (A+) o'lchamlar o'zgaradi — o'lchagich ham kuzatiladi
  if (measureEl.value) resizeObserver.observe(measureEl.value)
  measure()
  document.fonts?.ready.then(measure)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('keydown', onKeydown)
  resizeObserver?.disconnect()
  document.documentElement.style.overflow = ''
})

// Til almashganda sarlavhalar uzunligi o'zgaradi
watch(groups, () => nextTick(measure))

watch(() => route.fullPath, () => {
  open.value = null
  mobileOpen.value = false
})

watch(mobileOpen, (value) => {
  document.documentElement.style.overflow = value ? 'hidden' : ''
})

const query = ref('')
function submitSearch() {
  const q = query.value.trim()
  router.push({ path: localePath('/search'), query: q ? { q } : undefined })
}

const navItem = 'inline-flex h-10 items-center gap-1 whitespace-nowrap rounded-full px-3.5 text-[15px] font-medium text-ink/85 transition-colors hover:bg-brand-50 hover:text-ink'
</script>

<template>
  <header
    class="sticky top-0 z-50 border-b transition-[background-color,box-shadow,border-color] duration-300"
    :class="scrolled || open || mobileOpen
      ? 'border-line bg-paper/95 shadow-[0_10px_30px_-18px_rgba(19,17,47,0.35)] backdrop-blur-md'
      : 'border-transparent bg-paper'"
    @mouseleave="scheduleClose"
  >
    <!-- 1-qator: logo, qidiruv, amallar -->
    <div class="mx-auto flex h-[72px] max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8" @mouseenter="scheduleClose">
      <NuxtLink :to="localePath('/')" class="flex shrink-0 items-center gap-3" :aria-label="t('university.name')">
        <BrandMark class="size-12" />
        <span class="text-[15px] font-semibold text-ink sm:hidden">{{ t('university.short') }}</span>
        <span class="hidden leading-tight sm:block">
          <!-- Sayt nomi — bitta butun nom: ikkala qator bir xil, qalin -->
          <span class="block text-[15px] font-semibold text-ink">{{ t('university.line1') }}</span>
          <span class="block text-[15px] font-semibold text-ink">{{ t('university.line2') }}</span>
        </span>
      </NuxtLink>

      <form role="search" class="mx-auto hidden w-full max-w-sm xl:block" @submit.prevent="submitSearch">
        <label for="header-search" class="sr-only">{{ t('hero.searchLabel') }}</label>
        <div class="flex h-11 items-center gap-2 rounded-full border border-line bg-white px-4 transition focus-within:border-brand-300 focus-within:ring-4 focus-within:ring-brand-100">
          <Icon name="lucide:search" class="size-4 shrink-0 text-muted" />
          <input
            id="header-search"
            v-model="query"
            type="search"
            autocomplete="off"
            :placeholder="t('nav.searchPlaceholder')"
            class="min-w-0 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-muted/80 focus-visible:outline-none"
          >
        </div>
      </form>

      <div class="ml-auto flex items-center gap-1.5 xl:ml-0">
        <LangSwitcher />
        <NuxtLink
          :to="localePath('/search')"
          class="grid size-10 place-items-center rounded-full text-ink transition-colors hover:bg-brand-50 xl:hidden"
          :aria-label="t('nav.search')"
        >
          <Icon name="lucide:search" class="size-5" />
        </NuxtLink>
        <NuxtLink
          :to="localePath('/qabul-20262027')"
          class="hidden items-center gap-1.5 rounded-full bg-accent-400 px-5 py-2.5 text-sm font-semibold whitespace-nowrap text-ink transition-colors hover:bg-accent-300 sm:inline-flex"
        >
          {{ t('nav.admission') }}
          <Icon name="lucide:arrow-up-right" class="size-4" />
        </NuxtLink>
        <LoginMenu />
        <button
          type="button"
          class="grid size-10 place-items-center rounded-full text-ink transition-colors hover:bg-brand-50 md:hidden"
          :aria-expanded="mobileOpen"
          aria-controls="mobile-menu"
          :aria-label="mobileOpen ? t('nav.close') : t('nav.menu')"
          @click="mobileOpen = !mobileOpen"
        >
          <Icon :name="mobileOpen ? 'lucide:x' : 'lucide:menu'" class="size-6" />
        </button>
      </div>
    </div>

    <!-- 2-qator: asosiy menyu (planshet va kompyuter) -->
    <div class="hidden border-t border-line/70 md:block">
      <div class="mx-auto flex h-14 max-w-7xl items-center overflow-x-clip px-4 sm:px-6 lg:px-8">
        <nav ref="navEl" class="relative min-w-0 flex-1" :aria-label="t('nav.menu')">
          <!-- O'lchagich: hamma bo'limlar ko'rinmas holda — qaysilari sig'ishini hisoblash uchun -->
          <ul ref="measureEl" aria-hidden="true" class="pointer-events-none invisible absolute top-0 left-0 flex gap-0.5">
            <li v-for="group in groups" :key="group.id">
              <span :class="navItem">{{ group.title }}<span v-if="!group.url" class="inline-block size-4" /></span>
            </li>
          </ul>

          <ul class="flex items-center gap-0.5">
            <li
              v-for="(group, i) in visibleGroups"
              :key="group.id"
              class="relative"
              @mouseenter="group.url ? scheduleClose() : show(group.id)"
            >
              <NuxtLink v-if="group.url" :to="localePath(group.url)" :class="navItem">{{ group.title }}</NuxtLink>
              <button
                v-else
                type="button"
                :class="[navItem, open === group.id && 'bg-brand-50 text-ink']"
                :aria-expanded="open === group.id"
                aria-haspopup="true"
                @click="toggle(group.id)"
              >
                {{ group.title }}
                <Icon name="lucide:chevron-down" class="size-4 opacity-60 transition-transform duration-200" :class="open === group.id && 'rotate-180'" />
              </button>

              <!-- Kichik bo'limlar (Ta'lim yo'nalishlari, Video) uchun ixcham ro'yxat -->
              <Transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="opacity-0 -translate-y-1"
                leave-active-class="transition duration-100 ease-in"
                leave-to-class="opacity-0 -translate-y-1"
              >
                <div
                  v-if="open === group.id && !group.url && isSmall(group)"
                  class="absolute top-full z-10 mt-2 w-80 rounded-2xl border border-line bg-white p-2 shadow-[0_24px_48px_-20px_rgba(19,17,47,0.4)]"
                  :class="i > visibleGroups.length / 2 ? 'right-0' : 'left-0'"
                >
                  <NuxtLink
                    v-if="group.overview"
                    :to="localePath(group.overview)"
                    class="group/ov flex items-center justify-between rounded-xl px-3 pt-2.5 pb-1 font-display text-lg font-semibold text-ink transition-colors hover:text-brand-700"
                    :title="t('nav.overview')"
                  >
                    {{ group.title }}
                    <Icon name="lucide:arrow-right" class="size-4 text-brand-600 transition-transform group-hover/ov:translate-x-1" />
                  </NuxtLink>
                  <p v-if="group.description" class="px-3 pt-2 pb-1 text-xs leading-relaxed text-muted">{{ group.description }}</p>
                  <NavMenuLink
                    v-for="link in group.links"
                    :key="link.url"
                    :link="link"
                    class="group/link flex items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] font-medium text-ink transition-colors hover:bg-brand-50"
                  >
                    <span class="grid size-9 place-items-center rounded-lg bg-brand-50 text-brand-700 transition-colors group-hover/link:bg-brand-800 group-hover/link:text-accent-400">
                      <Icon :name="groupIcon(group.id)" class="size-[18px]" />
                    </span>
                    <span class="flex-1">{{ link.title }}</span>
                    <Icon name="lucide:arrow-right" class="size-4 text-brand-600 opacity-0 transition-opacity group-hover/link:opacity-100" />
                  </NavMenuLink>
                </div>
              </Transition>
            </li>

            <!-- "⋯" — sig'magan bo'limlar -->
            <li v-if="hiddenGroups.length" @mouseenter="show('more')">
              <button
                type="button"
                class="grid size-10 place-items-center rounded-full transition-colors"
                :class="open === 'more' ? 'bg-ink text-white' : 'bg-brand-50 text-ink hover:bg-brand-100'"
                :aria-expanded="open === 'more'"
                aria-haspopup="true"
                :aria-label="`${t('nav.more')}: ${hiddenGroups.map(g => g.title).join(', ')}`"
                :title="t('nav.more')"
                @click="toggle('more')"
              >
                <Icon name="lucide:ellipsis" class="size-5" />
              </button>
            </li>
          </ul>
        </nav>

        <!-- Maxsus imkoniyatlar (shrift, kontrast) — ko'rishi zaif foydalanuvchilar oson topishi uchun menyu qatorida -->
        <A11yControls variant="nav" class="ml-4 shrink-0" />
      </div>
    </div>

    <!-- Mega-panel (katta bo'limlar) -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <div
        v-if="activeMega"
        class="absolute inset-x-0 top-full hidden max-h-[calc(100dvh-10rem)] overflow-y-auto border-t border-line bg-paper shadow-[0_30px_60px_-30px_rgba(19,17,47,0.35)] md:block"
        @mouseenter="show(activeMega.id)"
      >
        <NavMegaPanel :group="activeMega" />
      </div>
    </Transition>

    <!-- "⋯" paneli -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <div
        v-if="open === 'more' && hiddenGroups.length"
        class="absolute inset-x-0 top-full hidden max-h-[calc(100dvh-10rem)] overflow-y-auto border-t border-line bg-paper shadow-[0_30px_60px_-30px_rgba(19,17,47,0.35)] md:block"
        @mouseenter="show('more')"
      >
        <NavMorePanel :groups="hiddenGroups" />
      </div>
    </Transition>

    <!-- Mobil menyu -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="opacity-0"
    >
      <div
        v-if="mobileOpen"
        id="mobile-menu"
        class="absolute inset-x-0 top-full h-[calc(100dvh-4.5rem)] overflow-y-auto border-t border-line bg-paper md:hidden"
      >
        <nav class="mx-auto max-w-7xl px-4 pt-2 pb-10 sm:px-6" :aria-label="t('nav.menu')">
          <template v-for="group in groups" :key="group.id">
            <NuxtLink
              v-if="group.url"
              :to="localePath(group.url)"
              class="flex items-center gap-3 border-b border-line py-4 text-lg font-semibold text-ink"
            >
              <Icon :name="groupIcon(group.id)" class="size-5 text-brand-600" />
              {{ group.title }}
            </NuxtLink>
            <details v-else class="group border-b border-line">
              <summary class="flex cursor-pointer list-none items-center gap-3 py-4 text-lg font-semibold text-ink [&::-webkit-details-marker]:hidden">
                <Icon :name="groupIcon(group.id)" class="size-5 text-brand-600" />
                <span class="flex-1">{{ group.title }}</span>
                <span class="text-xs font-medium text-muted">{{ group.links.length }}</span>
                <Icon name="lucide:chevron-down" class="size-5 text-muted transition-transform group-open:rotate-180" />
              </summary>
              <NuxtLink
                v-if="group.overview"
                :to="localePath(group.overview)"
                class="mb-3 flex items-center justify-between rounded-2xl bg-brand-50 px-4 py-3 text-[15px] font-semibold text-brand-800"
              >
                {{ t('nav.overview') }}
                <Icon name="lucide:arrow-right" class="size-4" />
              </NuxtLink>
              <NavSdgGrid v-if="group.links.some(l => l.sdg)" :links="group.links" compact class="pb-5" />
              <ul v-else class="grid gap-0.5 pb-4 sm:grid-cols-2">
                <li v-for="link in group.links" :key="link.url">
                  <NavMenuLink
                    :link="link"
                    class="flex items-center gap-3 rounded-xl px-2 py-2.5 text-[15px] hover:bg-brand-50"
                    :class="link.highlight ? 'font-semibold text-brand-800' : 'text-ink/85'"
                  >
                    <span class="size-1.5 shrink-0 rounded-full" :class="link.highlight ? 'bg-accent-500' : 'bg-brand-300'" />
                    <span class="flex-1">{{ link.title }}</span>
                    <span v-if="link.file" class="rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-bold text-red-700 uppercase">{{ link.file }}</span>
                  </NavMenuLink>
                </li>
              </ul>
            </details>
          </template>

          <NuxtLink
            :to="localePath('/qabul-20262027')"
            class="mt-6 flex items-center justify-center gap-2 rounded-full bg-accent-400 px-5 py-3.5 font-semibold text-ink"
          >
            {{ t('nav.admission') }}
            <Icon name="lucide:arrow-up-right" class="size-4" />
          </NuxtLink>
        </nav>
      </div>
    </Transition>
  </header>
</template>
