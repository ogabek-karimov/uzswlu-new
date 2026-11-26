<script setup lang="ts">
// Maxsus imkoniyatlar: bitta tugma (xalqaro belgi) — shrift, kontrast/rang va ovoz hammasi uning panelida.
// nav — menyu qatorida, faqat belgi, kursor kelganda nomi chiqadi (kompyuter/planshet); bar — yuqori to'q panelda, faqat belgi (telefon; nomi aria-label/title da)
const props = withDefaults(defineProps<{ variant?: 'bar' | 'nav' }>(), { variant: 'bar' })

const { t } = useI18n()
const { open, root } = useDropdown()

const isNav = computed(() => props.variant === 'nav')
</script>

<template>
  <div ref="root" :class="isNav ? 'relative' : ''">
    <button
      v-if="isNav"
      type="button"
      class="group/a11y relative grid size-11 place-items-center rounded-full bg-brand-800 text-white transition-colors hover:bg-brand-700"
      aria-haspopup="dialog"
      :aria-expanded="open"
      :aria-label="t('a11y.title')"
      @click="open = !open"
    >
      <A11yIcon class="size-6" />
      <!-- Kursor kelganda (yoki klaviatura bilan tanlanganda) nomi chiqadi -->
      <span
        v-if="!open"
        class="pointer-events-none absolute top-full right-0 z-10 mt-2 translate-y-1 rounded-lg bg-ink px-2.5 py-1 text-xs font-semibold whitespace-nowrap text-white opacity-0 shadow-lg transition duration-200 group-hover/a11y:translate-y-0 group-hover/a11y:opacity-100 group-focus-visible/a11y:translate-y-0 group-focus-visible/a11y:opacity-100"
        aria-hidden="true"
      >{{ t('a11y.title') }}</span>
    </button>
    <button
      v-else
      type="button"
      class="grid size-7 place-items-center rounded-full bg-white/12 text-white transition-colors hover:bg-white/20"
      aria-haspopup="dialog"
      :aria-expanded="open"
      :aria-label="t('a11y.title')"
      :title="t('a11y.title')"
      @click="open = !open"
    >
      <A11yIcon class="size-[18px]" />
    </button>

    <A11yPanel v-if="open && isNav" class="absolute top-full right-0 z-[60] mt-2" @close="open = false" />
    <A11yPanel v-else-if="open" class="fixed inset-x-3 top-12 z-[60] mx-auto max-h-[calc(100dvh-4rem)]!" @close="open = false" />
  </div>
</template>
