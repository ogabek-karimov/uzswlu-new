<script setup lang="ts">
const { t } = useI18n()
const { data: site } = await useSiteData()
</script>

<template>
  <div class="bg-brand-950 text-[13px] text-white/70">
    <div class="relative mx-auto flex min-h-10 max-w-7xl items-center justify-center px-4 py-1.5 sm:px-6 lg:px-8">
      <!-- Ishonch telefoni: yuqori qatorning o'rtasida, barcha ekranlarda -->
      <a v-if="site" :href="`tel:${site.phone.replace(/\s/g, '')}`" class="inline-flex flex-wrap items-center justify-center gap-x-2 gap-y-0.5 text-center transition-colors hover:text-white max-md:max-w-[calc(100%-5.5rem)]">
        <Icon name="lucide:phone" class="size-3.5 shrink-0 text-accent-400" />
        <span>{{ t('topbar.hotline') }}:</span>
        <span class="font-medium text-white">{{ site.phone }}</span>
        <span v-if="site.phoneExt">({{ t('topbar.ext') }}: {{ formatExtensions(site.phoneExt) }})</span>
      </a>

      <!-- Telefonda — shu yerda (o'ng chetda); kattaroq ekranda menyu qatorida (TheHeader) -->
      <div class="absolute top-1/2 right-4 flex -translate-y-1/2 items-center sm:right-6 md:hidden">
        <A11yControls />
      </div>
    </div>
  </div>
</template>
