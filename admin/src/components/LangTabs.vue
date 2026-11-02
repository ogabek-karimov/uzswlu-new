<script setup lang="ts">
import { LANGS, type Lang } from '@/lib/constants'

// Til tablari: har birida to'ldirilganlik belgisi (✓ to'liq, ! qisman, ○ bo'sh)
defineProps<{ modelValue: Lang; fill?: Partial<Record<Lang, 0 | 0.5 | 1>>; compact?: boolean }>()
defineEmits<{ 'update:modelValue': [Lang] }>()

const MARK = { 1: ['✓', 'bg-[#DDFBF0] text-[#0B5A43]', 'töldirilgan'], 0.5: ['!', 'bg-[#FEF3DC] text-[#8A5A00]', 'qisman'], 0: ['○', 'bg-[#F1F0F5] text-subtle', 'böş'] } as const
</script>

<template>
  <div role="tablist" aria-label="Til" class="flex flex-wrap gap-1">
    <button
      v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="modelValue === l.code"
      :class="compact
        ? ['h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold', modelValue === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted']
        : ['-mb-px flex h-[46px] items-center gap-2 rounded-t-xl px-4 text-sm font-semibold', modelValue === l.code ? 'bg-white text-ink shadow-[inset_0_3px_0_var(--color-brand-700),1px_0_0_var(--color-line),-1px_0_0_var(--color-line)]' : 'text-muted']"
      @click="$emit('update:modelValue', l.code)"
    >
      {{ compact ? l.short : l.label }}
      <span
        v-if="!compact && fill" :title="MARK[fill[l.code] ?? 0][2]"
        class="inline-grid h-5 min-w-5 place-items-center rounded-full px-1 text-[11px] font-bold" :class="MARK[fill[l.code] ?? 0][1]"
      >{{ MARK[fill[l.code] ?? 0][0] }}</span>
    </button>
  </div>
</template>
