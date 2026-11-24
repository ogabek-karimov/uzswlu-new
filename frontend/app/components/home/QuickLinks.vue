<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()
const NuxtLink = resolveComponent('NuxtLink')
const { data: home } = await useHomeData()

// Kartalar admin paneldagi «Tezkor xizmatlar» sahifasidan keladi. Ikonkalar sayt paketiga yig'ilishi uchun ruxsat etilgan nomlar
// shu yerda LITERAL qatorlar bilan yozilgan (admin panel va backend `apps/content/quick_links.py` bilan bir xil bo'lishi shart).
const ALLOWED = [
  'lucide:message-square-text',
  'lucide:graduation-cap',
  'lucide:database',
  'lucide:mail',
  'lucide:briefcase-business',
  'lucide:sprout',
  'lucide:book-a',
  'app:akt-lugat',
  'lucide:smartphone',
  'lucide:globe',
  'lucide:calendar-days',
  'lucide:file-text',
  'lucide:library',
  'lucide:phone',
  'lucide:users',
  'lucide:video',
  'lucide:map-pin',
  'lucide:award',
  'lucide:life-buoy',
]
// Rasm-belgilar (ilova logolari): kalit → rasm
const IMAGE_ICONS: Record<string, string> = { 'app:akt-lugat': '/images/quick/akt-lugat.webp' }
// Rangli «ilova belgisi» plitkalari (BRM va ilova logolari kabi): har xizmatga o'z rangi — gradient fon, oq belgi, rangli soya.
// Ro'yxatda yo'q belgi — tartib bo'yicha zaxira ranglardan
const TILE: Record<string, [string, string]> = {
  'lucide:message-square-text': ['#7C5CFF', '#4F35D2'],
  'lucide:graduation-cap': ['#1FB6FF', '#0A6FD6'],
  'lucide:database': ['#14C38E', '#0A8F6B'],
  'lucide:globe': ['#14C38E', '#0A8F6B'],
  'lucide:mail': ['#FF8A4C', '#E8483B'],
  'lucide:briefcase-business': ['#FFB020', '#F07A0B'],
  'lucide:book-a': ['#FF5C8A', '#D6336C'],
  'lucide:smartphone': ['#22C5D9', '#0E8FA3'],
  'lucide:calendar-days': ['#8B7CF6', '#5B45E0'],
  'lucide:file-text': ['#5B8CFF', '#2F5BDB'],
  'lucide:library': ['#B67CFF', '#7B3FE0'],
  'lucide:phone': ['#2DD4A0', '#0E9F74'],
  'lucide:users': ['#FF7A59', '#E2473A'],
  'lucide:video': ['#FF4D6D', '#C9184A'],
  'lucide:map-pin': ['#F25C54', '#C0392B'],
  'lucide:award': ['#FFC53D', '#E58E00'],
  'lucide:life-buoy': ['#4CC9F0', '#3A7BD5'],
}
const SPARE: [string, string][] = [['#7C5CFF', '#4F35D2'], ['#1FB6FF', '#0A6FD6'], ['#14C38E', '#0A8F6B'], ['#FF8A4C', '#E8483B'], ['#FFB020', '#F07A0B']]
function tile(icon: string, i: number) {
  const [a, b] = TILE[icon] ?? SPARE[i % SPARE.length]!
  return { background: `linear-gradient(140deg, ${a} 0%, ${b} 100%)`, boxShadow: `0 10px 20px -10px ${b}, inset 0 1px 0 rgb(255 255 255 / 0.35)` }
}
// Katta ekranda barcha nomlar bir qatorga sig'sa (≤ 18 belgi) — nom ostidagi bo'sh qator olib tashlanadi; uzunroq (ruscha) — kartalar tekis turishi uchun 2 qator joy qoladi
const shortTitles = computed(() => links.value.every(l => (l.title ?? '').length <= 18))
const links = computed(() => (home.value?.quickLinks ?? []).map(q => ({ ...q, icon: ALLOWED.includes(q.icon) ? q.icon : 'lucide:globe' })))

// Telefonda kartalar yonga suriladi (karusel): strelkalar bir karta kengligiga suradi
const track = ref<HTMLElement>()
const edge = reactive({ start: true, end: false })
function measure() {
  const el = track.value
  if (!el) return
  edge.start = el.scrollLeft < 8
  edge.end = el.scrollLeft + el.clientWidth >= el.scrollWidth - 8
}
function slide(dir: 1 | -1) {
  const el = track.value
  if (!el) return
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  el.scrollBy({ left: dir * el.clientWidth * 0.8, behavior: reduce ? 'auto' : 'smooth' })
}
onMounted(measure)
watch(links, () => nextTick(measure))
</script>

<template>
  <section v-if="links.length" class="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8 lg:pt-20" aria-labelledby="quick-title">
    <div class="mb-8 flex items-end justify-between gap-6">
      <div>
        <h2 id="quick-title" class="section-title font-display text-3xl leading-tight font-semibold tracking-tight sm:text-4xl">{{ t('quick.title') }}</h2>
      </div>
    </div>
    <div>
      <ul ref="track" class="-mx-4 flex snap-x snap-mandatory scroll-px-4 gap-3 overflow-x-auto overscroll-x-contain px-4 pb-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:mx-0 sm:grid sm:grid-cols-4 sm:overflow-visible sm:px-0 sm:pb-0 lg:grid-cols-7" @scroll.passive="measure">
        <li data-reveal-item v-for="(link, i) in links" :key="link.id" class="group/li min-w-[62%] shrink-0 snap-start min-[480px]:min-w-[44%] sm:min-w-0">
          <component
            :is="link.external ? 'a' : NuxtLink"
            v-bind="link.external ? { href: link.url, target: '_blank', rel: 'noopener' } : { to: localePath(link.url) }"
            class="group relative flex h-full flex-col items-center gap-3 overflow-hidden rounded-3xl border border-line bg-white px-4 pt-6 pb-5 text-center shadow-[0_1px_0_rgba(19,17,47,0.04)] transition duration-300 group-hover/li:-translate-y-1 hover:border-brand-200 hover:shadow-[0_24px_44px_-30px_rgb(19_17_47/0.4)] focus-visible:-translate-y-1 lg:px-2.5 motion-reduce:transition-none motion-reduce:group-hover/li:translate-y-0"
          >
            <!-- O'ng yuqori burchakdagi strelka — faqat sichqoncha/fokusda chiqadi: tashqi havola ↗, sayt ichida → -->
            <Icon
              :name="link.external ? 'lucide:arrow-up-right' : 'lucide:arrow-right'"
              class="absolute top-4 right-4 size-4 text-brand-700 opacity-0 transition duration-300 group-hover:translate-x-0 group-hover:opacity-100 group-focus-visible:opacity-100 motion-reduce:transition-none"
              :class="link.external ? 'translate-y-1 -translate-x-1 group-hover:translate-y-0' : '-translate-x-1'"
            />
            <!-- Belgi: markazda, katta. Ilova logosi — rasm; BRM — 17 rangli halqa (menyudagidek); qolganlari — ikonka -->
            <span v-if="IMAGE_ICONS[link.icon]" class="relative block size-14 overflow-hidden rounded-2xl shadow-[0_8px_18px_-10px_rgb(19_17_47/0.5)] ring-1 ring-line origin-bottom transition duration-300 group-hover:scale-110 group-hover:shadow-[0_12px_24px_-14px_rgb(19_17_47/0.35)] motion-reduce:transition-none motion-reduce:group-hover:transform-none">
              <img :src="IMAGE_ICONS[link.icon]" alt="" width="56" height="56" loading="lazy" class="size-full object-cover">
            </span>
            <span v-else-if="link.icon === 'lucide:sprout'" class="relative grid size-14 place-items-center rounded-2xl bg-white shadow-[0_8px_18px_-10px_rgb(19_17_47/0.5)] ring-1 ring-line origin-bottom transition duration-300 group-hover:scale-110 group-hover:shadow-[0_12px_24px_-14px_rgb(19_17_47/0.35)] motion-reduce:transition-none motion-reduce:group-hover:transform-none">
              <NavGroupIcon id="sdg" class="size-10" />
            </span>
            <span v-else class="relative grid size-14 place-items-center overflow-hidden rounded-2xl text-white origin-bottom transition duration-300 group-hover:scale-110 motion-reduce:transition-none motion-reduce:group-hover:transform-none" :style="tile(link.icon, i)">
              <!-- yuqoridan tushadigan yengil yaltiroq — ilova belgisi hissi -->
              <span aria-hidden="true" class="absolute inset-x-0 top-0 h-1/2 bg-gradient-to-b from-white/25 to-transparent" />
              <Icon :name="link.icon" class="relative text-[30px] drop-shadow-[0_1px_1px_rgb(0_0_0/0.15)]" />
            </span>
            <span>
              <span class="block min-h-[2lh] text-[15px] font-semibold text-ink" :class="shortTitles && 'lg:min-h-0'">{{ link.title }}</span>
              <span v-if="link.text" class="mt-0.5 line-clamp-3 min-h-[3lh] text-[13px] leading-snug text-muted">{{ link.text }}</span>
            </span>
            <!-- ustiga olib borilganda chapdan o'ngga o'sadigan indigo chiziq -->
            <span class="pointer-events-none absolute inset-x-4 bottom-0 h-0.5 origin-left scale-x-0 rounded-full bg-brand-200 transition-transform duration-300 group-hover:scale-x-100 group-focus-visible:scale-x-100 motion-reduce:transition-none lg:inset-x-5" aria-hidden="true" />
          </component>
        </li>
      </ul>
      <div v-if="links.length > 2" class="mt-3 flex justify-center gap-3 sm:hidden">
        <button type="button" class="grid size-11 place-items-center rounded-full border border-line bg-white text-ink transition disabled:opacity-35" :disabled="edge.start" :aria-label="t('quick.prev')" @click="slide(-1)">
          <Icon name="lucide:chevron-left" class="size-5" />
        </button>
        <button type="button" class="grid size-11 place-items-center rounded-full border border-line bg-white text-ink transition disabled:opacity-35" :disabled="edge.end" :aria-label="t('quick.next')" @click="slide(1)">
          <Icon name="lucide:chevron-right" class="size-5" />
        </button>
      </div>
    </div>
  </section>
</template>
