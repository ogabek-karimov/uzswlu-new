<script setup lang="ts">
// Chap chetdagi panel (eski saytdagidek): ijtimoiy tarmoqlar.
// Keng ekranda (≥1360px) doim ochiq; torroq ekranda kontentni yopmasligi uchun chetga yig'iladi —
// kursor kelsa yoki tilcha bosilsa chiqadi. Telefonda bu havolalar mobil menyuda.
const { t } = useI18n()
const localePath = useLocalePath()
const route = useRoute()
const { data: site } = await useSiteData()

const socials = computed(() => sortSocials(site.value?.socials ?? []))
const open = ref(false)
watch(() => route.fullPath, () => (open.value = false))

// Joriy fasl (shimoliy yarimshar): dek-fev qish, mar-may bahor, iyun-avg yoz, sen-noy kuz
const SEASONS = [
  { key: 'winter', icon: 'lucide:snowflake', bg: 'from-sky-500 to-blue-700' },
  { key: 'spring', icon: 'lucide:flower-2', bg: 'from-emerald-400 to-teal-600' },
  { key: 'summer', icon: 'lucide:sun', bg: 'from-amber-400 to-orange-500' },
  { key: 'autumn', icon: 'lucide:leaf', bg: 'from-orange-400 to-orange-600' },
] as const
const season = computed(() => SEASONS[Math.floor(((new Date().getMonth() + 1) % 12) / 3)]!)
const spin = ref(false)
let spinTimer: ReturnType<typeof setTimeout> | undefined
function burst() {
  spin.value = false
  nextTick(() => {
    spin.value = true
    clearTimeout(spinTimer)
    spinTimer = setTimeout(() => (spin.value = false), 900)
  })
}
onBeforeUnmount(() => clearTimeout(spinTimer))

const item = 'group relative grid size-12 place-items-center rounded-2xl outline-none transition-transform duration-200 focus-visible:ring-2 focus-visible:ring-brand-400'
const tip = 'pointer-events-none absolute top-1/2 left-full z-10 ml-3 -translate-x-1 -translate-y-1/2 rounded-lg bg-ink px-2.5 py-1 text-xs font-semibold whitespace-nowrap text-white opacity-0 shadow-lg transition duration-200 group-hover:translate-x-0 group-hover:opacity-100 group-focus-visible:translate-x-0 group-focus-visible:opacity-100'
</script>

<template>
  <nav class="social-dock fixed top-1/2 left-0 z-40 hidden items-center md:flex print:hidden" :class="open && 'is-open'" :aria-label="t('social.title')">
    <ul class="flex flex-col items-center gap-1.5 rounded-r-[22px] border border-l-0 border-line bg-white p-2 shadow-[0_18px_40px_-22px_rgba(19,17,47,0.5)]">
      <!-- Joriy fasl belgisi: ijtimoiy tarmoqlar tepasida; bosilsa animatsiya -->
      <li class="mb-0.5 w-full border-b border-line pb-2">
        <button type="button" :class="[item, 'season-btn !h-12 !w-full grid-flow-col gap-2 bg-gradient-to-br px-3 text-white shadow-md', season.bg, spin && 'is-spin']" :aria-label="t(`topbar.season.${season.key}`)" @click="burst">
          <Icon :name="season.icon" class="season-ico relative text-[1.5rem]" />
          <span class="relative text-xs font-extrabold tracking-wider whitespace-nowrap uppercase">{{ t(`topbar.season.${season.key}`) }}</span>
          <span aria-hidden="true" class="season-ring" />
        </button>
      </li>
      <li v-for="s in socials" :key="s.network">
        <a :href="s.url" target="_blank" rel="noopener" :class="[item, siteNetworks[s.network].ink]" :aria-label="siteNetworks[s.network].label">
          <span aria-hidden="true" class="absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100" :class="siteNetworks[s.network].fill" />
          <Icon :name="siteNetworks[s.network].icon" class="relative text-[1.5rem] transition-colors duration-200 group-hover:text-white group-focus-visible:text-white" />
          <span aria-hidden="true" :class="tip">{{ siteNetworks[s.network].label }}</span>
        </a>
      </li>
    </ul>
    <button
      type="button"
      class="dock-toggle -ml-px h-14 w-5 place-items-center rounded-r-xl border border-l-0 border-line bg-white text-muted shadow-[0_12px_24px_-16px_rgba(19,17,47,0.5)] transition-colors hover:text-ink"
      :aria-expanded="open"
      :aria-label="open ? t('social.hide') : t('social.show')"
      @click="open = !open"
    >
      <Icon :name="open ? 'lucide:chevron-left' : 'lucide:chevron-right'" class="text-sm" />
    </button>
  </nav>
</template>

<style scoped>
.season-btn {
  animation: season-pop-in 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) 0.4s both;
}
.season-ico {
  animation: season-sway 3.6s ease-in-out 1.4s infinite;
  transform-origin: 50% 85%;
}
.season-ring {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: 0 0 0 2px rgb(251 146 60 / 0.8);
  opacity: 0;
  pointer-events: none;
}
.season-btn:hover .season-ico {
  animation-duration: 1.2s;
}
.season-btn:active {
  transform: scale(0.9);
}
.season-btn.is-spin .season-ico {
  animation: season-spin 0.9s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.season-btn.is-spin .season-ring {
  animation: season-ring 0.8s ease-out;
}
@keyframes season-pop-in {
  from { opacity: 0; transform: scale(0.4) rotate(-90deg); }
  to { opacity: 1; transform: none; }
}
@keyframes season-sway {
  0%, 100% { transform: rotate(-12deg); }
  50% { transform: rotate(14deg); }
}
@keyframes season-spin {
  0% { transform: rotate(0) scale(1); }
  50% { transform: rotate(200deg) scale(1.5); }
  100% { transform: rotate(360deg) scale(1); }
}
@keyframes season-ring {
  0% { opacity: 0.8; transform: scale(1); }
  100% { opacity: 0; transform: scale(2); }
}
@media (prefers-reduced-motion: reduce) {
  .season-btn, .season-ico, .season-btn.is-spin .season-ico, .season-btn.is-spin .season-ring { animation: none; }
}
.social-dock {
  transform: translateY(-50%);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.dock-toggle {
  display: none;
}
/* Tor ekranda chetga yig'iladi: faqat tilcha ko'rinadi */
@media (max-width: 1359.98px) {
  .social-dock {
    transform: translate(calc(-100% + 1.25rem), -50%);
  }
  .social-dock:hover,
  .social-dock:focus-within,
  .social-dock.is-open {
    transform: translateY(-50%);
  }
  .dock-toggle {
    display: grid;
  }
}
@media (prefers-reduced-motion: reduce) {
  .social-dock {
    transition: none;
  }
}
</style>
