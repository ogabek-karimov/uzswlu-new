<script setup lang="ts">
import type { PageChild } from '#shared/types/api'

// Ichki sahifalar kartalari (admin → Sahifalar → «Ichki sahifalar kartalari»), masalan Yoshlar ittifoqi → Zakovat, Futbol…
// Karta: rangli tepa qism + belgi, nom, hujjat tugmalari (PDF yangi oynada oçiladi). Kompyuterda 4 ta ustun.
defineProps<{ items: PageChild[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
// Har kartaga öz rangi (brend palitrasi doirasida)
const TONES = [
  'from-[#5b4bbe] to-[#2a2066]', 'from-[#0e7a5a] to-[#0b3d30]', 'from-[#c2410c] to-[#7c2d12]', 'from-[#0369a1] to-[#0c4a6e]',
  'from-[#7c3aed] to-[#3b0764]', 'from-[#be185d] to-[#6b0f3a]', 'from-[#0f766e] to-[#134e4a]', 'from-[#a16207] to-[#713f12]',
]
</script>

<template>
  <ul class="child-grid mt-12 grid grid-cols-1 gap-4 min-[480px]:grid-cols-2 lg:grid-cols-4">
    <li v-for="(c, i) in items" :key="c.slug" class="child-card group relative flex flex-col overflow-hidden rounded-3xl border border-line bg-white transition duration-300 hover:-translate-y-1.5 hover:border-transparent hover:shadow-[0_26px_50px_-28px_rgb(28_21_72/0.55)]" :style="{ '--i': i }">
      <NuxtLink :to="localePath(c.url)" class="relative flex h-[118px] items-center justify-center overflow-hidden bg-gradient-to-br text-white" :class="TONES[i % TONES.length]" :aria-label="c.title">
        <span aria-hidden="true" class="child-orb" />
        <span aria-hidden="true" class="absolute inset-0 bg-[radial-gradient(rgb(255_255_255/0.14)_1px,transparent_1px)] [background-size:16px_16px] opacity-60" />
        <span class="relative grid size-16 place-items-center rounded-2xl bg-white/15 ring-1 ring-white/25 backdrop-blur-sm transition duration-500 group-hover:scale-110 group-hover:rotate-[-8deg]">
          <Icon :name="`lucide:${c.icon || 'sparkles'}`" class="text-[32px]" />
        </span>
      </NuxtLink>
      <div class="flex flex-1 flex-col p-4">
        <h3 class="leading-snug font-bold text-ink">
          <NuxtLink :to="localePath(c.url)" class="hover:text-brand-700">{{ c.title }}</NuxtLink>
        </h3>
        <ul v-if="c.attachments.length" class="mt-3 flex flex-wrap gap-1.5">
          <li v-for="doc in c.attachments" :key="doc.url">
            <a :href="doc.url" target="_blank" rel="noopener" :title="`${c.title} — ${doc.title} (PDF)`" class="group/doc inline-flex items-center gap-1.5 rounded-xl border border-line bg-paper py-1.5 pr-3 pl-2 text-xs leading-none font-semibold text-ink transition duration-200 hover:-translate-y-0.5 hover:border-brand-800 hover:bg-brand-800 hover:text-white">
              <Icon name="lucide:file-text" class="text-sm text-red-600 group-hover/doc:text-current" />{{ doc.title }}
              <span class="sr-only">— {{ c.title }}, PDF ({{ t('page.ctaNewTab') }})</span>
            </a>
          </li>
        </ul>
        <p v-else class="mt-2 text-[13px] text-muted">{{ t('page.noDocs') }}</p>
      </div>
    </li>
  </ul>
</template>

<style scoped>
/* Kartalar ketma-ket çiqadi, tepadagi nur sekin suzadi */
.child-card { animation: child-in 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both; animation-delay: calc(var(--i) * 70ms); }
@keyframes child-in { from { opacity: 0; transform: translateY(18px); } }
.child-orb {
  position: absolute;
  width: 140px;
  height: 140px;
  right: -40px;
  top: -50px;
  border-radius: 9999px;
  background: rgb(0 252 180 / 0.35);
  filter: blur(30px);
  animation: child-drift 9s ease-in-out infinite alternate;
}
@keyframes child-drift { to { transform: translate(-70px, 40px) scale(1.25); } }
@media (prefers-reduced-motion: reduce) {
  .child-card, .child-orb { animation: none; }
}
</style>
