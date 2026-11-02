<script setup lang="ts">
// Brauzerning o'z <dialog> elementi: fokus ichida qoladi, Escape va fon bosilsa yopiladi.
// sheet: telefonda pastdan chiqadigan oyna. beforeClose: false qaytarsa yopilmaydi (masalan, saqlanmagan fayl bor)
const open = defineModel<boolean>('open', { required: true })
const props = withDefaults(defineProps<{ title: string; sheet?: boolean; hideTitle?: boolean; bodyClass?: string; beforeClose?: () => boolean }>(), {
  bodyClass: 'p-5 sm:p-6',
  beforeClose: undefined,
})

const dialog = ref<HTMLDialogElement>()
const titleId = useId()

watch(open, (value) => {
  const el = dialog.value
  if (!el) return
  if (value && !el.open) el.showModal()
  if (!value && el.open) el.close()
}, { flush: 'post' })

function requestClose() {
  if (props.beforeClose && !props.beforeClose()) return
  open.value = false
}

// Ichki blok butun oynani to'ldiradi, shuning uchun dialogning o'zi faqat fon (::backdrop) bosilganda nishon bo'ladi
function onClick(event: MouseEvent) {
  if (event.target === dialog.value) requestClose()
}

defineExpose({ requestClose })
</script>

<template>
  <dialog
    ref="dialog"
    :aria-labelledby="titleId"
    class="m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] overflow-y-auto rounded-[28px] bg-white p-0 text-ink shadow-[0_40px_80px_-30px_rgba(17,12,46,0.6)] open:animate-dialog-in backdrop:bg-brand-950/55 backdrop:backdrop-blur-sm"
    :class="props.sheet && 'max-sm:mb-0 max-sm:w-full max-sm:max-w-none max-sm:rounded-b-none'"
    @cancel.prevent="requestClose"
    @close="open = false"
    @click="onClick"
  >
    <div :class="bodyClass">
      <h2 v-if="!hideTitle" :id="titleId" class="text-center text-lg font-bold">{{ title }}</h2>
      <h2 v-else :id="titleId" class="sr-only">{{ title }}</h2>
      <slot :close="requestClose" />
    </div>
  </dialog>
</template>
