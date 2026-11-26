<script setup lang="ts">
// Bölim sahifalari (çap menyu) — maxsus sahifalar uçun ([...slug].vue dagi bilan bir xil körinişda).
// Sahifa menyuda bölmasa hech narsa çiqmaydi.
const { t } = useI18n()
const route = useRoute()
const { data: site } = await useSiteData()
const path = computed(() => route.path.replace(/^\/(ru|en|zh)(?=\/|$)/, '').replace(/\/+$/, '') || '/')
const links = computed(() => site.value?.menu.find(g => g.links.some(l => l.url === path.value))?.links ?? [])
</script>

<template>
  <aside v-if="links.length" class="no-print order-2 min-w-0 lg:sticky lg:top-36 lg:order-1 lg:w-[320px] lg:shrink-0">
    <nav class="side-nav" :aria-label="t('page.sectionPages')">
      <p class="side-nav-title"><Icon name="lucide:layers" class="text-[15px]" />{{ t('page.sectionPages') }}</p>
      <ul class="flex flex-col gap-1 text-[15px]">
        <li v-for="link in links" :key="link.url">
          <span v-if="link.url === path" aria-current="page" class="side-nav-item side-nav-active">
            <Icon v-if="link.icon" :name="`lucide:${link.icon}`" class="size-[18px] shrink-0 text-brand-600" aria-hidden="true" />
                <span v-else class="side-nav-dot" aria-hidden="true" />
            <span class="min-w-0 flex-1">{{ link.title }}</span>
          </span>
          <NavMenuLink v-else :link="link" class="side-nav-item group">
            <Icon v-if="link.icon" :name="`lucide:${link.icon}`" class="size-[18px] shrink-0 text-brand-600" aria-hidden="true" />
                <span v-else class="side-nav-dot" aria-hidden="true" />
            <span class="min-w-0 flex-1">{{ link.title }}</span>
            <span v-if="link.file" class="self-center rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-bold text-red-700 uppercase">{{ link.file }}</span>
            <Icon v-else name="lucide:arrow-right" class="side-nav-arrow" />
          </NavMenuLink>
        </li>
      </ul>
    </nav>
  </aside>
</template>
