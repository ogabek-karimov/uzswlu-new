<script setup lang="ts">
import type { EventItem } from '#shared/types/api'

defineProps<{ events: EventItem[] }>()

const { t } = useI18n()
const localePath = useLocalePath()
const formatDate = useFormatDate()
</script>

<template>
  <section class="relative isolate overflow-hidden bg-brand-50/70">
    <!-- Fon: taqvim katakchalari (o'ng-tepadan so'nadi) va katta xira taqvim belgisi -->
    <div class="decor pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <span class="events-grid absolute inset-0" />
      <Icon name="lucide:calendar-days" class="absolute -bottom-10 -left-8 size-72 -rotate-12 text-brand-600/[0.06]" />
    </div>
    <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
    <SectionHeading
      :eyebrow="t('events.eyebrow')"
      :title="t('events.title')"
      :link="{ to: localePath('/events'), label: t('events.all') }"
    />

    <ul v-if="events.length" class="mt-12 grid gap-4 md:grid-cols-3">
      <li data-reveal-item class="group/li" v-for="event in events" :key="event.id">
        <article class="group relative flex h-full flex-col overflow-hidden rounded-[28px] border border-line bg-white transition duration-300 group-hover/li:-translate-y-1 hover:border-brand-300 hover:shadow-[0_30px_60px_-32px_var(--color-brand-700)] motion-reduce:transition-none motion-reduce:group-hover/li:translate-y-0">
          <!-- Sarlavha: to'q gradient, katta sana, toifa -->
          <div class="relative overflow-hidden bg-gradient-to-br from-brand-800 via-brand-900 to-brand-950 px-6 pt-6 pb-7 text-white">
            <span class="decor pointer-events-none absolute -top-10 -right-10 size-40 rounded-full border-[1.6rem] border-white/[0.06] transition-transform duration-700 group-hover:scale-125 motion-reduce:transition-none" aria-hidden="true" />
            <span class="decor pointer-events-none absolute -bottom-12 left-1/3 size-32 rounded-full bg-accent-400/15 blur-2xl" aria-hidden="true" />
            <div class="relative flex items-start justify-between gap-3">
              <time :datetime="event.startsAt" class="flex items-end gap-3">
                <span class="font-display text-[4.25rem] leading-[0.82] font-semibold text-white">{{ formatDate(event.startsAt, 'day') }}</span>
                <span class="pb-0.5 leading-tight">
                  <span class="block text-sm font-semibold text-accent-300">{{ formatDate(event.startsAt, 'month') }}</span>
                  <span class="block text-xs text-white/65 first-letter:uppercase">{{ formatDate(event.startsAt, 'weekday') }}</span>
                </span>
              </time>
              <span v-if="event.category" class="shrink-0 rounded-full bg-accent-400 px-3 py-1 text-xs font-semibold text-brand-950">{{ event.category }}</span>
            </div>
          </div>

          <div class="flex flex-1 flex-col p-6 pt-5">
            <h3 class="line-clamp-3 min-h-[3lh] text-lg leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700">
              <NuxtLink :to="localePath(`/events/${event.slug}`)">
                <span class="absolute inset-0" aria-hidden="true" />
                {{ event.title }}
              </NuxtLink>
            </h3>

            <!-- Vaqt va joy: alohida «qutichalar» -->
            <dl class="mt-5 flex flex-wrap gap-2 text-[13px]">
              <div class="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1.5 font-medium text-brand-800">
                <dt class="sr-only">{{ t('events.time') }}</dt>
                <Icon name="lucide:clock" class="size-4 shrink-0 text-brand-500" />
                <dd>{{ formatDate(event.startsAt, 'time') }}<template v-if="event.endsAt"> – {{ formatDate(event.endsAt, 'time') }}</template></dd>
              </div>
              <div class="inline-flex min-w-0 max-w-full items-center gap-1.5 rounded-full bg-accent-100 px-3 py-1.5 font-medium text-accent-600">
                <dt class="sr-only">{{ t('events.place') }}</dt>
                <Icon name="lucide:map-pin" class="size-4 shrink-0" />
                <dd class="truncate" :title="event.location">{{ event.location }}</dd>
              </div>
            </dl>

            <span class="mt-auto flex justify-end pt-5" aria-hidden="true">
              <span class="grid size-10 place-items-center rounded-full border border-brand-200 text-brand-700 transition duration-300 group-hover:-rotate-45 group-hover:border-accent-400 group-hover:bg-accent-400 group-hover:text-ink motion-reduce:transition-none">
                <Icon name="lucide:arrow-right" class="size-4" />
              </span>
            </span>
          </div>
        </article>
      </li>
    </ul>

    <p v-else class="mt-12 rounded-2xl border border-dashed border-line p-10 text-center text-muted">{{ t('events.empty') }}</p>
      </div>
  </section>
</template>

<style scoped>
.events-grid {
  background-image:
    linear-gradient(to right, rgb(56 43 133 / 0.07) 1px, transparent 1px),
    linear-gradient(to bottom, rgb(56 43 133 / 0.07) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(75% 95% at 88% 8%, #000, transparent 75%);
}
</style>
