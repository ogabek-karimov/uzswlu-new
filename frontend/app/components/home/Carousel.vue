<script setup lang="ts">
import type { Slide } from '#shared/types/api'

const props = withDefaults(defineProps<{ slides: Slide[]; interval?: number }>(), { interval: 6000 })

const { t } = useI18n()
const NuxtLink = resolveComponent('NuxtLink')

const DURATION = 700

const progress = ref(0)
const playing = ref(true)
const hovered = ref(false)

const count = computed(() => props.slides.length)
const running = computed(() => playing.value && !hovered.value && !dragging.value && count.value > 1)

// Uzluksiz aylanish: tasma = [oxirgining nusxasi, ...slaydlar, birinchining nusxasi].
// Oxirgidan keyin birinchining nusxasiga oddiy "keyingi" kabi o'tiladi, so'ng
// animatsiyasiz haqiqiy birinchi slaydga almashtiriladi — nusxa bir xil bo'lgani uchun ko'rinmaydi.
const looped = computed(() => count.value > 1)
const trackSlides = computed(() => {
  const real = props.slides.map((slide, i) => ({ slide, key: slide.id, real: i as number | null }))
  if (!looped.value) return real
  const first = props.slides[0]!
  const last = props.slides[count.value - 1]!
  return [{ slide: last, key: `clone-start-${last.id}`, real: null }, ...real, { slide: first, key: `clone-end-${first.id}`, real: null }]
})

/** Tasmadagi joriy o'rin (nusxalar bilan birga) */
const pos = ref(1)
const animate = ref(true)
const track = ref<HTMLElement>()
const shift = computed(() => (looped.value ? pos.value : 0))
/** Foydalanuvchiga ko'rinadigan slayd raqami (0 dan) */
const index = computed(() => (looped.value ? (((pos.value - 1) % count.value) + count.value) % count.value : 0))

const onClone = () => looped.value && (pos.value === 0 || pos.value === count.value + 1)

async function snap() {
  if (!onClone()) return
  animate.value = false
  pos.value = pos.value === 0 ? count.value : 1
  await nextTick()
  void track.value?.offsetWidth // sakrash animatsiyasiz qo'llanishi uchun
  animate.value = true
}

let settleTimer: ReturnType<typeof setTimeout> | undefined
async function moveBy(step: number) {
  if (!looped.value) return
  if (onClone()) await snap()
  animate.value = true
  pos.value += step
  progress.value = 0
  clearTimeout(settleTimer)
  // transitionend yashirin tabda kelmasligi mumkin — zaxira taymer
  settleTimer = setTimeout(snap, DURATION + 50)
}

const next = () => moveBy(1)
const prev = () => moveBy(-1)
const go = (i: number) => moveBy(i - index.value)

function onTransitionEnd(e: TransitionEvent) {
  if (e.target === track.value) snap()
}

onBeforeUnmount(() => clearTimeout(settleTimer))

// Avtomatik aylanish: jarayon chizig'i bilan bir xil soatdan yuradi, shuning uchun pauza ikkalasini birga to'xtatadi
let raf = 0
let last = 0
function tick(now: number) {
  if (last && running.value) {
    // Fon tabidan qaytganda katta sakrash bo'lmasligi uchun cheklangan
    progress.value += Math.min(now - last, 100) / props.interval
    if (progress.value >= 1) next()
  }
  last = now
  raf = requestAnimationFrame(tick)
}

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) playing.value = false
  raf = requestAnimationFrame(tick)
})
onBeforeUnmount(() => cancelAnimationFrame(raf))

// Barmoq / sichqoncha bilan surish
const dragging = ref(false)
const dragX = ref(0)
let startX = 0
let suppressClick = false

function onPointerDown(e: PointerEvent) {
  if (count.value < 2 || (e.pointerType === 'mouse' && e.button !== 0)) return
  snap()
  dragging.value = true
  suppressClick = false
  startX = e.clientX
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!dragging.value) return
  dragX.value = e.clientX - startX
  if (Math.abs(dragX.value) > 6) suppressClick = true
}

function onPointerUp(e: PointerEvent) {
  if (!dragging.value) return
  dragging.value = false
  const width = (e.currentTarget as HTMLElement).clientWidth
  if (Math.abs(dragX.value) > Math.min(80, width * 0.15)) dragX.value < 0 ? next() : prev()
  dragX.value = 0
}

function onClickCapture(e: MouseEvent) {
  if (suppressClick) {
    e.preventDefault()
    e.stopPropagation()
    suppressClick = false
  }
}
</script>

<template>
  <section
    v-if="count"
    class="mx-auto max-w-7xl px-4 pt-4 sm:px-6 sm:pt-6 lg:px-8"
    :aria-label="t('carousel.label')"
    aria-roledescription="carousel"
    @keydown.left.prevent="prev"
    @keydown.right.prevent="next"
  >
    <div
      class="group/carousel relative aspect-[16/9] w-full overflow-hidden rounded-2xl bg-brand-950 shadow-[0_30px_70px_-40px_var(--color-brand-900)] sm:rounded-[2rem]"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
      @focusin="hovered = true"
      @focusout="hovered = false"
    >
      <div
        ref="track"
        class="absolute inset-0 flex touch-pan-y select-none"
        :class="animate && !dragging && 'transition-transform duration-700 ease-[cubic-bezier(0.22,0.61,0.36,1)]'"
        :style="{ transform: `translateX(calc(${-shift * 100}% + ${dragX}px))` }"
        @transitionend="onTransitionEnd"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
        @click.capture="onClickCapture"
      >
        <!-- Ikki chetdagi nusxalar (real === null) faqat uzluksiz aylanish uchun, ekran o'quvchilardan yashirin -->
        <div
          v-for="item in trackSlides"
          :key="item.key"
          class="relative h-full w-full shrink-0 overflow-hidden"
          :role="item.real !== null ? 'group' : undefined"
          :aria-roledescription="item.real !== null ? 'slide' : undefined"
          :aria-label="item.real !== null ? `${item.real + 1} / ${count}` : undefined"
          :aria-hidden="item.real !== index"
          :inert="item.real !== index || undefined"
        >
          <!-- Zaxira fon: banner 16:9 bo'lmasa (admin noto'g'ri rasm yuklasa) chetlarni to'ldiradi. 16:9 bannerda ko'rinmaydi -->
          <img
            :src="item.slide.image"
            alt=""
            draggable="false"
            :loading="item.real === null || item.real <= index + 1 ? 'eager' : 'lazy'"
            class="decor absolute inset-0 size-full scale-110 object-cover opacity-60 blur-2xl"
          >
          <component
            :is="item.slide.link ? NuxtLink : 'div'"
            v-bind="item.slide.link ? { to: item.slide.link } : {}"
            class="relative block size-full"
          >
            <!-- Asosiy rasm: hech qachon qirqilmaydi -->
            <img
              :src="item.slide.image"
              :alt="item.real !== null ? item.slide.alt : ''"
              width="1920"
              height="1080"
              draggable="false"
              :loading="item.real === null || item.real <= index + 1 ? 'eager' : 'lazy'"
              :fetchpriority="item.real === 0 ? 'high' : undefined"
              class="size-full object-contain"
            >
          </component>
        </div>
      </div>

      <template v-if="count > 1">
        <!-- Strelkalar (telefonda surish yetarli) -->
        <button
          type="button"
          class="absolute top-1/2 left-4 hidden size-12 -translate-y-1/2 place-items-center rounded-full bg-white/85 text-ink shadow-lg backdrop-blur transition duration-300 group-hover/carousel:opacity-100 hover:bg-white focus-visible:opacity-100 sm:grid sm:opacity-0"
          :aria-label="t('carousel.prev')"
          @click="prev"
        >
          <Icon name="lucide:chevron-left" class="size-6" />
        </button>
        <button
          type="button"
          class="absolute top-1/2 right-4 hidden size-12 -translate-y-1/2 place-items-center rounded-full bg-white/85 text-ink shadow-lg backdrop-blur transition duration-300 group-hover/carousel:opacity-100 hover:bg-white focus-visible:opacity-100 sm:grid sm:opacity-0"
          :aria-label="t('carousel.next')"
          @click="next"
        >
          <Icon name="lucide:chevron-right" class="size-6" />
        </button>

        <!-- Pastki boshqaruv paneli -->
        <div class="pointer-events-none absolute inset-x-0 bottom-0 flex items-center justify-center gap-3 bg-gradient-to-t from-black/45 to-transparent px-4 pt-10 pb-3 sm:justify-between sm:px-6 sm:pb-5">
          <span class="hidden min-w-16 text-sm font-semibold text-white tabular-nums sm:block" aria-hidden="true">
            {{ String(index + 1).padStart(2, '0') }} <span class="text-white/50">/ {{ String(count).padStart(2, '0') }}</span>
          </span>

          <div class="pointer-events-auto flex items-center gap-1.5">
            <button
              v-for="(slide, i) in slides"
              :key="slide.id"
              type="button"
              class="relative grid h-6 place-items-center"
              :aria-label="t('carousel.goTo', { n: i + 1 })"
              :aria-current="i === index ? 'true' : undefined"
              @click="go(i)"
            >
              <span
                class="block h-1.5 overflow-hidden rounded-full transition-all duration-300"
                :class="i === index ? 'w-10 bg-white/35' : 'w-1.5 bg-white/60 hover:bg-white'"
              >
                <span v-if="i === index" class="block h-full rounded-full bg-accent-400" :style="{ width: `${progress * 100}%` }" />
              </span>
            </button>
          </div>

          <div class="flex min-w-16 justify-end">
            <button
              type="button"
              class="pointer-events-auto grid size-7 place-items-center rounded-full bg-black/30 text-white backdrop-blur transition-colors hover:bg-black/50 sm:size-9"
              :aria-label="playing ? t('carousel.pause') : t('carousel.play')"
              @click="playing = !playing"
            >
              <Icon :name="playing ? 'lucide:pause' : 'lucide:play'" class="size-3.5 sm:size-4" />
            </button>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
