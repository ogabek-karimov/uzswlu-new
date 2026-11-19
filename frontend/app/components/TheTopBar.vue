<script setup lang="ts">
const { t } = useI18n()
const { data: site } = await useSiteData()

</script>

<template>
  <div class="bg-[#2f2675] text-[13px] text-white/75">
    <div class="mx-auto flex min-h-10 max-w-7xl items-center justify-center px-4 py-1.5 max-md:justify-between max-md:gap-3 sm:px-6 lg:px-8">
      <!-- Ishonch telefoni: yuqori qatorning o'rtasida, barcha ekranlarda -->
      <a v-if="site" :href="`tel:${site.phone.replace(/\s/g, '')}`" class="inline-flex flex-wrap items-center justify-center gap-x-2 gap-y-0.5 text-center transition-colors hover:text-white max-md:min-w-0 max-md:flex-1 max-md:justify-start max-md:text-left">
        <Icon name="lucide:phone" class="size-3.5 shrink-0 text-accent-400" />
        <span>{{ t('topbar.hotline') }}:</span>
        <span class="font-medium text-white">{{ site.phone }}</span>
        <span v-if="site.phoneExt">({{ t('topbar.ext') }}: {{ formatExtensions(site.phoneExt) }})</span>
      </a>

      <!-- Telefonda — shu yerda, telefon yonida (oqimda, ustma-ust tushmasin); kattaroq ekranda menyu qatorida (TheHeader) -->
      <div class="flex shrink-0 items-center md:hidden">
        <A11yControls />
      </div>
    </div>
  </div>
</template>
