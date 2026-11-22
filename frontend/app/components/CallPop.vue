<script setup lang="ts">
// Pastki chap burchakdagi qo'ng'iroq tugmasi — faqat sayt ochilganda/yangilanganda (layout bir marta o'rnatiladi, SPA o'tishda qaytmaydi):
// 1) «tabletka»: trubka + «Biz bilan boğlaniş» → 2) trubka 2 marta silkinadi → 3) chapga yig'ilib dumaloqqa aylanadi →
// 4) yana 2 marta silkinadi → 5) yo'qoladi. Ko'ringan vaqt davomida trubka atrofidan 3 qatorli yashil to'lqin tarqaladi. Bosilsa — ishonch telefoniga qo'ng'iroq (admin → Sozlamalar dagi raqam).
const { t } = useI18n()
const { data: site } = await useSiteData()
const phone = computed(() => site.value?.phone || '+998 71 230 13 73')
const href = computed(() => `tel:${phone.value.replace(/[^\d+]/g, '')}`)

type Phase = 'off' | 'hidden' | 'pill' | 'circle' | 'gone'
const phase = ref<Phase>('off')
const ringing = ref(false)
const timers: ReturnType<typeof setTimeout>[] = []
const at = (ms: number, fn: () => void) => timers.push(setTimeout(fn, ms))

onMounted(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduced) {
    phase.value = 'hidden'
    at(400, () => (phase.value = 'pill'))
    at(4000, () => (phase.value = 'gone'))
    at(4500, () => (phase.value = 'off'))
    return
  }
  phase.value = 'hidden'                     // avval yashirin holda chiziladi — keyin silliq paydo bo'ladi
  at(500, () => (phase.value = 'pill'))
  at(1100, () => (ringing.value = true))     // 2 marta silkinish (0,9 s)
  at(2000, () => (ringing.value = false))
  at(2500, () => (phase.value = 'circle'))   // chapga yig'iladi
  at(3200, () => (ringing.value = true))     // yana 2 marta
  at(4100, () => (ringing.value = false))
  at(4600, () => (phase.value = 'gone'))     // yo'qoladi
  at(5200, () => (phase.value = 'off'))      // DOM'dan olib tashlanadi
})
onBeforeUnmount(() => timers.forEach(clearTimeout))
</script>

<template>
  <!-- Tashqi o'ram: joylashuv va to'lqinlar (tugma o'zi yig'ilganda chetini kesadi — to'lqinlar undan tashqarida) -->
  <div v-if="phase !== 'off'" class="fixed bottom-5 left-5 z-40 print:hidden">
    <!-- 3 qatorli yashil to'lqin: trubka doirasi markazidan tashqariga, navbat bilan -->
    <span v-if="phase === 'pill' || phase === 'circle'" class="pointer-events-none absolute bottom-0 left-0 grid size-14 place-items-center" aria-hidden="true">
      <span v-for="i in 3" :key="i" class="call-wave" :style="{ animationDelay: `${(i - 1) * 0.55}s` }" />
    </span>
    <a
      :href="href"
      :aria-label="`${t('callPop.label')}: ${phone}`"
      class="call-pop relative flex h-14 items-center overflow-hidden rounded-full border border-white/70 bg-white/85 text-ink shadow-[0_18px_40px_-18px_rgb(19_17_47/0.55)] backdrop-blur-md"
      :class="[`is-${phase}`]"
    >
      <span class="grid size-14 shrink-0 place-items-center">
        <span class="grid size-11 place-items-center rounded-full bg-accent-400 text-ink shadow-[0_6px_16px_-6px_rgb(0_160_120/0.7)]">
          <Icon name="lucide:phone" class="text-[22px]" :class="ringing && 'call-ring'" />
        </span>
      </span>
      <span class="call-label whitespace-nowrap pr-6 text-[15px] font-semibold">{{ t('callPop.label') }}</span>
    </a>
  </div>
</template>

<style scoped>
/* Kenglik: tabletka (yozuv bilan) → dumaloq (faqat trubka); ko'rinish/yo'qolish — shaffoflik va masshtab */
.call-pop {
  max-width: 20rem;
  opacity: 0;
  transform: translateY(12px) scale(0.92);
  transform-origin: left center;
  transition: max-width 0.6s cubic-bezier(0.65, 0, 0.35, 1), opacity 0.4s, transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}
.call-pop.is-pill,
.call-pop.is-circle {
  opacity: 1;
  transform: none;
}
.call-pop.is-circle {
  max-width: 3.5rem;
}
.call-pop.is-gone {
  max-width: 3.5rem;
  opacity: 0;
  transform: scale(0.6);
  pointer-events: none;
}
.call-label {
  transition: opacity 0.3s;
}
.call-pop.is-circle .call-label,
.call-pop.is-gone .call-label {
  opacity: 0;
}
/* Yashil to'lqin: doira (44 px) kattalashib, xiralashib yo'qoladi; 3 tasi navbat bilan */
.call-wave {
  position: absolute;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 999px;
  border: 2px solid rgb(0 220 160 / 0.7);
  background: rgb(0 252 180 / 0.18);
  animation: call-wave 1.65s cubic-bezier(0.2, 0.6, 0.35, 1) infinite;
}
@keyframes call-wave {
  0% { transform: scale(1); opacity: 0.9; }
  100% { transform: scale(2.6); opacity: 0; }
}
/* Trubka silkinishi: 2 marta (har biri 0,45 s) */
.call-ring {
  animation: call-ring 0.45s ease-in-out 2;
  transform-origin: 50% 60%;
}
@keyframes call-ring {
  0%, 100% { transform: rotate(0); }
  20% { transform: rotate(-18deg); }
  40% { transform: rotate(16deg); }
  60% { transform: rotate(-12deg); }
  80% { transform: rotate(8deg); }
}
@media (prefers-reduced-motion: reduce) {
  .call-pop { transition: opacity 0.3s; }
  .call-ring, .call-wave { animation: none; display: none; }
}
</style>
