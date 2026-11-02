<script setup lang="ts">
// Xodim surati (oldingi saytdagi qoida): xodimning o'z surati → ochilmasa HEMIS surati → ikkalasi ham bo'lmasa bosh harflar.
// decorative: ism yonida yozilgan joylarda (kartalar) ekran o'quvchi takrorlamasligi uchun
const props = defineProps<{ id: string; name: string; photo?: string | null; fallback?: string | null; decorative?: boolean }>()

const { t } = useI18n()
const step = ref(0)
watch(() => [props.photo, props.fallback], () => { step.value = 0 })
const src = computed(() => [props.photo, props.fallback].filter(Boolean)[step.value] ?? null)
const label = computed(() => (props.decorative ? undefined : t('staff.profile.photo', { name: props.name })))
</script>

<template>
  <img
    v-if="src"
    :src="src"
    :alt="label ?? ''"
    loading="lazy"
    class="object-cover"
    @error="step++"
  >
  <span
    v-else
    :role="label ? 'img' : undefined"
    :aria-label="label"
    :aria-hidden="label ? undefined : 'true'"
    class="grid place-items-center font-display font-semibold"
    :class="avatarTint(id)"
  >
    {{ initials(name) }}
  </span>
</template>
