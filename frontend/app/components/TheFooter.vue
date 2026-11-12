<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()
const { data: site } = await useSiteData()

// Davlat ramzlari havolasi — admin paneldagi "Ramzlar" bo'limidan (bo'lmasa standart)
const symbolHref = (key: string, fallback: string) => {
  const s = site.value?.symbols?.find(x => x.key === key)
  return s?.href || s?.audio || fallback
}

const usefulLinks = [
  { label: 'menu.applicants.items.admission', to: '/qabul-20262027' },
  { label: 'menu.applicants.items.bachelor', to: '/bakalavriat' },
  { label: 'menu.university.items.library', to: '/axborot-resurs-markazi' },
  { label: 'menu.activity.items.documents', to: '/meyoriy-hujjatlar' },
  { label: 'menu.activity.items.anticorruption', to: '/korrupsiyaga-qarshi-kurashish' },
]
</script>

<template>
  <footer class="bg-brand-950 text-white/65">
    <div class="mx-auto grid max-w-7xl gap-12 px-4 pt-10 pb-12 sm:px-6 lg:grid-cols-12 lg:gap-8 lg:px-8">
      <div class="lg:col-span-4">
        <NuxtLink :to="localePath('/')" class="flex items-center gap-3">
          <BrandMark class="size-14" />
          <span class="leading-tight">
            <span class="block font-semibold text-white">{{ t('university.line1') }}</span>
            <span class="block font-semibold text-white">{{ t('university.line2') }}</span>
          </span>
        </NuxtLink>
        <p class="mt-6 max-w-sm text-sm leading-relaxed">{{ t('footer.about') }}</p>
      </div>

      <!-- Bog'lanish, foydali havolalar va QR kod (binolar — bosh sahifadagi «Biz bilan bog'lanish» va Aloqa sahifasida) -->
      <div class="grid gap-10 sm:grid-cols-2 lg:col-span-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] lg:gap-8">
        <div>
          <p class="text-sm font-semibold text-white">{{ t('footer.contacts') }}</p>
          <ul v-if="site" class="mt-5 space-y-3 text-sm">
            <li class="flex gap-3">
              <Icon name="lucide:phone" class="mt-0.5 size-4 shrink-0 text-accent-400" />
              <span>
                <a :href="`tel:${site.phone.replace(/\s/g, '')}`" class="font-medium text-white/90 hover:text-white">{{ site.phone }}</a>
                <span class="block text-xs text-white/45">{{ t('footer.ext') }}: {{ formatExtensions(site.phoneExt) }}</span>
              </span>
            </li>
            <li v-for="email in site.emails" :key="email" class="flex gap-3">
              <Icon name="lucide:mail" class="mt-0.5 size-4 shrink-0 text-accent-400" />
              <a :href="`mailto:${email}`" class="break-all hover:text-white">{{ email }}</a>
            </li>
          </ul>
        </div>

        <div>
          <p class="text-sm font-semibold text-white">{{ t('footer.links') }}</p>
          <ul class="mt-5 space-y-2.5 text-sm">
            <li v-for="link in usefulLinks" :key="link.to">
              <NuxtLink :to="localePath(link.to)" class="transition-colors hover:text-accent-400">{{ t(link.label) }}</NuxtLink>
            </li>
          </ul>
        </div>

        <figure class="flex flex-col items-start gap-3">
          <img src="/images/footer-qr.png" :alt="t('footer.qr.alt')" width="132" height="132" loading="lazy" class="size-[132px] rounded-2xl bg-white p-1.5 [image-rendering:pixelated]">
          <figcaption class="max-w-[132px] text-xs leading-snug text-white/55">{{ t('footer.qr.caption') }}</figcaption>
        </figure>
      </div>
    </div>

    <div class="border-t border-white/10">
      <div class="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 text-xs text-white/45 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
        <p>{{ t('footer.copyright', { year: new Date().getFullYear(), name: t('university.name'), rights: t('footer.rights') }) }}</p>
        <nav :aria-label="t('footer.symbols.title')" class="flex flex-wrap items-center gap-x-5 gap-y-2">
          <span class="text-white/30">{{ t('footer.symbols.title') }}:</span>
          <a v-for="s in stateSymbols" :key="s.key" :href="symbolHref(s.key, s.href)" target="_blank" rel="noopener" class="transition-colors hover:text-white">
            {{ t(`footer.symbols.${s.key}`) }}
          </a>
        </nav>
      </div>
    </div>
  </footer>
</template>
