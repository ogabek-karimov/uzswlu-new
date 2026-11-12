<script setup lang="ts">
const { t } = useI18n()
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <a
      href="#main"
      class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:bg-accent-400 focus:px-4 focus:py-2 focus:font-semibold focus:text-ink"
    >
      {{ t('nav.skip') }}
    </a>
    <TheTopBar />
    <TheHeader />
    <main id="main" class="flex-1">
      <slot />
    </main>
    <TheFooter />
    <SocialDock />
    <A11ySpeechBar />
  </div>
</template>
