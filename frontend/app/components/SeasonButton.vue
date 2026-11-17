<script setup lang="ts">
// Joriy fasl belgisi (asosiy menyu boshida): fasl nomi + belgi; bosilsa animatsiya
const { t } = useI18n()

// dek-fev qish, mar-may bahor, iyun-avg yoz, sen-noy kuz (shimoliy yarimshar)
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
</script>

<template>
  <button
    type="button"
    class="season-btn relative inline-flex h-10 shrink-0 items-center gap-2 rounded-full bg-gradient-to-br px-3.5 text-white shadow-md outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
    :class="[season.bg, spin && 'is-spin']"
    :aria-label="t(`topbar.season.${season.key}`)"
    @click="burst"
  >
    <Icon :name="season.icon" class="season-ico relative text-[1.25rem]" />
    <span class="relative text-xs font-extrabold tracking-wider whitespace-nowrap uppercase">{{ t(`topbar.season.${season.key}`) }}</span>
    <span aria-hidden="true" class="season-ring" />
  </button>
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
</style>
