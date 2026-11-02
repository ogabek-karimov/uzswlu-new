<script setup lang="ts">
import { A11Y_SCHEMES } from '~/composables/useA11y'

// "Ko'rinish" paneli (canvas: "Komponent — Ko'rinish paneli"): shrift, rang rejimi, ovozli o'qish
const emit = defineEmits<{ close: [] }>()

const { t, locale } = useI18n()
const a11y = useA11y()
const speech = useSpeech()

// Namuna kataklar ranglari (rejimning o'zi CSS'da: main.css → html[data-scheme])
const SWATCH: Record<string, string> = {
  default: 'border-[#c9c5d6] bg-white text-ink',
  dark: 'border-black bg-black text-white',
  blue: 'border-[#7da7de] bg-[#dcebfa] text-[#0b2e6b]',
  sepia: 'border-[#c9b48e] bg-[#f3e9d2] text-[#3d2b1f]',
  green: 'border-black bg-black text-[#a3ff3d]',
}

const noUzVoice = computed(() => speech.supported && locale.value === 'uz' && !speech.hasExactVoice('uz'))

function readPage() {
  const text = document.querySelector('main')?.innerText ?? ''
  speech.speak(text, locale.value)
}

function toggleVoice() {
  a11y.toggleVoice()
  if (!a11y.voice.value) speech.stop()
  else trackEvent('Ovoz bilan öqiş yoqildi')
}
</script>

<template>
  <section
    role="dialog"
    :aria-label="t('a11y.title')"
    data-a11y-panel
    class="max-h-[calc(100dvh-9rem)] w-[340px] max-w-[calc(100vw-24px)] overflow-y-auto overscroll-contain rounded-3xl border border-line bg-white px-5 py-4 text-left text-ink shadow-[0_30px_60px_-30px_rgba(19,17,47,0.45)]"
  >
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-bold">{{ t('a11y.title') }}</h2>
      <button type="button" :aria-label="t('nav.close')" class="grid size-8 place-items-center rounded-full text-muted transition-colors hover:bg-brand-50 hover:text-ink" @click="emit('close')">
        <Icon name="lucide:x" class="size-5" />
      </button>
    </div>

    <!-- Shrift -->
    <p class="mt-3.5 text-[11px] font-bold tracking-[0.14em] text-muted uppercase">{{ t('a11y.font') }}</p>
    <div class="mt-2 flex items-center justify-between gap-2.5">
      <button type="button" :disabled="!a11y.canDecrease.value" :aria-label="`${t('topbar.fontSize')}: ${t('topbar.decrease')}`" class="h-11 w-16 rounded-xl border-2 border-line bg-white text-base font-bold transition-colors hover:bg-brand-50 disabled:opacity-35" @click="a11y.decrease">A−</button>
      <span class="text-lg font-bold" aria-live="polite">{{ a11y.percent.value }}%</span>
      <button type="button" :disabled="!a11y.canIncrease.value" :aria-label="`${t('topbar.fontSize')}: ${t('topbar.increase')}`" class="h-11 w-16 rounded-xl border-2 border-line bg-white text-xl font-bold transition-colors hover:bg-brand-50 disabled:opacity-35" @click="a11y.increase">A+</button>
    </div>
    <button type="button" class="mt-1.5 py-1 text-[13px] font-semibold text-accent-600 underline underline-offset-4" @click="a11y.reset">{{ t('a11y.reset') }}</button>

    <!-- Rang -->
    <p class="mt-3.5 text-[11px] font-bold tracking-[0.14em] text-muted uppercase">{{ t('a11y.color') }}</p>
    <div role="radiogroup" :aria-label="t('a11y.color')" class="mt-2 grid grid-cols-5 gap-2" data-a11y-keep>
      <button
        v-for="s in A11Y_SCHEMES"
        :key="s"
        type="button"
        role="radio"
        :aria-checked="a11y.scheme.value === s"
        :aria-label="t(`a11y.schemes.${s}`)"
        :title="t(`a11y.schemes.${s}`)"
        class="h-11 rounded-xl border-2 text-lg font-extrabold transition-transform hover:-translate-y-0.5"
        :class="[SWATCH[s], a11y.scheme.value === s && 'ring-2 ring-accent-600 ring-offset-2']"
        @click="a11y.setScheme(s)"
      >
        A
      </button>
    </div>
    <p class="mt-1.5 text-xs text-muted">{{ t(`a11y.schemes.${a11y.scheme.value}`) }}</p>

    <!-- Ovoz -->
    <p class="mt-3.5 text-[11px] font-bold tracking-[0.14em] text-muted uppercase">{{ t('a11y.voice') }}</p>
    <template v-if="speech.supported">
      <div class="mt-2 flex flex-wrap items-center gap-2">
        <button
          type="button"
          :aria-pressed="a11y.voice.value"
          class="flex h-10 items-center gap-1.5 rounded-xl border-2 px-3 text-[13px] font-bold transition-colors"
          :class="a11y.voice.value ? 'border-brand-800 bg-brand-800 text-white' : 'border-line bg-white text-ink hover:bg-brand-50'"
          @click="toggleVoice"
        >
          <Icon :name="a11y.voice.value ? 'lucide:volume-2' : 'lucide:volume-x'" class="size-[18px]" />
          {{ a11y.voice.value ? t('a11y.voiceOn') : t('a11y.voiceOff') }}
        </button>
        <template v-if="a11y.voice.value">
          <button v-if="!speech.speaking.value" type="button" class="flex h-10 items-center gap-1.5 rounded-xl border-2 border-line bg-white px-3 text-[13px] font-bold transition-colors hover:bg-brand-50" @click="readPage">
            <Icon name="lucide:play" class="size-4" />
            {{ t('a11y.readPage') }}
          </button>
          <button v-else type="button" class="flex h-10 items-center gap-1.5 rounded-xl border-2 border-line bg-white px-3 text-[13px] font-bold transition-colors hover:bg-brand-50" @click="speech.stop">
            <Icon name="lucide:square" class="size-4" />
            {{ t('a11y.stop') }}
          </button>
        </template>
      </div>
      <p class="mt-2 text-xs leading-normal text-muted">{{ a11y.voice.value ? t('a11y.hintOn') : t('a11y.hintOff') }}</p>
      <p v-if="a11y.voice.value && noUzVoice" class="mt-2 rounded-xl bg-brand-50 px-3 py-2 text-xs leading-normal text-brand-800">{{ t('a11y.noUz') }}</p>
      <p v-if="a11y.voice.value && speech.failed.value" role="alert" class="mt-2 rounded-xl bg-red-50 px-3 py-2 text-xs leading-normal text-red-700">{{ t('a11y.failed') }}</p>
    </template>
    <p v-else class="mt-2 text-xs text-muted">{{ t('a11y.unsupported') }}</p>
  </section>
</template>
