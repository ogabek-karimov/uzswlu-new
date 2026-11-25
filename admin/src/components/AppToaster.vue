<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { onToast, type Toast } from '@/lib/toast'
import Icon from './Icon.vue'

// Yuqorida (markazda) çiqadigan bildiriş: «Saqlandi», «Naşr qilindi», «Öçirildi».
// Ketma-ket saqlaşda (masalan, tartibni süriş) yangisi eskisining örnini egallaydi — ekran töldirilmaydi.
const current = ref<Toast | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined
const off = onToast((t) => {
  current.value = t
  clearTimeout(timer)
  timer = setTimeout(() => { current.value = null }, 2600)
})
onBeforeUnmount(() => { off(); clearTimeout(timer) })
</script>

<template>
  <div class="pointer-events-none fixed inset-x-0 top-4 z-[100] flex justify-center px-4" role="status" aria-live="polite">
    <Transition
      enter-active-class="transition duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]"
      enter-from-class="-translate-y-4 scale-95 opacity-0"
      leave-active-class="transition duration-200 ease-in"
      leave-to-class="-translate-y-2 opacity-0"
      mode="out-in"
    >
      <div
        v-if="current"
        :key="current.id"
        class="pointer-events-auto flex items-center gap-3 rounded-full bg-brand-950/95 py-2 pr-5 pl-2 text-white shadow-[0_18px_40px_-12px_rgb(19_17_47/0.55)] ring-1 ring-white/10 backdrop-blur"
      >
        <span
          class="grid size-8 place-items-center rounded-full"
          :class="current.kind === 'delete' ? 'bg-[#F04438] text-white' : 'bg-mint text-brand-950 shadow-[0_0_18px_-2px_var(--color-mint)]'"
          aria-hidden="true"
        >
          <Icon :name="current.kind === 'delete' ? 'trash' : 'check'" :size="16" />
        </span>
        <span class="text-sm font-semibold">{{ current.text }}</span>
      </div>
    </Transition>
  </div>
</template>
