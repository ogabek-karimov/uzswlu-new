// Ovozli o'qish — brauzerning o'zidagi Web Speech API (bepul: kalit, obuna yoki server kerak emas).
// Ovozlar brauzer va tizimga bog'liq: o'zbekcha ovoz bo'lmasa, o'qilishi yaqin tildagi ovoz tanlanadi.

const PREFER: Record<string, string[]> = {
  uz: ['uz', 'tr', 'ru'],
  ru: ['ru'],
  en: ['en'],
  zh: ['zh'],
}

// Uzun matnni bo'laklab o'qiymiz: ba'zi brauzerlar uzun gapni o'rtasida to'xtatib qo'yadi
function chunks(text: string, max = 220) {
  const parts = text.replace(/\s+/g, ' ').trim().split(/(?<=[.!?。！？;:])\s+/)
  const out: string[] = []
  for (const part of parts) {
    if (part.length <= max) {
      out.push(part)
      continue
    }
    let rest = part
    while (rest.length > max) {
      const cut = rest.lastIndexOf(' ', max)
      out.push(rest.slice(0, cut > 40 ? cut : max))
      rest = rest.slice(cut > 40 ? cut + 1 : max)
    }
    if (rest) out.push(rest)
  }
  return out.filter(Boolean)
}

let listening = false

function pickVoice(lang: string) {
  const voices = window.speechSynthesis.getVoices()
  for (const code of PREFER[lang] ?? [lang]) {
    const found = voices.find(v => v.lang.toLowerCase().startsWith(code))
    if (found) return { voice: found, exact: code === lang }
  }
  return { voice: null, exact: false }
}

export function useSpeech() {
  const supported = import.meta.client && 'speechSynthesis' in window
  const speaking = useState('speech-speaking', () => false)
  /** Ovoz ishga tushmasa (qurilmada ovoz dvigateli yo'q va h.k.) — panelda xabar chiqadi */
  const failed = useState('speech-failed', () => false)
  const voicesReady = useState('speech-voices', () => 0)

  if (supported && !listening) {
    // Ovozlar ro'yxati kech yuklanadi
    listening = true
    const update = () => (voicesReady.value = window.speechSynthesis.getVoices().length)
    update()
    window.speechSynthesis.addEventListener?.('voiceschanged', update)
  }

  function stop() {
    if (!supported) return
    window.speechSynthesis.cancel()
    speaking.value = false
  }

  function speak(text: string, lang: string) {
    if (!supported || !text.trim()) return
    window.speechSynthesis.cancel()
    failed.value = false
    const { voice } = pickVoice(lang)
    const list = chunks(text)
    list.forEach((part, i) => {
      const u = new SpeechSynthesisUtterance(part)
      if (voice) {
        u.voice = voice
        u.lang = voice.lang
      }
      else {
        u.lang = lang
      }
      u.rate = 0.95
      if (i === 0) u.onstart = () => (speaking.value = true)
      if (i === list.length - 1) u.onend = () => (speaking.value = false)
      u.onerror = (event) => {
        speaking.value = false
        if (event.error !== 'canceled' && event.error !== 'interrupted') failed.value = true
      }
      window.speechSynthesis.speak(u)
    })
    speaking.value = true
  }

  /** Shu til uchun aynan o'z ovozi bormi (o'zbekcha uchun ko'pincha yo'q) */
  const hasExactVoice = (lang: string) => {
    void voicesReady.value
    return supported ? pickVoice(lang).exact : false
  }

  return { supported, speaking, failed, speak, stop, hasExactVoice }
}
