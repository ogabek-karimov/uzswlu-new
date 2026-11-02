<script setup lang="ts">
const { t } = useI18n()
const i18nHead = useLocaleHead()

useHead(() => ({
  htmlAttrs: { lang: i18nHead.value.htmlAttrs?.lang },
  link: i18nHead.value.link ?? [],
  meta: [
    ...(i18nHead.value.meta ?? []),
    { name: 'description', content: t('meta.description') },
    { name: 'theme-color', content: '#1c1548' },
  ],
  titleTemplate: (title?: string) => (title ? `${title} — ${t('university.short')}` : t('university.name')),
}))
</script>

<template>
  <NuxtRouteAnnouncer />
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
