// Maxsus imkoniyatlar ("Ko'rinish" paneli): shrift o'lchami, rang rejimi, ovozli o'qish.
// Hech narsa saqlanmaydi: saytga har kirishda hammasi standart holatda, foydalanuvchi o'zi tanlaydi
// (sahifadan sahifaga o'tganda tanlov saqlanib turadi, sahifa qayta yuklansa — standartga qaytadi).
const STEPS = [90, 100, 110, 120, 130, 140, 150]
const DEFAULT_STEP = 1
// Oldingi versiyalar brauzerda saqlagan kalitlar — kirishda o'chiriladi
const STORAGE_KEY = 'uzswlu:a11y:v2'
const OLD_KEY = 'uzswlu:a11y'

/** Rang rejimlari — eski saytdagi 5 ta variant (dark — "Kontrast" tugmasi ham shuni yoqadi) */
export const A11Y_SCHEMES = ['default', 'dark', 'blue', 'sepia', 'green'] as const
export type A11yScheme = (typeof A11Y_SCHEMES)[number]

export function useA11y() {
  const step = useState('a11y-step', () => DEFAULT_STEP)
  const scheme = useState<A11yScheme>('a11y-scheme', () => 'default')
  const voice = useState('a11y-voice', () => false)

  function apply() {
    if (import.meta.server) return
    const root = document.documentElement
    root.style.fontSize = step.value === DEFAULT_STEP ? '' : `${STEPS[step.value]}%`
    if (scheme.value === 'default') delete root.dataset.scheme
    else root.dataset.scheme = scheme.value
  }

  /** Saytga kirganda: hammasi standart holatda; oldingi versiyalar brauzerda saqlagan tanlov o'chiriladi */
  function restore() {
    step.value = DEFAULT_STEP
    scheme.value = 'default'
    voice.value = false
    try {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(OLD_KEY)
    }
    catch {}
    apply()
  }

  const update = (fn: () => void) => () => {
    fn()
    apply()
  }

  return {
    step,
    scheme,
    voice,
    percent: computed(() => STEPS[step.value]!),
    canDecrease: computed(() => step.value > 0),
    canIncrease: computed(() => step.value < STEPS.length - 1),
    contrast: computed(() => scheme.value === 'dark'),
    restore,
    increase: update(() => {
      if (step.value < STEPS.length - 1) step.value++
    }),
    decrease: update(() => {
      if (step.value > 0) step.value--
    }),
    toggleContrast: update(() => {
      scheme.value = scheme.value === 'dark' ? 'default' : 'dark'
    }),
    setScheme: (value: A11yScheme) => {
      scheme.value = value
      apply()
    },
    toggleVoice: update(() => {
      voice.value = !voice.value
    }),
    /** Shrift va rangni boshlang'ich holatga qaytarish (ovoz o'zgarmaydi) */
    reset: update(() => {
      step.value = DEFAULT_STEP
      scheme.value = 'default'
    }),
  }
}
