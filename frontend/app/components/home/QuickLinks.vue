<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()
const NuxtLink = resolveComponent('NuxtLink')

const links = [
  { key: 'reception', icon: 'lucide:message-square-text', to: '/site/reception' },
  { key: 'student', icon: 'lucide:graduation-cap', href: 'https://student.uzswlu.uz' },
  { key: 'hemis', icon: 'lucide:database', href: 'https://hemis.uzswlu.uz' },
  { key: 'mail', icon: 'lucide:mail', to: '/services/mail' },
  { key: 'career', icon: 'lucide:briefcase-business', to: '/career' },
  { key: 'brm', icon: 'lucide:sprout', to: '/sdg-report' },
  { key: 'glossary', icon: 'lucide:book-a', to: '/services/glossary' },
]
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8" :aria-label="t('quick.title')">
    <div class="overflow-hidden rounded-3xl border border-line bg-white">
      <ul class="flex snap-x snap-mandatory overflow-x-auto [scrollbar-width:none] sm:grid sm:grid-cols-4 lg:grid-cols-7 lg:divide-x lg:divide-line">
        <li v-for="link in links" :key="link.key" class="min-w-[44%] shrink-0 snap-start sm:min-w-0">
          <component
            :is="link.href ? 'a' : NuxtLink"
            v-bind="link.href ? { href: link.href, target: '_blank', rel: 'noopener' } : { to: localePath(link.to!) }"
            class="group flex h-full flex-col gap-3 px-4 py-6 transition-colors hover:bg-brand-50 lg:px-5"
          >
            <span class="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-700 transition-colors group-hover:bg-brand-800 group-hover:text-accent-400">
              <Icon :name="link.icon" class="size-5" />
            </span>
            <span>
              <span class="flex items-center gap-1 text-[15px] font-semibold text-ink">
                {{ t(`quick.items.${link.key}.title`) }}
                <Icon v-if="link.href" name="lucide:arrow-up-right" class="size-3.5 text-muted" />
              </span>
              <span class="mt-0.5 block text-[13px] leading-snug text-muted">{{ t(`quick.items.${link.key}.text`) }}</span>
            </span>
          </component>
        </li>
      </ul>
    </div>
  </section>
</template>
