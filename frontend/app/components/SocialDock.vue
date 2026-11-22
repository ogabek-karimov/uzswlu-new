<script setup lang="ts">
// Chap chetdagi panel (eski saytdagidek): ijtimoiy tarmoqlar va «O'quv binolari».
// Barcha ekranlarda chetga yig'ilgan: faqat › tilcha ko'rinadi. Chap chetdagi sezgir zonaga yoki panelga sichqoncha kelsa chiqadi,
// ketsa 0,4 s dan keyin yopiladi; tilcha bosilsa ochiladi/yopiladi; Tab bilan kelinsa ham ochiladi.
// Sessiyada birinchi ochilgan sahifada 2,5 s ko'rinib turadi (panel borligini bildirish uchun). Telefonda bu havolalar mobil menyuda.
const { t } = useI18n()
const localePath = useLocalePath()
const route = useRoute()
const { data: site } = await useSiteData()

const socials = computed(() => sortSocials(site.value?.socials ?? []))
// «O'quv binolari» belgisi — admin paneldan (Sozlamalar → Binolar va xarita) ko'rsatiladi/yashiriladi
const showBuildings = computed(() => site.value?.showBuildings !== false)
const open = ref(false)      // tilcha bilan ochilgan (qayta bosilguncha turadi)
const hover = ref(false)     // sichqoncha panelda yoki chap chetdagi zonada
const peek = ref(false)      // birinchi tanishtiruv
let leaveTimer: ReturnType<typeof setTimeout> | undefined
function enter() {
  clearTimeout(leaveTimer)
  hover.value = true
}
function leave() {
  clearTimeout(leaveTimer)
  leaveTimer = setTimeout(() => (hover.value = false), 400)
}
watch(() => route.fullPath, () => {
  open.value = false
  hover.value = false
})
onMounted(() => {
  try {
    if (sessionStorage.getItem('dock-peek')) return
    sessionStorage.setItem('dock-peek', '1')
  }
  catch { return }
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
  peek.value = true
  setTimeout(() => (peek.value = false), 2500)
})
onBeforeUnmount(() => clearTimeout(leaveTimer))
const shown = computed(() => open.value || hover.value || peek.value)

// Joylashuv: butun ekranning emas, sticky header OSTIDAGI bo'sh joyning o'rtasida (header ostida qolib ketmasin);
// joy yetmasa panel sig'adigan darajada kichrayadi (60% gacha). Header balandligi aylantirishda o'zgaradi — kuzatib boriladi.
const navEl = ref<HTMLElement>()
const dockTop = ref<number | null>(null)
const dockScale = ref(1)
let raf = 0
function place() {
  raf = 0
  const header = document.querySelector('[data-site-header]')
  const top = Math.max(0, header?.getBoundingClientRect().bottom ?? 0)
  const avail = window.innerHeight - top - 16
  const listH = navEl.value?.querySelector('ul')?.offsetHeight ?? 0
  dockScale.value = listH > avail && listH > 0 ? Math.max(0.6, avail / listH) : 1
  dockTop.value = Math.round(top + (window.innerHeight - top) / 2)
}
const schedule = () => { if (!raf) raf = requestAnimationFrame(place) }
onMounted(() => {
  place()
  window.addEventListener('scroll', schedule, { passive: true })
  window.addEventListener('resize', schedule, { passive: true })
})
onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('scroll', schedule)
  window.removeEventListener('resize', schedule)
})
watch(() => route.fullPath, () => nextTick(schedule))
// Tilcha: ko'rinib turgan bo'lsa — yopadi (hover/peek ham), aks holda ochib qo'yadi
function toggle() {
  if (shown.value) {
    open.value = false; hover.value = false; peek.value = false
    ;(document.activeElement as HTMLElement | null)?.blur()   // fokus qolsa :has(:focus-visible) ochiq ushlab turmasin
  }
  else open.value = true
}

const item = 'group relative grid size-14 [@media(max-height:680px)]:size-11 place-items-center rounded-2xl outline-none transition-transform duration-200 focus-visible:ring-2 focus-visible:ring-brand-400'
// Yorliq ikonka OSTIDA chiqadi, foni tarmoq rangida (Telegram — moviy, YouTube — qizil, …) (ikonkaning chap chetidan, ekrandan chiqib ketmaydi), keyingi ikonka va tilcha ustida turadi
const tip = 'pointer-events-none absolute top-full left-0 z-20 mt-1 -translate-y-1 rounded-lg px-2.5 py-1 text-xs font-semibold whitespace-nowrap text-white opacity-0 shadow-lg transition duration-200 group-hover:translate-y-0 group-hover:opacity-100 group-focus-visible:translate-y-0 group-focus-visible:opacity-100'
</script>

<template>
  <!-- Chap chetdagi ko'rinmas sezgir zona: panelga aniq tegish shart emas -->
  <div aria-hidden="true" class="fixed top-1/2 left-0 z-[39] hidden h-[min(440px,80vh)] w-6 -translate-y-1/2 md:block print:hidden" @mouseenter="enter" @mouseleave="leave" />
  <nav
    ref="navEl"
    class="social-dock fixed top-1/2 left-0 z-40 hidden items-center md:flex print:hidden"
    :style="dockTop !== null ? { top: `${dockTop}px` } : undefined"
    :class="shown && 'is-open'"
    :aria-label="t('social.title')"
    @mouseenter="enter"
    @mouseleave="leave"
  >
    <!-- overflow yo'q: ichki scroll pastda polosa chiqarib, o'ngga chiquvchi yorliqlarni (tip) kesib qo'yardi; past ekranga ixcham o'lcham (max-height:680px) yetadi -->
    <ul class="dock-glass relative z-10 flex origin-left flex-col items-center gap-1.5 rounded-r-3xl py-2.5 pr-2 pl-1.5 [@media(max-height:680px)]:gap-0.5" :style="dockScale < 1 ? { transform: `scale(${dockScale})` } : undefined">
      <li v-for="s in socials" :key="s.network">
        <a :href="s.url" target="_blank" rel="noopener" :class="[item, siteNetworks[s.network].ink]" :aria-label="siteNetworks[s.network].label">
          <span aria-hidden="true" class="absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100" :class="siteNetworks[s.network].fill" />
          <Icon :name="siteNetworks[s.network].icon" class="relative text-[1.85rem] [@media(max-height:680px)]:text-[1.4rem] transition-colors duration-200 group-hover:text-white group-focus-visible:text-white" />
          <span aria-hidden="true" :class="[tip, siteNetworks[s.network].fill]">{{ siteNetworks[s.network].label }}</span>
        </a>
      </li>
      <li v-if="socials.length && showBuildings" aria-hidden="true" class="mx-auto my-0.5 h-px w-6 bg-line" />
      <li v-if="showBuildings">
        <NuxtLink :to="localePath('/oquv-binolari')" :class="[item, 'text-brand-700']" :aria-label="t('social.buildings')">
          <span aria-hidden="true" class="absolute inset-0 rounded-[inherit] bg-brand-700 opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100" />
          <img src="/images/icon-building.webp" alt="" width="128" height="61" loading="lazy" class="relative h-auto w-[3.25rem] [@media(max-height:680px)]:w-10 max-w-none drop-shadow-[0_2px_3px_rgb(0_0_0/0.25)] transition-transform duration-200 group-hover:scale-110">
          <span aria-hidden="true" :class="[tip, 'bg-brand-700']">{{ t('social.buildings') }}</span>
        </NuxtLink>
      </li>
    </ul>
    <button
      type="button"
      class="dock-toggle relative -ml-px h-16 w-6 place-items-center overflow-hidden rounded-r-2xl text-brand-900"
      :aria-expanded="shown"
      :aria-label="shown ? t('social.hide') : t('social.show')"
      @click="toggle"
    >
      <Icon :name="shown ? 'lucide:chevron-left' : 'lucide:chevron-right'" class="dock-chevron relative text-lg [stroke-width:3]" :class="!shown && 'is-nudging'" />
    </button>
  </nav>
</template>

<style scoped>
/* Panel foni: oq shaffof shisha — ikonkalar bitta plastinkada, tilcha uning davomi */
.dock-glass {
  background: rgb(255 255 255 / 0.6);
  backdrop-filter: blur(14px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 0.75);
  border-left: 0;
  box-shadow: 0 18px 40px -24px rgb(56 43 133 / 0.45), inset 0 1px 0 rgb(255 255 255 / 0.8);
}
/* Yig'ilgan holat: faqat tilcha (1.5rem) ko'rinadi */
.social-dock {
  transform: translate(calc(-100% + 1.5rem), -50%);   /* tilcha kengligi (w-6) */
  transition: transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
}
/* Ochiq: tilcha/hover/tanishtiruv yoki klaviatura fokusi (sichqoncha bosgan tugmaning fokusi panelni ochiq qoldirmasin) */
.social-dock:has(:focus-visible),
.social-dock.is-open {
  transform: translateY(-50%);
}
/* Tilcha: biroz shaffof oltin-amber gradient (shisha), to'q indigo strelka, yumshoq «nafas oluvchi» yog'du, ustidan o'tuvchi nur; yopiq holatda strelka o'ngga «undaydi» */
.dock-toggle {
  display: grid;
  background: linear-gradient(170deg, rgb(255 214 102 / 0.92), rgb(252 182 40 / 0.9) 55%, rgb(240 150 20 / 0.9));
  backdrop-filter: blur(10px);
  border: 1px solid rgb(255 255 255 / 0.45);
  border-left: 0;
  box-shadow: 0 10px 24px -10px rgb(200 120 0 / 0.6);
  animation: dock-glow 2.8s ease-in-out infinite;
  transition: filter 0.2s;
}
.dock-toggle::after {
  content: '';
  position: absolute;
  inset: -40% 0;
  background: linear-gradient(180deg, transparent, rgb(255 255 255 / 0.45), transparent);
  transform: translateY(-120%);
  animation: dock-shine 3.6s ease-in-out infinite;
}
.dock-toggle:hover {
  filter: brightness(1.15) saturate(1.1);
}
.is-nudging {
  animation: dock-nudge 1.8s ease-in-out infinite;
}
@keyframes dock-glow {
  0%, 100% { box-shadow: 0 10px 24px -10px rgb(200 120 0 / 0.6), 0 0 0 0 rgb(255 190 50 / 0); }
  50% { box-shadow: 0 10px 24px -10px rgb(200 120 0 / 0.6), 0 0 18px 4px rgb(255 190 50 / 0.55); }
}
@keyframes dock-shine {
  0%, 55% { transform: translateY(-120%); }
  85%, 100% { transform: translateY(120%); }
}
@keyframes dock-nudge {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(3px); }
}
@media (prefers-reduced-motion: reduce) {
  .social-dock {
    transition: none;
  }
  .dock-toggle, .dock-toggle::after, .is-nudging {
    animation: none;
  }
}
</style>
