<script setup lang="ts">
import type { Partner } from '#shared/types/api'

defineProps<{ partners: Partner[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
</script>

<template>
  <section v-if="partners.length" class="px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
    <div class="mx-auto max-w-7xl overflow-hidden rounded-[2rem] bg-brand-900 py-10 sm:py-12">
      <div class="px-6 sm:px-10">
        <SectionHeading
          :eyebrow="t('partners.eyebrow')"
          :title="t('partners.title')"
          :text="t('partners.text')"
          :link="{ to: localePath('/hamkorlarimiz'), label: t('partners.all') }"
          dark
        />
      </div>

      <div class="group/marquee mt-10 [mask-image:linear-gradient(to_right,transparent,black_6%,black_94%,transparent)]">
        <ul class="flex w-max animate-marquee gap-5 pr-5 [animation-duration:50s] group-hover/marquee:[animation-play-state:paused]">
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
                class="flex h-28 w-44 items-center justify-center rounded-2xl bg-white p-5 transition duration-300 hover:-translate-y-1 hover:shadow-[0_18px_40px_-24px_var(--color-accent-400)] sm:h-32 sm:w-52"
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
