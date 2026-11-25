<script setup lang="ts">
// Korporativ poçta: kirish tartibi va qoidalar; poçtaning o'zi webmail.uzswlu.uz da
const { t } = useI18n()
const localePath = useLocalePath()
const WEBMAIL = 'https://webmail.uzswlu.uz/'

const access = computed(() => [0, 1, 2].map(i => ({ title: t(`corpMail.access[${i}].title`), text: t(`corpMail.access[${i}].text`) })))
const rules = computed(() => [0, 1, 2, 3].map(i => t(`corpMail.rules[${i}]`)))

useSeo({ title: () => t('corpMail.title'), description: () => t('corpMail.lead') })
</script>

<template>
  <div>
    <PageIntro :crumbs="[{ label: t('corpMail.title') }]" :title="t('corpMail.title')" :lead="t('corpMail.lead')">
      <div class="flex flex-col items-start gap-2">
        <a :href="WEBMAIL" target="_blank" rel="noopener" class="inline-flex h-[56px] items-center gap-2.5 rounded-full bg-accent-400 px-7 text-base font-semibold text-brand-950 transition-colors hover:bg-white">
          <Icon name="lucide:mail" class="size-5" />
          {{ t('corpMail.open') }}
          <Icon name="lucide:arrow-up-right" class="size-4" />
        </a>
        <span class="text-[13px] text-white/60">{{ t('corpMail.openHint') }}</span>
      </div>
    </PageIntro>

    <section class="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8" aria-labelledby="cm-access">
      <h2 id="cm-access" class="font-display text-4xl font-semibold sm:text-[40px]">{{ t('corpMail.accessTitle') }}</h2>
      <ul class="mt-6 grid gap-4 md:grid-cols-3">
        <li v-for="(a, i) in access" :key="i" class="rounded-3xl border border-line bg-white p-6">
          <h3 class="text-lg font-semibold">{{ a.title }}</h3>
          <p class="mt-1.5 text-[15px] leading-relaxed text-muted">{{ a.text }}</p>
        </li>
      </ul>
    </section>

    <section class="mx-auto grid max-w-7xl gap-7 px-4 pt-16 pb-24 sm:px-6 lg:grid-cols-[1.2fr_1fr] lg:px-8">
      <div class="rounded-[28px] bg-brand-50 p-6 sm:p-8">
        <h2 class="font-display text-[30px] font-semibold">{{ t('corpMail.rulesTitle') }}</h2>
        <ul class="mt-5 grid gap-3">
          <li v-for="(r, i) in rules" :key="i" class="flex gap-3 text-[15px] leading-relaxed text-ink/85">
            <Icon name="lucide:shield-check" class="mt-0.5 size-5 shrink-0 text-accent-600" />
            {{ r }}
          </li>
        </ul>
      </div>
      <div class="rounded-[28px] bg-brand-950 p-6 text-white sm:p-8">
        <h2 class="font-display text-[30px] font-semibold">{{ t('corpMail.helpTitle') }}</h2>
        <p class="mt-3 text-white/70">{{ t('corpMail.helpText') }}</p>
        <NuxtLink :to="localePath('/aloqa')" class="mt-6 inline-flex h-[52px] items-center gap-2 rounded-full border border-white/25 px-6 font-semibold transition-colors hover:bg-white hover:text-ink">
          {{ t('corpMail.helpCta') }}
          <Icon name="lucide:arrow-right" class="size-4" />
        </NuxtLink>
      </div>
    </section>
    <SectionNav />
  </div>
</template>
