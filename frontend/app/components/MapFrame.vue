<script setup lang="ts">
// Xarita (iframe). Sahifa aylantirilganda xarita g'ildirak/barmoqni «ushlab» qolmasin: ustida shaffof qatlam turadi —
// bir marta bosilgach xaritani surish/kattalashtirish mumkin; kursor chiqib ketsa yana qulflanadi.
defineProps<{ src: string; title: string }>()

const { t } = useI18n()
const active = ref(false)
// Xarita yuklanganda — ota komponent yuklanish ekranini yopishi uchun
const emit = defineEmits<{ loaded: [] }>()
</script>

<template>
  <div class="absolute inset-0" @mouseleave="active = false">
    <iframe
      :src="src"
      loading="lazy"
      referrerpolicy="no-referrer-when-downgrade"
      :title="title"
      class="absolute inset-0 size-full border-0"
      :class="!active && 'pointer-events-none'"
      @load="emit('loaded')"
    />
    <button
      v-if="!active"
      type="button"
      class="group/map absolute inset-0 grid cursor-pointer place-items-center"
      :aria-label="t('map.activate')"
      @click="active = true"
    >
      <span class="pointer-events-none translate-y-1 rounded-full bg-ink/80 px-4 py-2 text-sm font-semibold text-white opacity-0 shadow-lg transition duration-200 group-hover/map:translate-y-0 group-hover/map:opacity-100 group-focus-visible/map:translate-y-0 group-focus-visible/map:opacity-100">
        {{ t('map.activate') }}
      </span>
    </button>
  </div>
</template>
