<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { collapseBus } from '@/lib/collapse'
import Icon from './Icon.vue'

// Yig'iladigan blok (sahifa tahrirlash formasidagi bo'limlar): sarlavha bosilsa yig'iladi/yoyiladi, holat brauzerda eslab qolinadi
// (`id` bo'yicha). `variant="card"` — alohida karta, `inner` — karta ichidagi ichki blok. «Hammasini yig'ish/yoyish» — lib/collapse.ts.
const props = withDefaults(defineProps<{
  id: string
  title: string
  hint?: string
  count?: number
  defaultOpen?: boolean
  variant?: 'card' | 'inner'
  bodyClass?: string
}>(), { defaultOpen: true, variant: 'card', bodyClass: 'flex flex-col gap-3' })

const KEY = `collapse:${props.id}`
const open = ref(props.defaultOpen)
// Foydalanuvchi o'zi yig'magan/yoymagan bo'lsa — sukut holati ma'lumotga ergashadi (masalan, sahifa yuklangach raqamlar bor bo'lsa — ochiq)
let chosen = false
onMounted(() => {
  try {
    const v = localStorage.getItem(KEY)
    if (v !== null) { open.value = v === '1'; chosen = true }
  }
  catch { /* saqlash yopiq — sukut holati */ }
})
watch(() => props.defaultOpen, (v) => { if (!chosen) open.value = v })
function toggle(v = !open.value) {
  open.value = v
  chosen = true
  try { localStorage.setItem(KEY, v ? '1' : '0') } catch { /* jim */ }
}
watch(() => collapseBus.tick, () => toggle(collapseBus.open))
const bodyId = `cb-${props.id}`
</script>

<template>
  <section :class="variant === 'card' ? 'card px-[22px] py-5' : 'rounded-2xl border border-line bg-[#FAF9FD] px-4 py-3.5'">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <button type="button" class="group flex min-w-0 flex-1 items-center gap-2.5 text-left" :aria-expanded="open" :aria-controls="bodyId" @click="toggle()">
        <span class="grid size-7 shrink-0 place-items-center rounded-lg border border-line bg-white text-muted transition group-hover:border-brand-700 group-hover:text-brand-700">
          <Icon name="chevronDown" :size="15" class="transition-transform duration-200" :class="!open && '-rotate-90'" />
        </span>
        <span class="min-w-0">
          <span class="flex flex-wrap items-center gap-2" :class="variant === 'card' ? 'text-base font-bold' : 'text-sm font-bold'">
            {{ title }}
            <span v-if="count" class="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700">{{ count }}</span>
          </span>
          <span v-if="hint" class="mt-0.5 block text-xs font-normal text-muted">{{ hint }}</span>
        </span>
      </button>
      <div v-if="$slots.actions && open" class="flex flex-wrap gap-1.5"><slot name="actions" /></div>
    </div>
    <div v-show="open" :id="bodyId" class="mt-3.5" :class="bodyClass"><slot /></div>
  </section>
</template>
