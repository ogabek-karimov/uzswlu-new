<script setup lang="ts">
import type { Slide } from '#shared/types/api'

// Staff sahifasi pastidagi karusel (oldingi saytdagidek): bosh sahifa bannerlari, markazda katta rasm,
// yonlarda o'tgan va navbatdagi rasm kichikroq va xiraroq chetdan chiqib turadi. Surish, ‹ › tugmalari, bosilsa — bosh sahifa.
const props = withDefaults(defineProps<{ slides: Slide[]; interval?: number }>(), { interval: 6000 })

const { t } = useI18n()
const localePath = useLocalePath()

const count = computed(() => props.slides.length)
const current = ref(0)
const hovered = ref(false)
const dragging = ref(false)
const dragX = ref(0)
const viewport = ref<HTMLElement>()

/** Aylana ro'yxatdagi eng qisqa masofa: -1 — chapdagi (o'tgan), 0 — markaz, 1 — o'ngdagi (navbatdagi) */
function offset(i: number) {
  const n = count.value
  let d = (i - current.value) % n
  if (d > n / 2) d -= n
  if (d < -n / 2) d += n
  return d
}

function go(step: number) {
  if (count.value < 2) return
  current.value = (current.value + step + count.value) % count.value
}

// Avtomatik aylanish: sichqoncha ustida yoki surilayotganda to'xtaydi
let timer: ReturnType<typeof setTimeout> | undefined
let reduced = false
function schedule() {
  clearTimeout(timer)
  if (count.value < 2 || hovered.value || dragging.value || reduced) return
  timer = setTimeout(() => go(1), props.interval)
}
watch([current, hovered, dragging, count], schedule)
onMounted(() => {
  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  schedule()
})
onBeforeUnmount(() => clearTimeout(timer))

// Sichqoncha / barmoq bilan surish
let startX = 0
let width = 1
let moved = false
function onDown(e: PointerEvent) {
  if (count.value < 2 || e.button !== 0) return
  dragging.value = true
  moved = false
  startX = e.clientX
  width = viewport.value?.clientWidth || 1
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}
function onMove(e: PointerEvent) {
  if (!dragging.value) return
  dragX.value = e.clientX - startX
  if (Math.abs(dragX.value) > 6) moved = true
}
function onUp() {
  if (!dragging.value) return
  dragging.value = false
  const threshold = width * 0.15
  if (dragX.value < -threshold) go(1)
  else if (dragX.value > threshold) go(-1)
  dragX.value = 0
}
function onSlideClick(e: MouseEvent, i: number) {
  // Surilgandan keyingi "click" bosish hisoblanmaydi; yondagi rasm bosilsa — o'sha rasmga o'tadi
  if (moved || offset(i) !== 0) {
    e.preventDefault()
    if (!moved) go(offset(i))
  }
}

function slideStyle(i: number) {
  const d = offset(i)
  const far = Math.abs(d) > 1
  return {
    // Yon rasm 0.86 marta kichik; uning ichki cheti markazdagidan 24px narida turadi → chetdan chiqib ko'rinadi
    transform: `translateX(calc(${d} * (93% + 24px) + ${dragX.value}px)) scale(${d === 0 ? 1 : 0.86})`,
    opacity: far ? 0 : d === 0 ? 1 : 0.55,
    filter: d === 0 ? 'none' : 'blur(1.5px) saturate(0.75) brightness(0.92)',
    zIndex: d === 0 ? 3 : 2,
    visibility: (far ? 'hidden' : 'visible') as 'hidden' | 'visible',
  }
}
</script>

<template>
  <section
    v-if="count"
    class="overflow-x-clip"
    :aria-label="t('staff.profile.banners')"
    aria-roledescription="carousel"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div
        ref="viewport"
        tabindex="0"
        class="relative mx-auto aspect-video w-[76%] touch-pan-y outline-offset-4 select-none sm:w-[84%] lg:w-[88%] 2xl:w-full"
        :class="dragging ? 'cursor-grabbing' : 'cursor-grab'"
        @mouseenter="hovered = true"
        @mouseleave="hovered = false"
        @focusin="hovered = true"
        @focusout="hovered = false"
        @keydown.left.prevent="go(-1)"
        @keydown.right.prevent="go(1)"
        @pointerdown="onDown"
        @pointermove="onMove"
        @pointerup="onUp"
        @pointercancel="onUp"
      >
        <NuxtLink
          v-for="(slide, i) in slides"
          :key="slide.id"
          :to="localePath('/')"
          draggable="false"
          :aria-hidden="offset(i) !== 0"
          :tabindex="offset(i) === 0 ? 0 : -1"
          class="group absolute inset-0 block overflow-hidden rounded-[28px] bg-brand-950 shadow-[0_30px_70px_-40px_var(--color-brand-900)]"
          :class="!dragging && 'transition-[transform,opacity,filter] duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)]'"
          :style="slideStyle(i)"
          @click="onSlideClick($event, i)"
        >
          <img
            :src="slide.image"
            :alt="slide.alt"
            draggable="false"
            :loading="Math.abs(offset(i)) <= 1 ? 'eager' : 'lazy'"
            class="size-full object-contain transition-transform duration-500"
            :class="offset(i) === 0 && 'group-hover:scale-[1.03]'"
          >
        </NuxtLink>
      </div>

      <div class="mt-5 flex items-center justify-center gap-4">
        <button
          type="button"
          :aria-label="t('carousel.prev')"
          class="grid size-11 place-items-center rounded-full border border-line bg-white text-ink transition hover:-translate-y-0.5 hover:border-accent-500"
          @click="go(-1)"
        >
          <Icon name="lucide:chevron-left" class="size-5" />
        </button>
        <span class="min-w-14 text-center text-sm font-semibold text-muted tabular-nums" aria-live="polite">
          {{ String(current + 1).padStart(2, '0') }} / {{ String(count).padStart(2, '0') }}
        </span>
        <button
          type="button"
          :aria-label="t('carousel.next')"
          class="grid size-11 place-items-center rounded-full border border-line bg-white text-ink transition hover:-translate-y-0.5 hover:border-accent-500"
          @click="go(1)"
        >
          <Icon name="lucide:chevron-right" class="size-5" />
        </button>
      </div>
    </div>
  </section>
</template>
