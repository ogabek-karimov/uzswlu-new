<script setup lang="ts">
// Raqam ko'rinish maydoniga kirganda 0 dan o'sib chiqadi (ease-out). SSR/JS'siz — oxirgi qiymat ko'rinadi;
// prefers-reduced-motion yoki ekranda bo'lmasa animatsiyasiz. `value` — tayyor satr ("1100", "17").
const props = defineProps<{ value: string }>()
const shown = ref(props.value)
const el = ref<HTMLElement>()

onMounted(() => {
  const target = Number(props.value.replace(/\D/g, ''))
  if (!target || matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return
  shown.value = '0'
  const io = new IntersectionObserver(([entry]) => {
    if (!entry?.isIntersecting) return
    io.disconnect()
    const start = performance.now()
    const dur = 1600
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / dur)
      shown.value = String(Math.round(target * (1 - Math.pow(1 - p, 3))))
      if (p < 1) requestAnimationFrame(tick)
      else shown.value = props.value
    }
    requestAnimationFrame(tick)
  }, { threshold: 0.4 })
  io.observe(el.value!)
  onBeforeUnmount(() => io.disconnect())
})
</script>

<template>
  <span ref="el" class="tabular-nums">{{ shown }}</span>
</template>
