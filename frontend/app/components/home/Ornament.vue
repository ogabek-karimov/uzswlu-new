<script setup lang="ts">
// O'zbek naqshlari — takrorlanuvchi fon. Rangi — currentColor (ota elementning text-* rangi).
//   girih — sakkiz qirrali yulduz (yangiliklar), suzani — gul-rozetkalar (e'lonlar), ikat — atlas rombchalari (tadbirlar), arch — ravoqlar
const props = withDefaults(defineProps<{ kind?: 'girih' | 'arch' | 'ikat' | 'suzani' }>(), { kind: 'girih' })
const id = useId()
const tile = computed(() => ({ girih: [88, 88], arch: [64, 72], ikat: [48, 72], suzani: [80, 80] }[props.kind]))
</script>

<template>
  <svg class="absolute inset-0 size-full" aria-hidden="true">
    <defs>
      <pattern :id="`orn-${id}`" :width="tile[0]" :height="tile[1]" patternUnits="userSpaceOnUse" :viewBox="`0 0 ${tile[0]} ${tile[1]}`">
        <g v-if="kind === 'girih'" fill="none" stroke="currentColor" stroke-width="1.1">
          <!-- Ikki kvadrat (biri 45° burilgan) — sakkiz qirrali yulduz -->
          <rect x="26" y="26" width="36" height="36" />
          <rect x="26" y="26" width="36" height="36" transform="rotate(45 44 44)" />
          <circle cx="44" cy="44" r="7" />
          <path d="M44 0v12M44 76v12M0 44h12M76 44h12" />
          <path d="M0 6 6 0M82 0l6 6M0 82l6 6M82 88l6-6" />
        </g>
        <g v-else-if="kind === 'suzani'" fill="none" stroke="currentColor" stroke-width="1.2">
          <!-- Suzani rozetkasi: doira, sakkizta gulbarg va o'rtada to'la gul; burchaklarda kichik gulchalar -->
          <circle cx="40" cy="40" r="17" />
          <ellipse v-for="a in [0, 45, 90, 135, 180, 225, 270, 315]" :key="a" cx="40" cy="27" rx="3.6" ry="7.5" :transform="`rotate(${a} 40 40)`" />
          <circle cx="40" cy="40" r="4.5" fill="currentColor" stroke="none" />
          <g v-for="[x, y] in [[0, 0], [80, 0], [0, 80], [80, 80]]" :key="`${x}-${y}`">
            <circle :cx="x" :cy="y" r="6" />
            <circle :cx="x" :cy="y" r="2" fill="currentColor" stroke="none" />
          </g>
        </g>
        <g v-else-if="kind === 'arch'" fill="none" stroke="currentColor" stroke-width="1.2">
          <!-- O'tkir uchli ravoq (peshtoq) va ichida kichigi; qatorlar yarim qadamga surilgan -->
          <path d="M8 72V40Q8 16 32 8Q56 16 56 40V72" />
          <path d="M18 72V44Q18 26 32 19Q46 26 46 44V72" />
          <path d="M32 0v8M0 36h8M56 36h8" />
          <circle cx="32" cy="34" r="2.2" fill="currentColor" stroke="none" />
        </g>
        <g v-else fill="none" stroke="currentColor" stroke-width="1.2">
          <!-- Atlas (ikat): tishli rombchalar zanjiri va ichida kichik romb -->
          <path d="M24 2 30 10 28 12 36 18 28 24 30 26 24 34 18 26 20 24 12 18 20 12 18 10Z" />
          <path d="M24 38 30 46 28 48 36 54 28 60 30 62 24 70 18 62 20 60 12 54 20 48 18 46Z" />
          <path d="M24 12 30 18 24 24 18 18Z" fill="currentColor" stroke="none" opacity="0.6" />
          <path d="M0 36h6M42 36h6" />
        </g>
      </pattern>
    </defs>
    <rect width="100%" height="100%" :fill="`url(#orn-${id})`" />
  </svg>
</template>
