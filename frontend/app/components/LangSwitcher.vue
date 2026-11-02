<script setup lang="ts">
const props = withDefaults(defineProps<{ variant?: 'dark' | 'light' }>(), { variant: 'light' })

const { t, locale, locales } = useI18n()
const switchLocalePath = useSwitchLocalePath()
const { open, root } = useDropdown()

const labels: Record<string, string> = { uz: 'UZ', ru: 'RU', en: 'EN', zh: '中文' }

const current = computed(() => locales.value.find(l => l.code === locale.value))
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="flex items-center gap-1.5 font-semibold transition-colors"
      :class="props.variant === 'dark'
        ? ['rounded-md px-2 py-1 text-[13px] text-white/85 hover:bg-white/10 hover:text-white', open && 'bg-white/10 text-white']
        : ['h-10 rounded-full px-3 text-sm text-ink/85 hover:bg-brand-50 hover:text-ink', open && 'bg-brand-50 text-ink']"
      :aria-expanded="open"
      aria-haspopup="true"
      aria-controls="lang-menu"
      :aria-label="`${t('topbar.language')}: ${current?.name}`"
      @click="open = !open"
    >
      <Icon name="lucide:globe" class="size-4" :class="props.variant === 'dark' ? 'text-accent-400' : 'text-brand-600'" />
      {{ labels[locale] }}
      <Icon name="lucide:chevron-down" class="size-3.5 opacity-70 transition-transform duration-200" :class="open && 'rotate-180'" />
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <ul
        v-if="open"
        id="lang-menu"
        class="absolute top-full right-0 z-[60] mt-2 w-48 rounded-xl border border-line bg-white p-1.5 text-ink shadow-[0_20px_40px_-16px_rgba(19,17,47,0.35)]"
      >
        <li v-for="l in locales" :key="l.code">
          <NuxtLink
            :to="switchLocalePath(l.code)"
            :hreflang="l.language"
            :lang="l.language"
            :aria-current="locale === l.code ? 'true' : undefined"
            class="flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-brand-50"
            :class="locale === l.code ? 'bg-brand-50 font-semibold text-brand-800' : 'text-ink/85'"
          >
            <span>{{ l.name }}</span>
            <Icon v-if="locale === l.code" name="lucide:check" class="size-4 text-brand-700" />
            <span v-else-if="labels[l.code] !== l.name" class="text-xs font-medium text-muted">{{ labels[l.code] }}</span>
          </NuxtLink>
        </li>
      </ul>
    </Transition>
  </div>
</template>
