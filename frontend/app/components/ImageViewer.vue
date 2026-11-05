<script setup lang="ts">
// Suratni to'liq ekranda ko'rish (canvas: "Komponent — Suratni töliq ekranda körish").
// Brauzerning <dialog> elementi: fokus ichida qoladi, Escape yopadi. ‹ ›, klaviatura strelkalari va telefonda surish bilan almashadi
const props = defineProps<{ images: string[]; caption?: string }>()
const index = defineModel<number | null>('index', { required: true })

const { t } = useI18n()
const dialog = ref<HTMLDialogElement>()
const current = computed(() => (index.value === null ? null : props.images[index.value] ?? null))
const many = computed(() => props.images.length > 1)

const lockScroll = (on: boolean) => (document.documentElement.style.overflow = on ? 'hidden' : '')

watch(index, (value) => {
  const el = dialog.value
  if (!el) return
  if (value !== null && !el.open) {
    el.showModal()
    lockScroll(true)
  }
  if (value === null && el.open) el.close()
}, { flush: 'post' })

function onClose() {
  index.value = null
  lockScroll(false)
}

function step(delta: number) {
  if (index.value === null || !many.value) return
  index.value = (index.value + delta + props.images.length) % props.images.length
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowLeft') step(-1)
  if (event.key === 'ArrowRight') step(1)
}

// Suratdan va tugmalardan tashqari bo'sh joy bosilsa yopiladi
function onClick(event: MouseEvent) {
  if (!(event.target as HTMLElement).closest('img, button')) dialog.value?.close()
}

let touchX: number | null = null
function onTouchEnd(event: TouchEvent) {
  const dx = touchX === null ? 0 : (event.changedTouches[0]?.clientX ?? touchX) - touchX
  touchX = null
  if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1)
}

onBeforeUnmount(() => lockScroll(false))
</script>

<template>
  <dialog
    ref="dialog"
    :aria-label="t('posts.viewer')"
    class="no-print m-0 h-dvh max-h-none w-screen max-w-none overflow-hidden bg-transparent p-0 text-white open:animate-dialog-in backdrop:bg-brand-950/95"
    @close="onClose"
    @keydown="onKeydown"
    @click="onClick"
    @touchstart.passive="touchX = $event.touches[0]?.clientX ?? null"
    @touchend="onTouchEnd"
  >
    <div class="grid h-full grid-rows-[auto_minmax(0,1fr)_auto]">
      <div class="flex h-16 items-center justify-between pr-3 pl-5 sm:h-20 sm:pr-6 sm:pl-8">
        <span class="text-sm font-semibold text-white/75 tabular-nums">
          <template v-if="many && index !== null">{{ index + 1 }} / {{ images.length }}</template>
        </span>
        <button type="button" :aria-label="t('posts.closeViewer')" class="grid size-12 place-items-center rounded-full border border-white/20 bg-white/10 transition-colors hover:bg-white/20" @click="dialog?.close()">
          <Icon name="lucide:x" class="size-5" />
        </button>
      </div>

      <div class="relative min-h-0 px-3 sm:px-28">
        <!-- Surat o'z nisbatida, maydonga sig'adigan eng katta o'lchamda (markazda) -->
        <div class="relative size-full">
          <img v-if="current" :key="current" :src="current" :alt="caption ?? ''" class="absolute inset-0 m-auto max-h-full max-w-full rounded-xl shadow-[0_40px_80px_-30px_rgba(0,0,0,0.7)]">
        </div>
        <template v-if="many">
          <button type="button" :aria-label="t('posts.prevImage')" class="absolute top-1/2 left-3 grid size-12 -translate-y-1/2 place-items-center rounded-full border border-white/20 bg-white/10 transition-colors hover:bg-white/20 max-sm:bg-brand-950/50 sm:left-8 sm:size-14" @click="step(-1)">
            <Icon name="lucide:chevron-left" class="size-6" />
          </button>
          <button type="button" :aria-label="t('posts.nextImage')" class="absolute top-1/2 right-3 grid size-12 -translate-y-1/2 place-items-center rounded-full border border-white/20 bg-white/10 transition-colors hover:bg-white/20 max-sm:bg-brand-950/50 sm:right-8 sm:size-14" @click="step(1)">
            <Icon name="lucide:chevron-right" class="size-6" />
          </button>
        </template>
      </div>

      <p class="line-clamp-2 min-h-16 px-6 py-4 text-center text-sm text-white/70 sm:min-h-[72px] sm:py-6">{{ caption }}</p>
    </div>
  </dialog>
</template>
