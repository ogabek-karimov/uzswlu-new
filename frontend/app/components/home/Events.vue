<script setup lang="ts">
import type { EventItem } from '#shared/types/api'

defineProps<{ events: EventItem[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()
</script>

<template>
  <section class="bg-brand-50/70">
    <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
    <SectionHeading
      :eyebrow="t('events.eyebrow')"
      :title="t('events.title')"
      :link="{ to: localePath('/events'), label: t('events.all') }"
    />

    <ul v-if="events.length" class="mt-12 grid gap-4 md:grid-cols-3">
      <li v-for="event in events" :key="event.id">
        <article class="group relative flex h-full flex-col rounded-2xl border border-line bg-white p-6 transition duration-300 hover:-translate-y-1 hover:border-brand-300 hover:shadow-[0_24px_50px_-28px_var(--color-brand-700)]">
          <div class="flex items-start justify-between gap-4">
            <time :datetime="event.startsAt" class="flex items-end gap-3">
              <span class="font-display text-6xl leading-[0.85] font-semibold text-brand-800">{{ formatDate(event.startsAt, 'day') }}</span>
              <span class="pb-0.5 leading-tight">
                <span class="block text-sm font-semibold text-ink">{{ formatDate(event.startsAt, 'month') }}</span>
                <span class="block text-xs text-muted first-letter:uppercase">{{ formatDate(event.startsAt, 'weekday') }}</span>
              </span>
            </time>
            <span v-if="event.category" class="shrink-0 rounded-full bg-accent-100 px-3 py-1 text-xs font-semibold text-accent-600">{{ event.category }}</span>
          </div>

          <h3 class="mt-6 line-clamp-3 min-h-[3lh] text-lg leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700">
            <NuxtLink :to="localePath(`/events/${event.slug}`)">
              <span class="absolute inset-0" aria-hidden="true" />
              {{ event.title }}
            </NuxtLink>
          </h3>

          <dl class="mt-auto space-y-2 border-t border-line pt-5 text-sm text-muted">
            <div class="flex items-center gap-2">
              <dt class="sr-only">{{ t('events.time') }}</dt>
              <Icon name="lucide:clock" class="size-4 shrink-0 text-brand-500" />
              <dd>{{ formatDate(event.startsAt, 'time') }}<template v-if="event.endsAt"> – {{ formatDate(event.endsAt, 'time') }}</template></dd>
            </div>
            <div class="flex min-w-0 items-center gap-2">
              <dt class="sr-only">{{ t('events.place') }}</dt>
              <Icon name="lucide:map-pin" class="size-4 shrink-0 text-brand-500" />
              <dd class="truncate" :title="event.location">{{ event.location }}</dd>
            </div>
          </dl>
        </article>
      </li>
    </ul>

    <p v-else class="mt-12 rounded-2xl border border-dashed border-line p-10 text-center text-muted">{{ t('events.empty') }}</p>
      </div>
  </section>
</template>
