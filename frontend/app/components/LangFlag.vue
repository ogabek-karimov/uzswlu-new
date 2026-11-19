<script setup lang="ts">
// Til tanlagich uchun dumaloq bayroqcha (uz — O'zbekiston, ru — Rossiya, en — Buyuk Britaniya, zh — Xitoy). Ichki SVG, tashqi so'rovsiz.
defineProps<{ code: string }>()

function star(cx: number, cy: number, r: number, rot = -90): string {
  return Array.from({ length: 10 }, (_, i) => {
    const rad = ((rot + i * 36) * Math.PI) / 180
    const k = i % 2 === 0 ? r : r * 0.382
    return `${(cx + k * Math.cos(rad)).toFixed(2)},${(cy + k * Math.sin(rad)).toFixed(2)}`
  }).join(' ')
}
const uzStars = [[13.2, 3.4], [15.6, 3.4], [10.8, 5.6], [13.2, 5.6], [15.6, 5.6]].map(([x, y]) => star(x!, y!, 0.9))
const cnSmall = [[10, 2], [12, 4], [12, 7], [10, 9]].map(([x, y]) => star(x!, y!, 1, -50))
</script>

<template>
  <span class="inline-grid shrink-0 overflow-hidden rounded-full ring-1 ring-black/10" aria-hidden="true">
    <svg v-if="code === 'uz'" viewBox="0 0 24 24" class="size-full">
      <rect width="24" height="8" fill="#0099b5" />
      <rect y="8" width="24" height="8" fill="#fff" />
      <rect y="16" width="24" height="8" fill="#1eb53a" />
      <rect y="7.6" width="24" height="0.8" fill="#ce1126" />
      <rect y="15.6" width="24" height="0.8" fill="#ce1126" />
      <circle cx="6" cy="4" r="2.8" fill="#fff" />
      <circle cx="7.1" cy="4" r="2.5" fill="#0099b5" />
      <polygon v-for="(p, i) in uzStars" :key="i" :points="p" fill="#fff" />
    </svg>
    <svg v-else-if="code === 'ru'" viewBox="0 0 24 24" class="size-full">
      <rect width="24" height="8" fill="#fff" />
      <rect y="8" width="24" height="8" fill="#0039a6" />
      <rect y="16" width="24" height="8" fill="#d52b1e" />
    </svg>
    <svg v-else-if="code === 'en'" viewBox="15 0 30 30" class="size-full">
      <rect width="60" height="30" fill="#012169" />
      <path d="M0 0 60 30M60 0 0 30" stroke="#fff" stroke-width="6" />
      <path d="M0 0 60 30M60 0 0 30" stroke="#c8102e" stroke-width="2" />
      <path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10" />
      <path d="M30 0v30M0 15h60" stroke="#c8102e" stroke-width="6" />
    </svg>
    <svg v-else-if="code === 'zh'" viewBox="0 0 20 20" class="size-full">
      <rect width="20" height="20" fill="#ee1c25" />
      <polygon :points="star(5, 5, 3)" fill="#ffde00" />
      <polygon v-for="(p, i) in cnSmall" :key="i" :points="p" fill="#ffde00" />
    </svg>
  </span>
</template>
