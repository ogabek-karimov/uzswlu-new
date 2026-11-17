<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()
const NuxtLink = resolveComponent('NuxtLink')
const { data: home } = await useHomeData()

// Kartalar admin paneldagi «Tezkor xizmatlar» sahifasidan keladi. Ikonkalar sayt paketiga yig'ilishi uchun ruxsat etilgan nomlar
// shu yerda LITERAL qatorlar bilan yozilgan (admin panel va backend `apps/content/quick_links.py` bilan bir xil bo'lishi shart).
const ALLOWED = [
  'lucide:message-square-text',
  'lucide:graduation-cap',
  'lucide:database',
  'lucide:mail',
  'lucide:briefcase-business',
  'lucide:sprout',
  'lucide:book-a',
  'lucide:smartphone',
  'lucide:globe',
  'lucide:calendar-days',
  'lucide:file-text',
  'lucide:library',
  'lucide:phone',
  'lucide:users',
  'lucide:video',
  'lucide:map-pin',
  'lucide:award',
  'lucide:life-buoy',
]
const links = computed(() => (home.value?.quickLinks ?? []).map(q => ({ ...q, icon: ALLOWED.includes(q.icon) ? q.icon : 'lucide:globe' })))
</script>

<template>
  <section v-if="links.length" class="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8 lg:pt-20" aria-labelledby="quick-title">
    <div class="mb-8 flex items-end justify-between gap-6">
      <div>
        <p class="flex items-center gap-3 text-xs font-semibold tracking-[0.2em] text-accent-600 uppercase">
          <span class="h-px w-8 bg-accent-500" />
          {{ t('quick.eyebrow') }}
        </p>
        <h2 id="quick-title" class="mt-3 font-display text-3xl leading-tight font-semibold tracking-tight text-ink sm:text-4xl">{{ t('quick.title') }}</h2>
      </div>
    </div>
    <div>
      <ul class="-mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-3 [scrollbar-width:none] sm:mx-0 sm:grid sm:grid-cols-4 sm:overflow-visible sm:px-0 sm:pb-0 lg:grid-cols-7">
        <li data-reveal-item v-for="link in links" :key="link.id" class="group/li min-w-[46%] shrink-0 snap-start sm:min-w-0">
          <component
            :is="link.external ? 'a' : NuxtLink"
            v-bind="link.external ? { href: link.url, target: '_blank', rel: 'noopener' } : { to: localePath(link.url) }"
            data-spot class="group relative flex h-full flex-col gap-3 overflow-hidden rounded-3xl border border-line bg-white px-4 py-5 shadow-[0_1px_0_rgba(19,17,47,0.04)] transition duration-300 group-hover/li:-translate-y-1 hover:border-brand-200 hover:bg-brand-50 hover:shadow-[0_26px_50px_-30px_var(--color-brand-700)] focus-visible:-translate-y-1 focus-visible:bg-brand-50 lg:px-5 motion-reduce:transition-none motion-reduce:group-hover/li:translate-y-0"
          >
            <span class="decor pointer-events-none absolute -top-8 -right-8 size-24 rounded-full bg-brand-100/60 transition-transform duration-500 group-hover:scale-150 group-hover:bg-accent-100 motion-reduce:transition-none" aria-hidden="true" />
            <span class="relative grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-700 transition duration-300 group-group-hover/li:-translate-y-1 group-hover:-rotate-6 group-hover:bg-brand-800 group-hover:text-accent-400 group-hover:shadow-[0_12px_24px_-12px_var(--color-brand-800)] motion-reduce:transition-none motion-reduce:group-hover:transform-none">
              <Icon :name="link.icon" class="size-5" />
            </span>
            <span>
              <span class="flex min-h-[2lh] items-start gap-1 text-[15px] font-semibold text-ink">
                {{ link.title }}
                <Icon v-if="link.external" name="lucide:arrow-up-right" class="size-3.5 text-muted" />
              </span>
              <span v-if="link.text" class="mt-0.5 line-clamp-3 min-h-[3lh] text-[13px] leading-snug text-muted">{{ link.text }}</span>
            </span>
            <!-- ustiga olib borilganda chapdan o'ngga o'sadigan mint chiziq -->
            <span class="pointer-events-none absolute inset-x-4 bottom-0 h-0.5 origin-left scale-x-0 rounded-full bg-accent-400 transition-transform duration-300 group-hover:scale-x-100 group-focus-visible:scale-x-100 motion-reduce:transition-none lg:inset-x-5" aria-hidden="true" />
          </component>
        </li>
      </ul>
    </div>
  </section>
</template>
