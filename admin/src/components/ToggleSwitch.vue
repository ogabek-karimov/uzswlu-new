<script setup lang="ts">
defineProps<{ modelValue: boolean; label: string; on?: string }>()
defineEmits<{ 'update:modelValue': [boolean] }>()
</script>

<template>
  <button
    type="button" role="switch" :aria-checked="modelValue" :aria-label="label"
    class="relative h-[26px] w-[46px] shrink-0 rounded-full transition"
    :style="{ background: modelValue ? (on ?? 'var(--color-brand-700)') : '#D3CFE3' }"
    @click="$emit('update:modelValue', !modelValue)"
  >
    <span class="absolute top-[3px] size-5 rounded-full bg-white shadow transition-all" :class="modelValue ? 'left-[23px]' : 'left-[3px]'" />
  </button>
</template>
