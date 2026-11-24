<script setup lang="ts">
import { computed } from 'vue'
import Icon from './Icon.vue'

// Ro'yxat ostidagi «yana ko'rsatish»: har bosilganda `step` tadan qo'shiladi. Yonidagi «yig'ish» faqat oxirgi qo'shilganini olib tashlaydi;
// hammasi ochilgan (oxirgi qadam) bo'lsagina «hammasini yig'ish» — boshlang'ich `step` taga qaytaradi. Yangi uzunlikni `less` bilan beradi.
// Ingichka chiziq — nechtasi ko'rinayotgani (masalan, 10 / 17)
const props = withDefaults(defineProps<{ shown: number; total: number; step?: number; busy?: boolean }>(), { step: 5, busy: false })
const emit = defineEmits<{ more: []; less: [count: number] }>()
const rest = computed(() => Math.max(0, props.total - props.shown))
const next = computed(() => Math.min(props.step, rest.value))
const shownNow = computed(() => Math.min(props.shown, props.total))
function less() {
  if (!rest.value) return emit('less', props.step) // oxirgi qadam — hammasini yig'ish
  const s = shownNow.value
  emit('less', Math.max(props.step, s % props.step ? s - (s % props.step) : s - props.step)) // faqat oxirgi qo'shilgan qism
}
</script>

<template>
  <div v-if="total > step" class="flex flex-col items-center gap-2 border-t border-line px-[22px] pt-3 pb-4">
    <div class="flex w-full items-center gap-3 text-xs text-muted">
      <div class="h-1 flex-1 overflow-hidden rounded-full bg-[#ECEAF3]"><div class="h-full rounded-full bg-brand-700 transition-all duration-300" :style="{ width: `${Math.min(100, shown / total * 100)}%` }" /></div>
      <span class="tabular-nums">{{ Math.min(shown, total) }} / {{ total }}</span>
    </div>
    <div class="flex flex-wrap items-center justify-center gap-2">
    <button
      v-if="shown > step" type="button"
      class="group inline-flex h-9 items-center gap-2 rounded-full border border-line bg-white pr-2 pl-4 text-[13px] font-semibold text-muted transition-colors hover:border-brand-700 hover:text-brand-700"
      @click="less"
    >
      {{ rest ? 'Yig‘iş' : 'Hammasini yig‘iş' }}
      <span class="grid size-6 rotate-180 place-items-center rounded-full bg-[#F1F0F5] transition-transform group-hover:-translate-y-0.5"><Icon name="chevronDown" :size="14" /></span>
    </button>
    <button
      v-if="rest" type="button" :disabled="busy"
      class="group inline-flex h-9 items-center gap-2 rounded-full border border-line bg-white pr-2 pl-4 text-[13px] font-semibold text-ink transition-colors hover:border-brand-700 hover:text-brand-700 disabled:opacity-60"
      :aria-label="`Yana ${next} tasini körsatiş`" @click="$emit('more')"
    >
      {{ busy ? 'Yuklanmoqda…' : `Yana ${next} ta` }}
      <span class="grid size-6 place-items-center rounded-full bg-brand-50 text-brand-700 transition-transform group-hover:translate-y-0.5"><Icon name="chevronDown" :size="14" /></span>
    </button>
    </div>
  </div>
</template>
