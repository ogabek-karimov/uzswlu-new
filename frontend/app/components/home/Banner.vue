<script setup lang="ts">
import type { HomeBanner } from '#shared/types/api'

// Bayram banneri (masalan, Mustaqillik bayrami): admin panelda bitta rasm, ko'z belgisi bilan yashiriladi.
// Rasm o'z nisbatida, konteyner kengligida; havola berilsa — bosiladi
const props = defineProps<{ banner: HomeBanner | null }>()

const localePath = useLocalePath()
const external = computed(() => /^https?:\/\//.test(props.banner?.link ?? ''))
const to = computed(() => (props.banner?.link && !external.value ? localePath(props.banner.link) : undefined))
</script>

<template>
  <section v-if="banner" class="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8 lg:pb-16">
    <component
      :is="banner.link ? (external ? 'a' : resolveComponent('NuxtLink')) : 'div'"
      :href="external ? banner.link : undefined"
      :to="to"
      :target="external ? '_blank' : undefined"
      :rel="external ? 'noopener' : undefined"
      class="group block overflow-hidden rounded-[24px] bg-brand-950 shadow-[0_30px_60px_-36px_rgba(19,17,47,0.6)]"
    >
      <img
        :src="banner.image"
        :alt="banner.alt"
        :width="banner.width ?? undefined"
        :height="banner.height ?? undefined"
        loading="lazy"
        decoding="async"
        class="block h-auto w-full transition-transform duration-700 ease-out motion-reduce:transition-none"
        :class="banner.link && 'group-hover:scale-[1.015]'"
      >
    </component>
  </section>
</template>
