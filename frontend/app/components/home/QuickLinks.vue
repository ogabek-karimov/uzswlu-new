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
  <section class="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8 lg:pt-20" aria-labelledby="quick-title">
    <div class="mb-8 flex items-end justify-between gap-6">
      <div>
        <p class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">
          <span class="h-px w-8 bg-accent-500" />
          {{ t('quick.eyebrow') }}
        </p>
        <h2 id="quick-title" class="mt-3 font-display text-3xl leading-tight font-semibold tracking-tight text-ink sm:text-4xl">{{ t('quick.title') }}</h2>
      </div>
    </div>
    <div class="overflow-hidden rounded-3xl border border-line bg-white shadow-[0_24px_50px_-40px_var(--color-brand-700)]">
      <ul class="flex snap-x snap-mandatory overflow-x-auto [scrollbar-width:none] sm:grid sm:grid-cols-4 lg:grid-cols-7 lg:divide-x lg:divide-line">
        <li data-reveal-item v-for="link in links" :key="link.key" class="min-w-[44%] shrink-0 snap-start sm:min-w-0">
          <component
            :is="link.href ? 'a' : NuxtLink"
            v-bind="link.href ? { href: link.href, target: '_blank', rel: 'noopener' } : { to: localePath(link.to!) }"
            class="group relative flex h-full flex-col gap-3 px-4 py-6 transition-colors hover:bg-brand-50 focus-visible:bg-brand-50 lg:px-5"
          >
            <span class="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-700 transition duration-300 group-hover:-translate-y-1 group-hover:-rotate-6 group-hover:bg-brand-800 group-hover:text-accent-400 group-hover:shadow-[0_12px_24px_-12px_var(--color-brand-800)] motion-reduce:transition-none motion-reduce:group-hover:transform-none">
              <Icon :name="link.icon" class="size-5" />
            </span>
            <span>
              <span class="flex min-h-[2lh] items-start gap-1 text-[15px] font-semibold text-ink">
                {{ t(`quick.items.${link.key}.title`) }}
                <Icon v-if="link.href" name="lucide:arrow-up-right" class="size-3.5 text-muted" />
              </span>
              <span class="mt-0.5 line-clamp-3 min-h-[3lh] text-[13px] leading-snug text-muted">{{ t(`quick.items.${link.key}.text`) }}</span>
            </span>
            <!-- ustiga olib borilganda chapdan o'ngga o'sadigan mint chiziq -->
            <span class="pointer-events-none absolute inset-x-4 bottom-0 h-0.5 origin-left scale-x-0 rounded-full bg-accent-400 transition-transform duration-300 group-hover:scale-x-100 group-focus-visible:scale-x-100 motion-reduce:transition-none lg:inset-x-5" aria-hidden="true" />
          </component>
        </li>
      </ul>
    </div>
  </section>
</template>
