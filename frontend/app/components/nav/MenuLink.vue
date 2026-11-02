<script setup lang="ts">
import type { MenuLink } from '#shared/types/api'

const props = defineProps<{ link: MenuLink }>()

const localePath = useLocalePath()
const NuxtLink = resolveComponent('NuxtLink')

const external = computed(() => isExternal(props.link))
</script>

<!-- Ichki sahifa — NuxtLink (til prefiksi bilan), PDF va tashqi manzil — oddiy havola -->
<template>
  <component
    :is="external ? 'a' : NuxtLink"
    v-bind="external ? { href: link.url, target: '_blank', rel: 'noopener' } : { to: localePath(link.url) }"
  >
    <slot />
  </component>
</template>
