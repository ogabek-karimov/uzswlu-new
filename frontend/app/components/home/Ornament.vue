<script setup lang="ts">
// O'zbek naqshi (sakkiz qirrali yulduz — girih) takrorlanuvchi fon. Rangi — currentColor (ota elementning text-* rangi).
defineProps<{ size?: number }>()
const id = useId()
</script>

<template>
  <svg class="absolute inset-0 size-full" aria-hidden="true">
    <defs>
      <pattern :id="`orn-${id}`" :width="size ?? 88" :height="size ?? 88" patternUnits="userSpaceOnUse" viewBox="0 0 88 88">
        <g fill="none" stroke="currentColor" stroke-width="1.1">
          <!-- Ikki kvadrat (biri 45° burilgan) — sakkiz qirrali yulduz -->
          <rect x="26" y="26" width="36" height="36" />
          <rect x="26" y="26" width="36" height="36" transform="rotate(45 44 44)" />
          <circle cx="44" cy="44" r="7" />
          <!-- Qo'shni yulduzlarni bog'lovchi chiziqlar va burchakdagi kichik rombchalar -->
          <path d="M44 0v12M44 76v12M0 44h12M76 44h12" />
          <path d="M0 6 6 0M82 0l6 6M0 82l6 6M82 88l6-6" />
        </g>
      </pattern>
    </defs>
    <rect width="100%" height="100%" :fill="`url(#orn-${id})`" />
  </svg>
</template>
