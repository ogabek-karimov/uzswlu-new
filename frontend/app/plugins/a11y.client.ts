// Maxsus imkoniyatlar: saqlangan tanlovni tiklash va ovoz rejimida matnni o'qish:
// kursor ustidagi matn (0,3 soniya tursa), telefonda bosilgan matn, belgilangan matn va Tab bilan tanlangan havola/tugma.
export default defineNuxtPlugin((nuxtApp) => {
  const a11y = useA11y()
  const speech = useSpeech()
  const lang = () => document.documentElement.lang.slice(0, 2) || 'uz'

  nuxtApp.hook('app:mounted', () => a11y.restore())

  // Sahifa almashsa — o'qish to'xtaydi
  nuxtApp.hook('page:start', () => {
    speech.stop()
    mark(null)
  })

  // O'qilayotgan element ajratib ko'rsatiladi (main.css: [data-speaking])
  let current: HTMLElement | null = null
  function mark(el: HTMLElement | null) {
    current?.removeAttribute('data-speaking')
    current = el
    el?.setAttribute('data-speaking', '')
  }
  watch(speech.speaking, (on) => {
    if (!on) mark(null)
  })
  watch(a11y.voice, (on) => {
    if (!on) mark(null)
  })

  function say(text: string, el: HTMLElement | null) {
    const clean = text.replace(/\s+/g, ' ').trim()
    if (clean.length < 2) return
    speech.speak(clean, lang())
    mark(el)
  }

  // Kursor turgan "o'qiladigan" eng kichik blok: paragraf, sarlavha, ro'yxat bandi, havola, tugma, jadval katagi …
  const BLOCK = 'a, button, label, summary, h1, h2, h3, h4, h5, h6, p, li, dt, dd, td, th, figcaption, blockquote, caption, legend, [role="button"], [role="link"], [role="tab"], [data-speak]'
  const SKIP = 'input, textarea, select, option, [contenteditable="true"], [data-a11y-panel], [aria-hidden="true"]'

  const ACTION = 'a, button, label, summary, [role="button"], [role="link"], [role="tab"]'
  const ownText = (el: Element) => [...el.childNodes].some(n => n.nodeType === Node.TEXT_NODE && n.textContent!.trim().length > 1)

  function readable(target: EventTarget | null): { el: HTMLElement; text: string } | null {
    let node = target instanceof Element ? target : null
    // Bezak belgilar (aria-hidden ikonka) ustida — ularni o'rab turgan element olinadi
    while (node?.closest('[aria-hidden="true"]')) node = node.closest('[aria-hidden="true"]')!.parentElement
    if (!(node instanceof HTMLElement) || node.closest(SKIP)) return null
    // Rasm — tavsifi (alt) o'qiladi
    if (node instanceof HTMLImageElement && node.alt.trim()) return { el: node, text: node.alt }
    const block = node.closest<HTMLElement>(BLOCK)
    // Havola/tugma — butunligicha; boshqa joyda — kursor turgan matn bo'lagi (span, div) yoki uni o'ragan blok
    const el = block?.matches(ACTION) ? block : ownText(node) ? node : block
    if (!el || el === document.body || el.tagName === 'MAIN') return null
    // Faqat belgidan iborat tugma/havola — aria-label yoki title
    // CSS bilan katta harfga o'tkazilgan matn ("UNIVERSITET") harfma-harf o'qilmasin — asl yozilishi olinadi
    const visible = getComputedStyle(el).textTransform === 'uppercase' ? el.textContent ?? '' : el.innerText
    const text = (el.getAttribute('aria-label') || visible || el.getAttribute('title') || el.querySelector('img')?.alt || '').slice(0, 1500)
    return text.trim() ? { el, text } : null
  }

  // Sichqoncha: kursor 0,3 soniya bir joyda tursa o'qiydi (sahifa bo'ylab yurganda hammasini o'qib ketmasligi uchun)
  let timer: ReturnType<typeof setTimeout> | undefined
  document.addEventListener('mouseover', (event) => {
    if (!a11y.voice.value) return
    clearTimeout(timer)
    const found = readable(event.target)
    if (!found || (found.el === current && speech.speaking.value)) return
    timer = setTimeout(() => {
      // Matn belgilanayotgan bo'lsa — belgilangan qism o'qiladi (pastda)
      if (window.getSelection()?.toString().trim()) return
      say(found.text, found.el)
    }, 300)
  })
  document.addEventListener('mouseout', () => clearTimeout(timer))

  // Telefon (sensor ekran): matnga bosilganda o'qiladi; havola va tugmalar odatdagidek ishlaydi
  document.addEventListener('pointerup', (event) => {
    if (!a11y.voice.value || event.pointerType !== 'touch') return
    const target = event.target as HTMLElement | null
    if (target?.closest('a, button, [role="button"], [role="link"], [role="tab"]')) return
    const found = readable(target)
    if (found) say(found.text, found.el)
  })

  // Klaviatura: Tab bilan tanlangan havola/tugma o'qiladi
  document.addEventListener('focusin', (event) => {
    if (!a11y.voice.value) return
    const target = event.target as HTMLElement | null
    if (!target?.matches?.(':focus-visible')) return
    const found = readable(target)
    if (found) say(found.text, found.el)
  })

  // Belgilangan matn (sichqoncha yoki Shift+strelka) — shu qism o'qiladi
  function readSelection(event: Event) {
    if (!a11y.voice.value) return
    const target = event.target as HTMLElement | null
    if (target?.closest('input, textarea, select, [data-a11y-panel]')) return
    const text = window.getSelection()?.toString().trim() ?? ''
    if (text.length < 2) return
    clearTimeout(timer)
    say(text, null)
  }

  document.addEventListener('mouseup', readSelection)
  document.addEventListener('keyup', (event) => {
    if (event.shiftKey) readSelection(event)
  })
})
