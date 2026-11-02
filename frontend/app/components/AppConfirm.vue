<script setup lang="ts">
// Saytning o'zidagi kichik tasdiqlash oynasi (brauzerning confirm() oynasi o'rniga — oldingi saytdagidek)
const open = defineModel<boolean>('open', { required: true })
defineProps<{ title: string; text?: string; confirmLabel: string; cancelLabel: string; danger?: boolean }>()
const emit = defineEmits<{ confirm: [] }>()
</script>

<template>
  <AppDialog v-model:open="open" :title="title" hide-title class="max-w-[400px]" body-class="p-6 text-center">
    <span class="mx-auto grid size-13 place-items-center rounded-2xl" :class="danger ? 'bg-[#fdecec] text-[#c62828]' : 'bg-[#fff6db] text-[#a66b00]'">
      <Icon name="lucide:triangle-alert" class="size-6" />
    </span>
    <p class="mt-3.5 text-[17px] font-bold">{{ title }}</p>
    <p v-if="text" class="mt-1.5 text-muted">{{ text }}</p>
    <div class="mt-5 grid grid-cols-2 gap-2.5">
      <button
        type="button"
        class="h-12 rounded-[14px] font-bold text-white transition-colors"
        :class="danger ? 'bg-[#c62828] hover:bg-[#a51f1f]' : 'bg-brand-900 hover:bg-brand-800'"
        @click="emit('confirm'); open = false"
      >
        {{ confirmLabel }}
      </button>
      <button type="button" class="h-12 rounded-[14px] border border-line bg-white font-semibold text-ink transition-colors hover:border-accent-500" @click="open = false">
        {{ cancelLabel }}
      </button>
    </div>
  </AppDialog>
</template>
