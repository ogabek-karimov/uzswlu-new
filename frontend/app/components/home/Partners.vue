<script setup lang="ts">
import type { Partner } from '#shared/types/api'

defineProps<{ partners: Partner[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
</script>

<template>
  <!-- Ramkasiz, butun kenglikdagi qorong'i tasma -->
  <section v-if="partners.length" class="relative isolate overflow-hidden bg-brand-900 py-14 lg:py-20">
    <div>
      <img src="/images/bg/conference.webp" alt="" width="1280" height="720" loading="lazy" decoding="async" class="decor bg-kb pointer-events-none absolute -inset-10 -z-20 size-[calc(100%+5rem)] max-w-none object-cover opacity-40">
      <span class="decor pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgb(28_21_72/0.85),rgb(28_21_72/0.6)_50%,rgb(28_21_72/0.88))]" aria-hidden="true" />
      <!-- Fon: xalqaro hamkorlik — globus chiziqlari (meridian va parallellar), juda xira -->
      <svg class="decor pointer-events-none absolute -top-28 -right-24 -z-10 size-[28rem] text-white/[0.07]" viewBox="0 0 400 400" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true">
        <circle cx="200" cy="200" r="190" /><ellipse cx="200" cy="200" rx="190" ry="70" /><ellipse cx="200" cy="200" rx="190" ry="130" />
        <ellipse cx="200" cy="200" rx="70" ry="190" /><ellipse cx="200" cy="200" rx="130" ry="190" /><path d="M10 200H390M200 10V390" />
      </svg>
      <svg class="decor pointer-events-none absolute -bottom-24 -left-16 -z-10 size-72 text-accent-400/[0.08]" viewBox="0 0 400 400" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true">
        <circle cx="200" cy="200" r="190" /><ellipse cx="200" cy="200" rx="190" ry="90" /><ellipse cx="200" cy="200" rx="90" ry="190" /><path d="M10 200H390M200 10V390" />
      </svg>
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          :eyebrow="t('partners.eyebrow')"
          :title="t('partners.title')"
          :text="t('partners.text')"
          :link="{ to: localePath('/hamkorlarimiz'), label: t('partners.all') }"
          dark
        />
      </div>

      <div class="group/marquee mt-10 [mask-image:linear-gradient(to_right,transparent,black_6%,black_94%,transparent)]">
        <ul class="flex w-max animate-marquee gap-5 will-change-transform pr-5 [animation-duration:50s] group-hover/marquee:[animation-play-state:paused]">
          <!-- Uzluksiz aylanish uchun ro'yxat ikki marta; ikkinchisi ekran o'quvchilardan yashirin -->
          <template v-for="copy in 2" :key="copy">
            <li
              v-for="partner in partners"
              :key="`${copy}-${partner.id}`"
              :aria-hidden="copy === 2 || undefined"
              class="shrink-0"
            >
              <component
                :is="partner.url ? 'a' : 'div'"
                v-bind="partner.url ? { href: partner.url, target: '_blank', rel: 'noopener', tabindex: copy === 2 ? -1 : undefined } : {}"
                :title="partner.name"
                class="flex h-28 w-44 items-center justify-center rounded-2xl bg-white p-5 transition duration-300 hover:shadow-[0_18px_40px_-24px_var(--color-accent-400)] sm:h-32 sm:w-52"
              >
                <img :src="partner.logo" :alt="copy === 1 ? partner.name : ''" loading="lazy" decoding="async" class="max-h-full max-w-full object-contain">
              </component>
            </li>
          </template>
        </ul>
      </div>
    </div>
  </section>
</template>
