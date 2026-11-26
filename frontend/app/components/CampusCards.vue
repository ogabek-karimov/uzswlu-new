<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// Binolar kartalari (Aloqa sahifasi va «O'quv binolari» sahifasi uchun umumiy): Yandex xaritasi, manzil, telefon, yo'nalish.
// Ma'lumot bitta joydan — admin panel → Sozlamalar → «Binolar va xarita»
defineProps<{ campuses: ContactPage['campuses'] }>()

const { t } = useI18n()

// Bino logosi: binoga bog'langan fakultet logosi (admin: Binolar va xarita → Fakultet); bosh binoda — universitet logosi
function logoOf(c: ContactPage['campuses'][number]): string | null {
  return c.logo ?? (c.id === 'main' ? '/logos/uzswlu.png' : null)
}
const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`
</script>

<template>
  <ul v-reveal class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
    <li v-for="c in campuses" :key="c.id" data-reveal-item class="group/campus flex flex-col overflow-hidden rounded-3xl border border-line bg-white shadow-[0_1px_0_rgb(19_17_47/0.04)] transition duration-300 ease-out hover:z-10 hover:-translate-y-1.5 hover:border-brand-300 hover:shadow-[0_30px_60px_-28px_rgb(56_43_133/0.55)] motion-reduce:transition-none motion-reduce:hover:transform-none">
      <!-- Yandex xaritasi (bosh sahifadagi bilan bir xil); xarita bo'lmasa — belgi -->
      <div class="relative h-[250px] overflow-hidden bg-brand-100">
        <MapFrame v-if="c.mapEmbed" :src="c.mapEmbed" :title="`${c.name} — ${t('contact.route')}`" />
        <!-- Bino logosi: hamma kartada bir xil o'lcham va joy (xaritaning yuqori chap burchagi) -->
        <span v-if="logoOf(c)" class="pointer-events-none absolute top-3 left-3 z-10 size-[62px] rounded-full shadow-[0_0_22px_-2px_rgb(0_252_180/0.65)]" aria-hidden="true">
          <!-- Aylanuvchi yorqin nur (mint → indigo) -->
          <span class="absolute inset-0 animate-spin rounded-full bg-[conic-gradient(from_0deg,#00fcb4,#7f70d3,#ffffff,#00fcb4)] [animation-duration:4s] motion-reduce:animate-none" />
          <span class="absolute inset-[3px] grid place-items-center overflow-hidden rounded-full bg-white">
            <img :src="logoOf(c)!" alt="" width="56" height="56" loading="lazy" class="size-full object-cover" :class="c.id === 'main' && 'scale-90 object-contain'">
          </span>
        </span>
        <span v-if="!c.mapEmbed" class="absolute top-1/2 left-1/2 size-10 -translate-x-1/2 -translate-y-1/2 -rotate-45 rounded-[999px_999px_999px_0] bg-brand-800" aria-hidden="true" />
      </div>
      <!-- Xarita osti: nom, belgili ma'lumot qatorlari va «Yo'nalish olish» tugmasi (kartalarda bir qatorda — pastga tekislangan) -->
      <div class="flex flex-1 flex-col p-5">
        <h3 class="text-lg leading-snug font-semibold transition-colors group-hover/campus:text-brand-700">{{ c.name }}</h3>
        <ul class="mt-3.5 flex flex-col gap-2.5 text-[14px] leading-snug">
          <li class="flex gap-2.5 text-muted">
            <span class="grid size-8 shrink-0 place-items-center rounded-[10px] bg-brand-50 text-brand-700" aria-hidden="true"><Icon name="lucide:map-pin" class="size-4" /></span>
            <span class="min-w-0 self-center">{{ c.address }}</span>
          </li>
          <li>
            <a :href="tel(c.phone)" class="group/row flex items-center gap-2.5 font-semibold text-ink transition-colors hover:text-brand-700">
              <span class="grid size-8 shrink-0 place-items-center rounded-[10px] bg-accent-400/15 text-accent-600 transition-colors group-hover/row:bg-accent-400 group-hover/row:text-ink" aria-hidden="true"><Icon name="lucide:phone" class="size-4" /></span>
              <span class="tabular-nums">{{ c.phone }}</span>
            </a>
          </li>
          <li v-if="c.email">
            <a :href="`mailto:${c.email}`" class="group/row flex min-w-0 items-center gap-2.5 font-medium text-ink transition-colors hover:text-brand-700">
              <span class="grid size-8 shrink-0 place-items-center rounded-[10px] bg-brand-50 text-brand-700 transition-colors group-hover/row:bg-brand-800 group-hover/row:text-white" aria-hidden="true"><Icon name="lucide:mail" class="size-4" /></span>
              <span class="min-w-0 break-all">{{ c.email }}</span>
            </a>
          </li>
        </ul>
        <span class="min-h-5 flex-1" aria-hidden="true" />
        <a
          :href="c.mapUrl"
          target="_blank"
          rel="noopener"
          class="group/route relative flex items-center gap-2.5 overflow-hidden rounded-full border border-brand-100 bg-brand-50/70 py-1.5 pr-4 pl-1.5 text-sm font-semibold text-brand-800 transition-colors duration-300 hover:border-transparent hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-400"
        >
          <!-- Kursor kelganda — indigo gradient chapdan to'ladi -->
          <span class="absolute inset-0 origin-left scale-x-0 bg-[linear-gradient(120deg,#382b85,#13112f)] transition-transform duration-500 ease-out group-hover/route:scale-x-100" aria-hidden="true" />
          <span class="relative grid size-8 shrink-0 place-items-center rounded-full bg-white text-brand-700 shadow-[0_4px_12px_-6px_rgb(56_43_133/0.6)] transition-colors group-hover/route:bg-accent-400 group-hover/route:text-ink" aria-hidden="true">
            <Icon name="lucide:navigation" class="size-4" />
          </span>
          <span class="relative flex-1">{{ t('contact.route') }}</span>
          <Icon name="lucide:arrow-up-right" class="relative size-4 transition-transform duration-300 group-hover/route:translate-x-0.5 group-hover/route:-translate-y-0.5 group-hover/route:text-accent-400" aria-hidden="true" />
        </a>
      </div>
    </li>
  </ul>
</template>
