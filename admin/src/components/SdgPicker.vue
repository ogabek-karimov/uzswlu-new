<script setup lang="ts">
import { SDG_COLORS, SDG_NAMES } from '@/lib/constants'

// BRM: "BRMga kirmaydi" yoki 17 maqsaddan bittasi
const props = defineProps<{ modelValue: number }>()
const emit = defineEmits<{ 'update:modelValue': [number] }>()
const pick = (n: number) => emit('update:modelValue', props.modelValue === n ? 0 : n)
</script>

<template>
  <div>
    <button
      type="button" role="radio" :aria-checked="!modelValue"
      class="mt-3.5 flex h-11 w-full items-center gap-2.5 rounded-xl px-3.5 text-sm font-semibold"
      :class="!modelValue ? 'border-2 border-brand-700 bg-brand-50' : 'border border-field bg-white'"
      @click="emit('update:modelValue', 0)"
    >
      <span class="grid size-[18px] place-items-center rounded-full border-2" :class="!modelValue ? 'border-brand-700' : 'border-[#C9C5D6]'"><span class="size-2 rounded-full" :class="!modelValue && 'bg-brand-700'" /></span>
      BRMga kirmaydi
    </button>
    <div role="radiogroup" aria-label="BRM maqsadi" class="mt-2.5 grid grid-cols-6 gap-1.5">
      <button
        v-for="(color, i) in SDG_COLORS" :key="i" type="button" role="radio" :aria-checked="modelValue === i + 1"
        :aria-label="`BRM ${i + 1} — ${SDG_NAMES[i]}`" :title="`BRM ${i + 1} — ${SDG_NAMES[i]}`"
        class="aspect-square rounded-[10px] text-[15px] font-extrabold text-white transition hover:-translate-y-0.5"
        :style="{ background: color, opacity: modelValue && modelValue !== i + 1 ? 0.35 : 1, boxShadow: modelValue === i + 1 ? '0 0 0 3px #fff, 0 0 0 5px #13112F' : undefined }"
        @click="pick(i + 1)"
      >{{ i + 1 }}</button>
    </div>
    <div class="mt-3 flex items-center gap-3 rounded-2xl bg-[#FAF9FD] px-3.5 py-3">
      <span class="grid size-9 shrink-0 place-items-center rounded-[10px] font-bold text-white" :style="{ background: modelValue ? SDG_COLORS[modelValue - 1] : '#C9C5D6' }">{{ modelValue || '—' }}</span>
      <span class="text-[13px] leading-snug">
        <b class="block text-sm">{{ modelValue ? `BRM ${modelValue} — ${SDG_NAMES[modelValue - 1]}` : 'BRMga kirmaydi' }}</b>
        <span class="text-muted">{{ modelValue ? `Post /brm-${modelValue} sahifasida ham öz-özidan çiqadi.` : 'Post faqat yangiliklar röyxatida çiqadi.' }}</span>
      </span>
    </div>
  </div>
</template>
