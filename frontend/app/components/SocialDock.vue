<script setup lang="ts">
// Chap chetdagi panel (eski saytdagidek): ijtimoiy tarmoqlar va «Öquv binolari».
// Keng ekranda (≥1360px) doim ochiq; torroq ekranda kontentni yopmasligi uchun chetga yig'iladi —
// kursor kelsa yoki tilcha bosilsa chiqadi. Telefonda bu havolalar mobil menyuda.
const { t } = useI18n()
const localePath = useLocalePath()
const route = useRoute()
const { data: site } = await useSiteData()

const socials = computed(() => sortSocials(site.value?.socials ?? []))
const open = ref(false)
watch(() => route.fullPath, () => (open.value = false))

const item = 'group relative grid size-10 place-items-center rounded-[14px] outline-none transition-transform duration-200 hover:translate-x-0.5 focus-visible:ring-2 focus-visible:ring-brand-400'
const tip = 'pointer-events-none absolute top-1/2 left-full z-10 ml-3 -translate-x-1 -translate-y-1/2 rounded-lg bg-ink px-2.5 py-1 text-xs font-semibold whitespace-nowrap text-white opacity-0 shadow-lg transition duration-200 group-hover:translate-x-0 group-hover:opacity-100 group-focus-visible:translate-x-0 group-focus-visible:opacity-100'
</script>

<template>
  <nav class="social-dock fixed top-1/2 left-0 z-40 hidden items-center md:flex print:hidden" :class="open && 'is-open'" :aria-label="t('social.title')">
    <ul class="flex flex-col gap-1 rounded-r-[20px] border border-l-0 border-line bg-white p-1.5 shadow-[0_18px_40px_-22px_rgba(19,17,47,0.5)]">
      <li v-for="s in socials" :key="s.network">
        <a :href="s.url" target="_blank" rel="noopener" :class="[item, siteNetworks[s.network].ink]" :aria-label="siteNetworks[s.network].label">
          <span aria-hidden="true" class="absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100" :class="siteNetworks[s.network].fill" />
          <Icon :name="siteNetworks[s.network].icon" class="relative text-[1.15rem] transition-colors duration-200 group-hover:text-white group-focus-visible:text-white" />
          <span aria-hidden="true" :class="tip">{{ siteNetworks[s.network].label }}</span>
        </a>
      </li>
      <li v-if="socials.length" aria-hidden="true" class="mx-auto my-0.5 h-px w-6 bg-line" />
      <li>
        <NuxtLink :to="localePath('/oquv-binolari')" :class="[item, 'text-brand-700']" :aria-label="t('social.buildings')">
          <span aria-hidden="true" class="absolute inset-0 rounded-[inherit] bg-brand-700 opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100" />
          <Icon name="lucide:landmark" class="relative text-[1.15rem] transition-colors duration-200 group-hover:text-white group-focus-visible:text-white" />
          <span aria-hidden="true" :class="tip">{{ t('social.buildings') }}</span>
        </NuxtLink>
      </li>
    </ul>
    <button
      type="button"
      class="dock-toggle -ml-px h-14 w-5 place-items-center rounded-r-xl border border-l-0 border-line bg-white text-muted shadow-[0_12px_24px_-16px_rgba(19,17,47,0.5)] transition-colors hover:text-ink"
      :aria-expanded="open"
      :aria-label="open ? t('social.hide') : t('social.show')"
      @click="open = !open"
    >
      <Icon :name="open ? 'lucide:chevron-left' : 'lucide:chevron-right'" class="text-sm" />
    </button>
  </nav>
</template>

<style scoped>
.social-dock {
  transform: translateY(-50%);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.dock-toggle {
  display: none;
}
/* Tor ekranda chetga yig'iladi: faqat tilcha ko'rinadi */
@media (max-width: 1359.98px) {
  .social-dock {
    transform: translate(calc(-100% + 1.25rem), -50%);
  }
  .social-dock:hover,
  .social-dock:focus-within,
  .social-dock.is-open {
    transform: translateY(-50%);
  }
  .dock-toggle {
    display: grid;
  }
}
@media (prefers-reduced-motion: reduce) {
  .social-dock {
    transition: none;
  }
}
</style>
