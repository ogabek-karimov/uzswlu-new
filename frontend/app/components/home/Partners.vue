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
      <!-- Fon: xalqaro hamkorlik — globus chiziqlari (meridian va parallellar), juda xira -->
      <svg class="decor pointer-events-none absolute -top-28 -right-24 -z-10 size-[28rem] max-md:size-80" viewBox="0 0 400 400" fill="none" aria-hidden="true">
        <g class="text-white/[0.09]" stroke="currentColor" stroke-width="1">
          <circle cx="200" cy="200" r="190" />
          <ellipse class="globe-mer" cx="200" cy="200" rx="150" ry="190" />
          <ellipse class="globe-mer" style="animation-delay: -6s" cx="200" cy="200" rx="100" ry="190" />
          <ellipse class="globe-mer" style="animation-delay: -12s" cx="200" cy="200" rx="50" ry="190" />
          <path d="M10 200H390M26 120Q200 150 374 120M26 280Q200 250 374 280M70 52Q200 78 330 52M70 348Q200 322 330 348" />
        </g>
        <g class="text-accent-400/55" stroke="currentColor" stroke-width="1.4" stroke-linecap="round">
          <path class="globe-arc" d="M150 190Q215 90 290 140" />
          <path class="globe-arc" style="animation-delay: -1s" d="M150 190Q235 80 330 150" />
          <path class="globe-arc" style="animation-delay: -2s" d="M150 190Q90 100 70 112" />
          <path class="globe-arc" style="animation-delay: -2.6s" d="M150 190Q110 90 118 96" />
        </g>
        <g class="text-accent-400/70" fill="currentColor">
          <circle cx="150" cy="190" r="4.5" /><circle cx="290" cy="140" r="3.2" /><circle cx="330" cy="150" r="3.2" /><circle cx="70" cy="112" r="3.2" /><circle cx="118" cy="96" r="3.2" />
        </g>
        <g class="text-accent-400/60" stroke="currentColor" stroke-width="1.2">
          <circle class="globe-ping" cx="150" cy="190" r="8" /><circle class="globe-ping" style="animation-delay: -1s" cx="290" cy="140" r="6" /><circle class="globe-ping" style="animation-delay: -1.9s" cx="330" cy="150" r="6" />
        </g>
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
