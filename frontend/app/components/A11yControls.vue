<script setup lang="ts">
// Maxsus imkoniyatlar: bitta "Ko'rinish" tugmasi — shrift, kontrast/rang va ovoz hammasi uning panelida.
// nav — menyu qatorida, katta va yaqqol (kompyuter/planshet); bar — yuqori to'q panelda, ixcham (telefon)
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
      class="flex h-11 items-center gap-2 rounded-full border-2 border-brand-800 bg-brand-800 pr-4 pl-3 text-sm font-bold text-white transition-colors hover:bg-brand-700"
      aria-haspopup="dialog"
      :aria-expanded="open"
      @click="open = !open"
    >
      <Icon name="lucide:eye" class="size-5" />
      {{ t('a11y.title') }}
    </button>
    <button
      v-else
      type="button"
      class="flex h-7 items-center gap-1.5 rounded-full bg-white/12 px-2.5 text-xs font-bold text-white transition-colors hover:bg-white/20"
      aria-haspopup="dialog"
      :aria-expanded="open"
      @click="open = !open"
    >
      <Icon name="lucide:eye" class="size-4" />
      {{ t('a11y.title') }}
    </button>

    <A11yPanel v-if="open && isNav" class="absolute top-full right-0 z-[60] mt-2" @close="open = false" />
    <A11yPanel v-else-if="open" class="fixed inset-x-3 top-12 z-[60] mx-auto max-h-[calc(100dvh-4rem)]!" @close="open = false" />
  </div>
</template>
