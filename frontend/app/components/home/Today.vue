<script setup lang="ts">
import type { EventItem } from '#shared/types/api'

// "Yaqin tadbir" yo'lagi — eng yaqin tadbir bo'lsa ko'rinadi
const props = defineProps<{ events: EventItem[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()

const next = computed(() => props.events[0])
</script>

<template>
  <section v-if="next" class="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
    <NuxtLink
      :to="localePath(`/events/${next.slug}`)"
      class="group flex flex-wrap items-center gap-x-6 gap-y-1 rounded-2xl bg-accent-100 px-5 py-3.5 text-[15px] text-ink transition-colors hover:brightness-95"
    >
      <span class="font-semibold text-accent-600">{{ t('events.eyebrow') }}</span>
      <span class="min-w-0 flex-1"><b>{{ next.title }}</b>, <time :datetime="next.startsAt">{{ formatDate(next.startsAt, 'datetime') }}</time></span>
      <span class="inline-flex items-center gap-1.5 font-semibold text-accent-600">
        {{ t('events.all') }}
        <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
      </span>
    </NuxtLink>
  </section>
</template>
