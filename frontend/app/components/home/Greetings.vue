<script setup lang="ts">
// Jahon tillaridagi salomlashuvlar tasmasi — bezak (ekran o'quvchilardan yashirin)
const words = ['Hello', 'Hallo', 'Bonjour', '你好', '안녕하세요', 'Hola', 'Ciao', 'こんにちは', 'Salom', 'Привет', 'مرحبا']
</script>

<template>
  <div class="overflow-hidden bg-accent-400 py-5 text-ink" aria-hidden="true">
    <div class="flex w-max animate-marquee gap-8 pr-8 font-display text-3xl font-semibold whitespace-nowrap [animation-duration:60s]">
      <template v-for="copy in 2" :key="copy">
        <span v-for="word in words" :key="`${copy}-${word}`" class="flex items-center gap-8">
          {{ word }}
          <span class="text-xl opacity-50">✦</span>
        </span>
      </template>
    </div>
  </div>
</template>
