<script setup lang="ts">
import type { I18n } from '@/lib/api'
import { LANGS } from '@/lib/constants'

// Bitta maydon 4 tilda (UZ · RU · EN · ZH). layout="grid" — "Nomi · Özbekça" yorliqli 2×2,
// "rows" — chapda til kodi, kiritish maydonlari ustma-ust.
const props = withDefaults(defineProps<{ modelValue: I18n | undefined; label: string; layout?: 'grid' | 'rows'; textarea?: boolean; rows?: number; required?: boolean; placeholders?: Partial<Record<keyof I18n, string>>; idPrefix?: string }>(), { layout: 'grid', rows: 3 })
const emit = defineEmits<{ 'update:modelValue': [I18n] }>()

const id = props.idPrefix ?? `i18n-${Math.random().toString(36).slice(2, 8)}`
function set(code: keyof I18n, value: string) {
  emit('update:modelValue', { ...(props.modelValue ?? {}), [code]: value })
}
</script>

<template>
  <div v-if="layout === 'grid'" class="grid gap-3 sm:grid-cols-2">
    <div v-for="l in LANGS" :key="l.code">
      <label :for="`${id}-${l.code}`" class="label">{{ label }} · {{ l.label }}<template v-if="required && l.code === 'uz'"> *</template></label>
      <textarea
        v-if="textarea" :id="`${id}-${l.code}`" :rows="rows" class="field h-auto! py-2.5 leading-normal" :required="required && l.code === 'uz'"
        :value="modelValue?.[l.code] ?? ''" :placeholder="placeholders?.[l.code]" @input="set(l.code, ($event.target as HTMLTextAreaElement).value)"
      />
      <input
        v-else :id="`${id}-${l.code}`" class="field" :required="required && l.code === 'uz'"
        :value="modelValue?.[l.code] ?? ''" :placeholder="placeholders?.[l.code]" @input="set(l.code, ($event.target as HTMLInputElement).value)"
      >
    </div>
  </div>
  <fieldset v-else>
    <legend class="label">{{ label }}</legend>
    <div class="flex flex-col gap-2">
      <label v-for="l in LANGS" :key="l.code" class="flex items-center gap-2">
        <span class="w-[30px] shrink-0 text-xs font-bold text-subtle">{{ l.short }}</span>
        <input class="field" :aria-label="`${label} · ${l.label}`" :value="modelValue?.[l.code] ?? ''" :placeholder="placeholders?.[l.code] ?? (l.code === 'zh' ? 'xitoyça' : '')" @input="set(l.code, ($event.target as HTMLInputElement).value)">
      </label>
    </div>
  </fieldset>
</template>
