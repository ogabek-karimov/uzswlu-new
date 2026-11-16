<script setup lang="ts">
const { t } = useI18n()

// Joriy fasl (shimoliy yarimshar): dek-fev qish, mar-may bahor, iyun-avg yoz, sen-noy kuz
const SEASONS = [
  { key: 'winter', icon: 'lucide:snowflake', bg: 'from-sky-500 to-blue-700' },
  { key: 'spring', icon: 'lucide:flower-2', bg: 'from-emerald-400 to-teal-600' },
  { key: 'summer', icon: 'lucide:sun', bg: 'from-amber-400 to-orange-500' },
  { key: 'autumn', icon: 'lucide:leaf', bg: 'from-orange-400 to-orange-600' },
] as const
const season = computed(() => SEASONS[Math.floor(((new Date().getMonth() + 1) % 12) / 3)]!)
</script>

<template>
  <div
    class="season-badge pointer-events-none absolute top-[14%] left-0 z-20 inline-flex items-center gap-2.5 overflow-hidden rounded-r-full bg-gradient-to-r py-2.5 pr-5 pl-3 text-white shadow-[0_12px_30px_-10px_rgba(0,0,0,.55)] sm:gap-3 sm:py-3.5 sm:pr-8 sm:pl-5"
    :class="season.bg"
    role="note"
  >
    <Icon :name="season.icon" class="season-icon size-5 shrink-0 sm:size-7" />
    <span class="text-xs font-extrabold tracking-wider whitespace-nowrap uppercase sm:text-lg">{{ t(`topbar.season.${season.key}`) }}</span>
    <span class="season-shine" aria-hidden="true" />
  </div>
</template>

<style scoped>
.season-badge {
  animation: season-in 0.9s cubic-bezier(0.22, 1, 0.36, 1) 0.5s both;
}
.season-icon {
  transform-origin: 50% 90%;
  animation: season-sway 3.6s ease-in-out 1.4s infinite;
}
.season-shine {
  position: absolute;
  inset: 0 auto 0 0;
  width: 40%;
  background: linear-gradient(105deg, transparent, rgb(255 255 255 / 0.35), transparent);
  transform: translateX(-160%) skewX(-18deg);
  animation: season-shine 5s ease-in-out 1.6s infinite;
}
@keyframes season-in {
  from { transform: translateX(-105%); opacity: 0; }
  to { transform: none; opacity: 1; }
}
@keyframes season-sway {
  0%, 100% { transform: rotate(-12deg); }
  50% { transform: rotate(14deg) translateY(-1px); }
}
@keyframes season-shine {
  0%, 60% { transform: translateX(-160%) skewX(-18deg); }
  100% { transform: translateX(420%) skewX(-18deg); }
}
@media (prefers-reduced-motion: reduce) {
  .season-badge, .season-icon, .season-shine { animation: none; }
  .season-shine { display: none; }
}
</style>
