<script setup lang="ts">
// Aloqa / ijtimoiy tarmoq / ilmiy profil plitalari: hover'da biroz ko'tariladi va kattalashadi (oldingi saytdagidek)
defineProps<{ tiles: StaffTile[] }>()

const { t } = useI18n()
</script>

<template>
  <ul class="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
    <li v-for="tile in tiles" :key="tile.key">
      <a
        :href="tile.href"
        :target="tile.external ? '_blank' : undefined"
        :rel="tile.external ? 'noopener' : undefined"
        class="flex items-center gap-3.5 rounded-[18px] border border-line bg-white p-4 text-ink transition duration-200 hover:-translate-y-0.5 hover:scale-[1.02] hover:border-accent-500 hover:shadow-[0_18px_40px_-28px_var(--color-accent-600)]"
      >
        <span class="grid size-11 shrink-0 place-items-center rounded-xl text-white" :class="tile.tile"><Icon :name="tile.icon" class="size-5" /></span>
        <span class="min-w-0 flex-1">
          <span class="block font-bold">{{ tile.label }}</span>
          <span class="mt-0.5 block truncate text-sm text-muted">{{ tile.sub }}</span>
        </span>
        <Icon name="lucide:arrow-up-right" class="size-[18px] shrink-0 text-muted" />
        <span v-if="tile.external" class="sr-only">({{ t('staff.profile.newTab') }})</span>
      </a>
    </li>
  </ul>
</template>
