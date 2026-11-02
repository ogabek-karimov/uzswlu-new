<script setup lang="ts">
import type { MenuLink } from '#shared/types/api'

const props = defineProps<{ links: MenuLink[]; compact?: boolean }>()

const goals = computed(() => props.links.filter(l => l.sdg))
const extras = computed(() => props.links.filter(l => !l.sdg))
</script>

<template>
  <div>
    <!-- 17 ta maqsad — BMT rasmiy ranglarida -->
    <ul data-a11y-keep class="grid gap-2" :class="compact ? 'grid-cols-6' : 'grid-cols-6 xl:grid-cols-9'">
      <li v-for="goal in goals" :key="goal.url">
        <NavMenuLink
          :link="goal"
          class="group/sdg block h-full overflow-hidden rounded-xl bg-white ring-1 ring-line transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_14px_30px_-16px_rgba(19,17,47,0.45)] hover:ring-transparent"
          :title="`${goal.sdg}. ${goal.title}`"
        >
          <span
            class="flex items-center justify-between px-2.5 font-display font-semibold"
            :class="compact ? 'h-9 text-lg' : 'h-12 text-2xl'"
            :style="{ background: sdgColor(goal.sdg!), color: sdgInk(goal.sdg!) }"
          >
            {{ goal.sdg }}
            <Icon name="lucide:arrow-up-right" class="size-3.5 opacity-0 transition-opacity group-hover/sdg:opacity-100" />
          </span>
          <span v-if="!compact" class="line-clamp-3 block px-2.5 py-2 text-[11.5px] leading-snug font-medium text-ink">{{ goal.title }}</span>
          <span v-else class="sr-only">{{ goal.title }}</span>
        </NavMenuLink>
      </li>
    </ul>

    <!-- Qo'shimcha sahifalar (GreenMetric, hisobot va h.k.) -->
    <ul v-if="extras.length" class="mt-4 flex flex-wrap gap-2">
      <li v-for="link in extras" :key="link.url">
        <NavMenuLink
          :link="link"
          class="inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-3.5 py-2 text-sm font-medium text-ink transition-colors hover:border-brand-300 hover:bg-brand-50"
        >
          <Icon name="lucide:leaf" class="size-3.5 text-emerald-600" />
          {{ link.title }}
        </NavMenuLink>
      </li>
    </ul>
  </div>
</template>
