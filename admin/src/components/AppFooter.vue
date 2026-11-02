<script setup lang="ts">
import { VERSION } from '@/lib/constants'
import { siteSettings } from '@/lib/settings'
import TelegramIcon from './TelegramIcon.vue'
</script>

<template>
  <footer class="flex flex-wrap items-center justify-between gap-x-5 gap-y-2 border-t border-line px-4 pt-4 pb-6 text-[13px] text-subtle sm:px-8">
    <span class="flex flex-wrap items-center gap-x-3.5 gap-y-2">
      <span>© 2026 ÖzDJTU · Boşqaruv paneli</span>
      <span class="chip bg-brand-100 text-brand-800" title="Admin panel versiyasi">Versiya {{ VERSION }}</span>
    </span>
    <span class="flex flex-wrap items-center gap-x-[18px] gap-y-2">
      <a :href="siteSettings.supportUrl" target="_blank" rel="noopener" class="inline-flex items-center gap-1.5 font-semibold text-[#3D3958] hover:text-brand-700">
        <TelegramIcon :size="16" /> {{ siteSettings.supportText }}
      </a>
      <span>Işlab çiqdi: <b class="font-semibold text-[#3D3958]">Oğabek Karimov</b></span>
    </span>
  </footer>
</template>
