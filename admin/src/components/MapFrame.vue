<script setup lang="ts">
import { ref } from 'vue'

// Xarita (iframe): sahifa aylantirilganda xarita «ushlab» qolmasin — bir marta bosilgach suriladi; kursor chiqsa yana qulflanadi
defineProps<{ src: string; title: string }>()
const active = ref(false)
</script>

<template>
  <div class="relative aspect-[4/3] w-full" @mouseleave="active = false">
    <iframe :src="src" loading="lazy" referrerpolicy="no-referrer-when-downgrade" :title="title" class="block size-full" :class="!active && 'pointer-events-none'" />
    <button v-if="!active" type="button" class="group absolute inset-0 grid cursor-pointer place-items-center" aria-label="Xaritani boshqarish uchun bosing" @click="active = true">
      <span class="pointer-events-none rounded-full bg-black/70 px-3.5 py-1.5 text-xs font-semibold text-white opacity-0 transition group-hover:opacity-100">Xaritani boshqarish uchun bosing</span>
    </button>
  </div>
</template>
