<script setup lang="ts">
import type { PageCta } from '#shared/types/api'

// Matndan keyingi chaqiruv bloki (admin → Sahifalar → «Chaqiruv bloki»), masalan «Axborot-resurs markazi» → uzlib.uz.
// Animatsiyalar: aylanuvçi gradient çegara, suzuvçi nurlar va ikonkalar, tugmada yaltiroq çiziq + puls; ekranga kelganda pastdan çiqadi.
// prefers-reduced-motion — hammasi öçadi.
const props = defineProps<{ cta: PageCta }>()

const { t } = useI18n()
const localePath = useLocalePath()
const NuxtLink = resolveComponent('NuxtLink')
const external = computed(() => /^https?:\/\//.test(props.cta.url))
const host = computed(() => {
  try { return external.value ? new URL(props.cta.url).host.replace(/^www\./, '') : '' }
  catch { return '' }
})

const root = ref<HTMLElement>()
// Sukut böyiça körinadi (SSR, JS yöq); kuzatuvçi ulangandagina yaşirilib, ekranga kelganda çiqadi
const armed = ref(false)
const shown = ref(false)
let io: IntersectionObserver | undefined
onMounted(() => {
  if (!root.value || !('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return
  io = new IntersectionObserver(([e]) => {
    if (e?.isIntersecting) { shown.value = true; io?.disconnect() }
  }, { threshold: 0.2 })
  io.observe(root.value)
  armed.value = true
})
onBeforeUnmount(() => io?.disconnect())
</script>

<template>
  <aside ref="root" class="cta-wrap mt-12" :class="[armed && 'is-armed', shown && 'is-in']">
    <div class="cta-card relative isolate overflow-hidden rounded-[28px] bg-brand-950 px-6 py-9 text-white sm:px-10 sm:py-11">
      <!-- suzuvçi nurlar -->
      <span aria-hidden="true" class="cta-glow cta-glow-a" />
      <span aria-hidden="true" class="cta-glow cta-glow-b" />
      <span aria-hidden="true" class="cta-grid" />
      <!-- suzuvçi ikonkalar -->
      <Icon aria-hidden="true" name="lucide:book-open" class="cta-float right-[8%] top-[14%] text-4xl text-accent-400/80" style="--d: 0s" />
      <Icon aria-hidden="true" name="lucide:sparkles" class="cta-float right-[24%] bottom-[16%] text-2xl text-accent-300/70" style="--d: -2.2s" />
      <Icon aria-hidden="true" name="lucide:library-big" class="cta-float right-[3%] bottom-[22%] hidden text-5xl text-white/15 sm:block" style="--d: -4.1s" />

      <div class="relative max-w-[560px]">
        <p v-if="host" class="cta-step inline-flex items-center gap-2 rounded-full border border-accent-400/40 bg-accent-400/10 px-3 py-1 text-xs font-bold tracking-wide text-accent-300" style="--i: 0">
          <span class="cta-dot" aria-hidden="true" />{{ host }}
        </p>
        <h2 v-if="cta.title" class="cta-step mt-4 font-display text-[28px] leading-tight font-semibold sm:text-[34px]" style="--i: 1">{{ cta.title }}</h2>
        <p v-if="cta.text" class="cta-step mt-3 text-[15px] leading-relaxed text-white/80 sm:text-base" style="--i: 2">{{ cta.text }}</p>

        <component
          :is="external ? 'a' : NuxtLink"
          v-bind="external ? { href: cta.url, target: '_blank', rel: 'noopener' } : { to: localePath(cta.url) }"
          class="cta-step cta-btn group relative mt-7 inline-flex items-center gap-3 overflow-hidden rounded-full bg-accent-400 py-3.5 pr-3.5 pl-6 text-[15px] font-bold text-brand-950 transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_18px_40px_-12px_rgb(0_252_180/0.65)] focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-accent-300"
          style="--i: 3"
        >
          <span aria-hidden="true" class="cta-shine" />
          <span class="relative">{{ cta.label }}</span>
          <span class="relative grid size-9 place-items-center rounded-full bg-brand-950 text-accent-400 transition-transform duration-300 group-hover:translate-x-1 group-hover:-rotate-45">
            <Icon :name="external ? 'lucide:arrow-up-right' : 'lucide:arrow-right'" class="size-[18px] rotate-45 transition-transform duration-300 group-hover:rotate-45" />
          </span>
          <span v-if="external" class="sr-only">({{ t('page.ctaNewTab') }})</span>
        </component>
      </div>
    </div>
  </aside>
</template>

<style scoped>
@property --cta-angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}

/* Aylanuvçi gradient çegara */
.cta-wrap {
  position: relative;
  padding: 2px;
  border-radius: 30px;
  background: conic-gradient(from var(--cta-angle), var(--color-accent-400), #7c6cf2, var(--color-brand-500, #4b3fd1), #ff8fd8, var(--color-accent-400));
  animation: cta-spin 7s linear infinite;
  transition: opacity 0.7s ease, transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
}
/* Faqat kuzatuvçi ulanganda yaşiriladi — JS işlamasa ham blok körinadi */
.cta-wrap.is-armed:not(.is-in) { opacity: 0; transform: translateY(28px) scale(0.985); }
@keyframes cta-spin { to { --cta-angle: 360deg; } }

/* Matn qatorlari ketma-ket çiqadi */
.cta-step {
  transition: opacity 0.6s ease, transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
  transition-delay: calc(0.15s + var(--i) * 0.12s);
}
.is-armed:not(.is-in) .cta-step { opacity: 0; transform: translateY(14px); }
.is-in .cta-btn { transition: opacity 0.6s ease calc(0.15s + var(--i) * 0.12s), transform 0.3s ease, box-shadow 0.3s ease; }

/* Suzuvçi nurlar */
.cta-glow {
  position: absolute;
  z-index: -1;
  border-radius: 9999px;
  filter: blur(60px);
  pointer-events: none;
}
.cta-glow-a { width: 340px; height: 340px; right: -80px; top: -120px; background: rgb(0 252 180 / 0.35); animation: cta-drift 11s ease-in-out infinite alternate; }
.cta-glow-b { width: 300px; height: 300px; left: -100px; bottom: -140px; background: rgb(124 108 242 / 0.55); animation: cta-drift 13s ease-in-out infinite alternate-reverse; }
@keyframes cta-drift {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(-60px, 40px) scale(1.2); }
}
.cta-grid {
  position: absolute;
  inset: 0;
  z-index: -1;
  background-image: radial-gradient(rgb(255 255 255 / 0.09) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: linear-gradient(110deg, transparent 30%, #000 75%);
}

/* Suzuvçi ikonkalar */
.cta-float {
  position: absolute;
  animation: cta-bob 6s ease-in-out infinite;
  animation-delay: var(--d);
}
@keyframes cta-bob {
  0%, 100% { transform: translateY(0) rotate(-6deg); }
  50% { transform: translateY(-14px) rotate(6deg); }
}

/* Jonli nuqta */
.cta-dot {
  width: 7px;
  height: 7px;
  border-radius: 9999px;
  background: var(--color-accent-400);
  box-shadow: 0 0 0 0 rgb(0 252 180 / 0.7);
  animation: cta-ping 1.8s ease-out infinite;
}
@keyframes cta-ping { to { box-shadow: 0 0 0 9px rgb(0 252 180 / 0); } }

/* Tugma: yaltiroq çiziq + puls halqasi */
.cta-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 35%, rgb(255 255 255 / 0.75) 50%, transparent 65%);
  transform: translateX(-120%);
  animation: cta-shine 3.2s ease-in-out infinite 1.2s;
}
@keyframes cta-shine {
  0%, 55% { transform: translateX(-120%); }
  100% { transform: translateX(120%); }
}
.cta-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: 0 0 0 0 rgb(0 252 180 / 0.55);
  animation: cta-pulse 2.4s ease-out infinite 1.6s;
  pointer-events: none;
}
@keyframes cta-pulse { 0% { box-shadow: 0 0 0 0 rgb(0 252 180 / 0.55); } 100% { box-shadow: 0 0 0 18px rgb(0 252 180 / 0); } }

@media (prefers-reduced-motion: reduce) {
  .cta-wrap, .cta-glow, .cta-float, .cta-dot, .cta-shine, .cta-btn::after { animation: none; }
  .cta-wrap, .cta-step { transition: none; }
}
@media print {
  .cta-wrap { display: none; }
}
</style>
