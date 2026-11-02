<script setup lang="ts">
const { t } = useI18n()
const { data: site } = await useSiteData()
</script>

<template>
  <div class="bg-brand-950 text-[13px] text-white/70">
    <div class="mx-auto flex h-10 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
      <a v-if="site" :href="`tel:${site.phone.replace(/\s/g, '')}`" class="hidden items-center gap-2 transition-colors hover:text-white md:inline-flex">
        <Icon name="lucide:phone" class="size-3.5 text-accent-400" />
        <span>{{ t('topbar.hotline') }}:</span>
        <span class="font-medium text-white">{{ site.phone }}</span>
      </a>

      <!-- Telefonda — shu yerda; kattaroq ekranda menyu qatorida (TheHeader) -->
      <div class="ml-auto flex items-center md:hidden">
        <A11yControls />
      </div>
    </div>
  </div>
</template>
