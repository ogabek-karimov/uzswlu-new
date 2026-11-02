<script setup lang="ts">
// Ovozli o'qish ketayotganda pastda chiqadigan kichik panel — istalgan payt to'xtatish uchun
const { t } = useI18n()
const speech = useSpeech()
</script>

<template>
  <div v-if="speech.speaking.value" role="status" class="fixed right-4 bottom-4 z-[70] flex items-center gap-3 rounded-full bg-ink py-2 pr-2 pl-4 text-white shadow-[0_20px_40px_-16px_rgba(19,17,47,0.6)]">
    <Icon name="lucide:volume-2" class="size-5 animate-pulse text-accent-400" />
    <span class="text-sm font-semibold">{{ t('a11y.reading') }}</span>
    <button type="button" class="flex h-10 items-center gap-1.5 rounded-full bg-white px-4 text-sm font-bold text-ink transition-colors hover:bg-accent-400" @click="speech.stop">
      <Icon name="lucide:square" class="size-3.5" />
      {{ t('a11y.stop') }}
    </button>
  </div>
</template>
