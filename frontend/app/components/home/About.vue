<script setup lang="ts">
import type { HomeVideoTour, Stat } from '#shared/types/api'

// «Universitet haqida»: raqamlar tasmasi (fakultet, akademik xodim, kafedra, talaba — HEMIS'dan)
// va ikkita karta — universitet haqida va video tur
const props = defineProps<{ stats: Stat[]; videoTour?: HomeVideoTour | null }>()

const { t } = useI18n()
const localePath = useLocalePath()
const playing = ref(false)
// Video kartaning o'zida: bosilganda o'ynaydi, fokus yopish tugmasiga; yopilganda fokus yana «o'ynatish» tugmasiga qaytadi
const closeBtn = ref<HTMLButtonElement>()
const playBtn = ref<HTMLButtonElement>()
const posterOk = ref(true)
const videoReady = ref(false)
async function play() {
  videoReady.value = false
  playing.value = true
  await nextTick()
  closeBtn.value?.focus()
}
async function stop() {
  playing.value = false
  await nextTick()
  playBtn.value?.focus()
}

// «Universitet haqida» kartasi ekranda ko'rinib turganda — davriy yaltirash (main.css: .shine-loop.is-in-view); ekrandan chiqsa to'xtaydi
const aboutCard = ref<HTMLElement>()
const aboutInView = ref(false)
let aboutObserver: IntersectionObserver | undefined
onMounted(() => {
  if (!aboutCard.value || !('IntersectionObserver' in window)) return
  aboutObserver = new IntersectionObserver(([e]) => (aboutInView.value = !!e?.isIntersecting), { threshold: 0.5 })
  aboutObserver.observe(aboutCard.value)
})
onBeforeUnmount(() => aboutObserver?.disconnect())

// Tartib: fakultet → akademik xodim → kafedra → talaba. Ikonkalar ma'nosi original saytdagidek (qalam, kurs, sertifikat, bitiruvchi).
const FACTS = [
  { key: 'faculties', icon: 'lucide:pencil-ruler', tile: 'bg-accent-400 text-brand-950', glow: 'bg-accent-400/25' },
  { key: 'staff', icon: 'lucide:book-open', tile: 'bg-brand-300 text-brand-950', glow: 'bg-brand-300/25' },
  { key: 'departments', icon: 'lucide:award', tile: 'bg-white text-brand-700', glow: 'bg-white/20' },
  { key: 'students', icon: 'lucide:graduation-cap', tile: 'bg-accent-300 text-brand-950', glow: 'bg-accent-300/25' },
] as const

const facts = computed(() => FACTS.flatMap((fact) => {
  const value = props.stats.find(stat => stat.key === fact.key)?.value
  return value === undefined ? [] : [{ ...fact, ...formatStat(value) }]
}))
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :aria-label="t('about.eyebrow')">
    <!-- Raqamlar: bitta qator (telefonda 2×2). Katakchalar ingichka chiziq bilan ajratilgan, hoverda yorishadi -->
    <dl v-if="facts.length" class="grid grid-cols-2 gap-px overflow-hidden rounded-[28px] border border-brand-100 bg-brand-100 shadow-[0_24px_50px_-34px_rgb(56_43_133/0.45)] lg:grid-cols-4">
      <div
        v-for="fact in facts"
        data-reveal-item
        :key="fact.key"
        class="group relative flex items-center gap-4 overflow-hidden bg-white px-5 py-6 transition-colors duration-300 hover:bg-brand-50 sm:gap-5 sm:px-7 sm:py-8"
      >
        <span class="pointer-events-none absolute -top-10 -left-10 size-32 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100" :class="fact.glow" aria-hidden="true" />
        <span class="relative grid size-12 shrink-0 -rotate-6 place-items-center rounded-2xl shadow-[0_12px_24px_-14px_rgb(56_43_133/0.55)] transition-transform duration-300 group-hover:rotate-0 group-hover:scale-110 sm:size-14 motion-reduce:transition-none" :class="fact.tile" aria-hidden="true">
          <Icon :name="fact.icon" class="size-6 sm:size-7" />
        </span>
        <div class="relative flex min-w-0 flex-col-reverse">
          <dt class="text-sm leading-snug text-muted sm:text-[15px]">{{ t(`about.facts.${fact.key}`) }}</dt>
          <dd class="font-display text-4xl leading-none text-brand-800 sm:text-5xl"><CountUp :value="fact.number" /><span class="text-accent-600">{{ fact.suffix }}</span></dd>
        </div>
      </div>
    </dl>

    <div class="mt-8 grid gap-6 lg:auto-rows-[minmax(25rem,auto)] lg:grid-cols-12">
      <!-- Universitet haqida: shisha karta — hover'da ko'tariladi, ustidan yaltiroq nur o'tadi, ortidagi iliq (oltin) va osmon rang yog'du kuchayadi, binafsha yo'q (matn ortida, yopmaydi) -->
      <article ref="aboutCard" data-reveal-item :class="aboutInView && 'is-in-view'" class="shine shine-tint shine-loop group/about relative isolate flex flex-col overflow-hidden rounded-[28px] border border-white/80 bg-[linear-gradient(150deg,rgb(255_255_255/0.96),rgb(250_248_244/0.9)_60%,rgb(246_241_232/0.85))] p-8 shadow-[0_20px_44px_-34px_rgb(19_17_47/0.4),inset_0_1px_0_rgb(255_255_255/0.9)] backdrop-blur-md transition duration-500 hover:-translate-y-1 hover:border-[#e7ddc8] hover:shadow-[0_36px_70px_-38px_rgb(19_17_47/0.5),inset_0_1px_0_rgb(255_255_255/0.9)] sm:p-9 lg:col-span-5 motion-reduce:transition-none motion-reduce:hover:translate-y-0">
        <span class="pointer-events-none absolute -top-20 -right-16 -z-10 size-56 rounded-full bg-[rgb(255_196_110/0.28)] blur-3xl transition duration-700 group-hover/about:scale-125 group-hover/about:bg-[rgb(255_196_110/0.42)]" aria-hidden="true" />
        <span class="pointer-events-none absolute -bottom-24 -left-20 -z-10 size-56 rounded-full bg-[rgb(125_190_255/0.18)] blur-3xl transition duration-700 group-hover/about:scale-125 group-hover/about:bg-[rgb(125_190_255/0.3)]" aria-hidden="true" />
        <h2 class="section-title section-title-plain relative font-display text-4xl leading-[1.1] font-semibold sm:text-[2.6rem]">{{ t('about.title') }}</h2>
        <p class="relative mt-4 text-[17px] leading-relaxed text-muted">{{ t('about.text') }}</p>
        <NuxtLink :to="localePath('/universitet-haqida')" class="group relative mt-6 inline-flex items-center gap-1.5 self-start rounded-full border border-ink/15 bg-white/70 px-4 py-2 font-semibold text-ink backdrop-blur transition hover:border-ink/40 hover:bg-white">
          {{ t('about.link') }}
          <Icon name="lucide:arrow-right" class="size-4 transition-transform group-hover:translate-x-1" />
        </NuxtLink>
      </article>

      <!-- Video tur: admin panelda («Universitet haqida» bo'limi) havola kiritilsa — bosilganda shu kartaning o'zida o'ynaydi
           (alohida oyna ochilmaydi), burchakdagi tugma bilan yopiladi -->
      <div v-if="videoTour" data-reveal-item class="relative min-h-[300px] overflow-hidden rounded-[28px] bg-brand-600 lg:col-span-7">
        <!-- O'ynayotganda: fonda old (muqova) rasm, video uning ustida 16:9 nisbatda markazda. Qora joy yo'q: video yuklanguncha
             o'rnida yaltiraydigan shisha panel; muqova bo'lmasa yoki ochilmasa — shisha fon (kursor kelganda yaltiraydi) -->
        <div v-if="playing" class="video-stage group/stage absolute inset-0 grid place-items-center overflow-hidden">
          <img v-if="videoTour.poster && posterOk" :src="videoTour.poster" alt="" class="absolute inset-0 size-full object-cover" loading="lazy" aria-hidden="true" @error="posterOk = false">
          <span v-else class="glass-bg absolute inset-0" aria-hidden="true" />
          <div class="video-fit glass-frame relative overflow-hidden rounded-2xl bg-white/15 shadow-[0_24px_50px_-24px_rgb(28_21_72/0.55)] ring-1 ring-white/50 backdrop-blur-xl">
            <span v-if="!videoReady" class="glass-sheen absolute inset-0" aria-hidden="true" />
            <video v-if="videoTour.kind === 'file'" :src="videoTour.url" :poster="videoTour.poster || undefined" class="transition-opacity duration-500" :class="videoReady ? 'opacity-100' : 'opacity-0'" controls autoplay playsinline @loadeddata="videoReady = true" />
            <iframe v-else :src="videoTour.url" :title="videoTour.title || t('about.videoTitle')" class="transition-opacity duration-500" :class="videoReady ? 'opacity-100' : 'opacity-0'" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" @load="videoReady = true" />
          </div>
          <button
            ref="closeBtn"
            type="button"
            class="absolute top-3 right-3 grid size-10 place-items-center rounded-full bg-white/25 text-white ring-1 ring-white/50 backdrop-blur-md transition-colors hover:bg-white hover:text-ink"
            :aria-label="t('nav.close')"
            :title="t('nav.close')"
            @click="stop"
          >
            <Icon name="lucide:x" class="size-5" />
          </button>
        </div>
        <button
          v-else
          ref="playBtn"
          type="button"
          class="oz-stripes group relative flex size-full min-h-[300px] flex-col justify-between p-6 text-left text-white transition duration-300 hover:shadow-[0_30px_60px_-30px_var(--color-brand-700)] motion-reduce:transition-none"
          :aria-label="`${t('about.videoLabel')}: ${videoTour.title || t('about.videoTitle')}`"
          @click="play"
        >
          <img v-if="videoTour.poster" :src="videoTour.poster" alt="" class="absolute inset-0 size-full object-cover transition-transform duration-700 group-hover:scale-105 motion-reduce:transition-none" loading="lazy">
          <span class="absolute inset-0 bg-gradient-to-t from-brand-950/85 via-brand-950/25 to-brand-950/30" aria-hidden="true" />
          <span class="relative text-sm text-white/85">{{ t('about.videoLabel') }}</span>
          <span class="relative grid size-[70px] place-self-center place-items-center rounded-full bg-white text-brand-600 shadow-[0_18px_40px_-16px_rgba(17,12,46,0.7)] transition-transform group-hover:scale-110 motion-reduce:transition-none" aria-hidden="true">
            <Icon name="lucide:play" class="ml-0.5 size-6 fill-current" />
          </span>
          <span class="relative">
            <span class="block text-[17px] leading-snug font-semibold">{{ videoTour.title || t('about.videoTitle') }}</span>
            <span v-if="videoTour.text" class="mt-1 line-clamp-2 block text-sm text-white/80">{{ videoTour.text }}</span>
          </span>
        </button>
      </div>
      <!-- Video tur hali kiritilmagan: «Video darsliklar» ga olib bormaydi — admin panelda havola kiritilgach ochiladi -->
      <div v-else data-reveal-item class="oz-stripes relative flex min-h-[300px] flex-col justify-between overflow-hidden rounded-[28px] bg-brand-600 p-6 text-white lg:col-span-7">
        <span class="text-sm text-white/80">{{ t('about.videoLabel') }}</span>
        <span class="grid size-[70px] place-self-center place-items-center rounded-full bg-white/25 text-white" aria-hidden="true">
          <Icon name="lucide:play" class="ml-0.5 size-6 fill-current" />
        </span>
        <span>
          <span class="block text-[17px] leading-snug font-semibold">{{ t('about.videoTitle') }}</span>
          <span class="mt-1 block text-sm text-white/75">{{ t('about.videoSoon') }}</span>
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Video karta ichiga sig'adigan eng katta 16:9 o'lcham (kartaning eni ham, bo'yi ham hisobga olinadi) */
.video-stage { container-type: size; }
/* Video tur roligi keng formatda (~2,12:1; zaxira bilan 2,16) yozilgan, YouTube uni 16:9 pleyerga tepa/pastdan qora polosa bilan joylaydi.
   Ramka tasvir nisbatida, 16:9 pleyer uning markazida — polosalar ramkadan tashqarida qoladi (kesiladi), qora joy ko'rinmaydi.
   Ramka karta ichiga sig'adigan eng katta o'lchamda (eni ham, bo'yi ham hisobga olinadi). */
.video-fit { --ratio: 2.16; aspect-ratio: var(--ratio) / 1; width: min(100%, 100cqh * var(--ratio)); }
.video-fit > iframe, .video-fit > video { position: absolute; left: 0; top: 50%; width: 100%; height: auto; aspect-ratio: 16 / 9; transform: translateY(-50%); }
.video-fit > video { object-fit: cover; }
/* Muqova yo'q / ochilmadi: shisha fon — yumshoq indigo → mint, suzuvchi yog'dular */
.glass-bg {
  background:
    radial-gradient(40% 60% at 15% 20%, rgb(0 252 180 / 0.45), transparent 70%),
    radial-gradient(45% 65% at 85% 80%, rgb(125 108 230 / 0.55), transparent 70%),
    linear-gradient(135deg, #5b4bbe, #7d6ce6 50%, #2fb894);
  background-size: 160% 160%;
  animation: glass-drift 12s ease-in-out infinite alternate;
}
@keyframes glass-drift { to { background-position: 100% 100%; } }
/* Video yuklanguncha shisha panel ustidan nur o'tib turadi */
.glass-sheen {
  background: linear-gradient(110deg, transparent 30%, rgb(255 255 255 / 0.45) 50%, transparent 70%) no-repeat;
  background-size: 250% 100%;
  animation: glass-sweep 1.6s ease-in-out infinite;
}
@keyframes glass-sweep { from { background-position: 130% 0; } to { background-position: -130% 0; } }
/* Kursor kelganda shisha ramka ustidan bir marta nur o'tadi */
.glass-frame::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: linear-gradient(110deg, transparent 35%, rgb(255 255 255 / 0.35) 50%, transparent 65%) no-repeat;
  background-size: 250% 100%;
  background-position: 130% 0;
  transition: background-position 0.9s ease;
}
.group\/stage:hover .glass-frame::after { background-position: -130% 0; }
@media (prefers-reduced-motion: reduce) {
  .glass-bg, .glass-sheen { animation: none; }
  .glass-frame::after { transition: none; }
}
/* Rasmdagi kabi diagonal chiziqlar (surat yoki video muqovasi o'rniga) */
.oz-stripes {
  background-image: repeating-linear-gradient(135deg, rgb(255 255 255 / 0.07) 0 22px, transparent 22px 44px);
}
</style>
