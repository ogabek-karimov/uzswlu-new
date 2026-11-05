<script setup lang="ts">
import type { PostTranslation, PostType } from '#shared/types/api'

// Telegram'da ulashish (canvas: "Komponent — Telegram'da ulaşiş"): o'zbekcha surat, ostida post bor barcha tillardagi havolalar.
// Telefonda — ulashish oynasi: surat fayl bo'lib boradi, havolalar uning ostida.
// Kompyuterda brauzer Telegram'ga faylni o'zi bera olmaydi — oyna: havolalarni, keyin suratni nusxalab Telegram'ga qo'yish
// (xabar maydonidagi matn surat ostiga tushadi). JS ishlamasa — oddiy t.me havolasi
const props = defineProps<{ type: PostType; slug: string; translations?: PostTranslation[]; image?: string | null }>()

const { t, locale } = useI18n()
const origin = useRequestURL().origin

const links = computed(() => {
  const langs = props.translations?.length ? props.translations.map(item => item.lang) : [normalizeLocale(locale.value)]
  return LOCALES.filter(code => langs.includes(code))
    .map(lang => ({ lang, url: `${origin}${lang === 'uz' ? '' : `/${lang}`}/${props.type}/${props.slug}` }))
})
const text = computed(() => links.value.map(link => link.url).join('\n\n'))
const href = computed(() => {
  const [first, ...rest] = links.value
  const extra = rest.length ? `&text=${encodeURIComponent(`\n${rest.map(link => link.url).join('\n\n')}`)}` : ''
  return `https://t.me/share/url?url=${encodeURIComponent(first?.url ?? '')}${extra}`
})
// O'zbekcha surat (o'zbekchasi bo'lmasa — shu sahifaniki)
const image = computed(() => props.translations?.find(item => item.lang === 'uz')?.image ?? props.image ?? null)

// Suratni kerakli formatga o'tkazish: telefonda JPEG (WebP Telegram'da stiker bo'lib ketmasin), buferga — PNG
async function render(type: 'image/jpeg' | 'image/png'): Promise<Blob> {
  if (!image.value) throw new Error('no image')
  const blob = await fetch(new URL(image.value, location.origin), { mode: 'cors' }).then(res => (res.ok ? res.blob() : Promise.reject(new Error(String(res.status)))))
  const bitmap = await createImageBitmap(blob)
  const canvas = document.createElement('canvas')
  canvas.width = bitmap.width
  canvas.height = bitmap.height
  canvas.getContext('2d')?.drawImage(bitmap, 0, 0)
  return new Promise((resolve, reject) => canvas.toBlob(out => (out ? resolve(out) : reject(new Error('encode'))), type, 0.92))
}

// Telefonda fayl oldindan tayyorlanadi: ulashish bosilgan zahoti chaqirilishi shart (brauzer talabi)
const touch = ref(false)
let file: File | null = null
onMounted(async () => {
  touch.value = matchMedia('(pointer: coarse)').matches
  if (!touch.value || !image.value || !navigator.canShare) return
  try {
    const candidate = new File([await render('image/jpeg')], `${props.slug}.jpg`, { type: 'image/jpeg' })
    if (navigator.canShare({ files: [candidate] })) file = candidate
  }
  catch { /* t.me havolasi ishlaydi */ }
})

const open = ref(false)
function onClick(event: MouseEvent) {
  if (file) {
    event.preventDefault()
    navigator.share({ files: [file], text: text.value }).catch((error: DOMException) => {
      if (error.name !== 'AbortError') location.href = href.value
    })
    return
  }
  if (touch.value) return
  event.preventDefault()
  open.value = true
}

// Kompyuter: 1) havolalar → xabar maydoniga, 2) surat → yana qo'yiladi
const pasteKey = ref('Ctrl+V')
onMounted(() => {
  if (/Mac|iPhone|iPad/.test(navigator.userAgent)) pasteKey.value = '⌘V'
})
const step = ref(0)
const failed = ref(false)
watch(open, (value) => {
  if (value) {
    step.value = 0
    failed.value = false
  }
})
async function copyLinks() {
  await navigator.clipboard.writeText(text.value)
  step.value = Math.max(step.value, 1)
}
async function copyImage() {
  failed.value = false
  try {
    // Promise to'g'ridan-to'g'ri beriladi: Safari bosilgan zahotdagi ruxsatni yo'qotmaydi
    await navigator.clipboard.write([new ClipboardItem({ 'image/png': render('image/png') })])
    step.value = 2
  }
  catch {
    failed.value = true
  }
}
</script>

<template>
  <a :href="href" target="_blank" rel="noopener" :aria-label="t('posts.shareTelegram')" :title="t('posts.shareTelegram')" class="grid size-10 place-items-center rounded-full border border-line bg-white text-ink transition-colors hover:border-accent-500" @click="onClick">
    <Icon name="simple-icons:telegram" class="size-4" />
  </a>

  <AppDialog v-model:open="open" :title="t('posts.tg.title')" class="max-w-[480px] text-left" body-class="p-6">
    <!-- Xabar ko'rinishi: Telegram'da shunday boradi (surat ramkadan chiqmaydi, ostida yuboriladigan havolalar) -->
    <p class="mt-4 text-[13px] text-muted">{{ t('posts.tg.preview') }}</p>
    <div class="mt-2 overflow-hidden rounded-[18px] border border-line bg-paper">
      <div v-if="image" class="bg-brand-50">
        <img :src="image" alt="" class="mx-auto block h-[220px] w-auto max-w-full object-contain">
      </div>
      <ul class="px-3.5 py-3">
        <li v-for="link in links" :key="link.lang" class="flex items-baseline gap-2.5 py-0.5">
          <span class="w-6 shrink-0 text-[11px] font-bold text-muted uppercase">{{ link.lang }}</span>
          <span class="min-w-0 truncate text-[13px] text-brand-700">{{ link.url }}</span>
        </li>
      </ul>
    </div>

    <ol class="mt-5 grid gap-3.5">
      <li class="flex gap-3">
        <span class="grid size-[26px] shrink-0 place-items-center rounded-full text-[13px] font-bold text-white" :class="step >= 1 ? 'bg-accent-600' : 'bg-brand-800'">
          <Icon v-if="step >= 1" name="lucide:check" class="size-3.5" />
          <template v-else>1</template>
        </span>
        <div class="min-w-0 flex-1">
          <button
            type="button"
            class="inline-flex h-11 items-center gap-2 rounded-[14px] px-[18px] text-sm font-semibold transition-colors"
            :class="step >= 1 ? 'border border-line bg-white text-accent-600' : 'bg-ink text-white hover:bg-brand-800'"
            @click="copyLinks"
          >
            <Icon v-if="step >= 1" name="lucide:check" class="size-4" />
            {{ step >= 1 ? t('posts.tg.copied') : t('posts.tg.copyLinks') }}
          </button>
          <p class="mt-1.5 text-[13px] leading-normal text-muted">{{ t('posts.tg.step1', { key: pasteKey }) }}</p>
        </div>
      </li>
      <li v-if="image" class="flex gap-3">
        <span class="grid size-[26px] shrink-0 place-items-center rounded-full text-[13px] font-bold text-white" :class="step >= 2 ? 'bg-accent-600' : 'bg-brand-800'">
          <Icon v-if="step >= 2" name="lucide:check" class="size-3.5" />
          <template v-else>2</template>
        </span>
        <div class="min-w-0 flex-1">
          <button
            type="button"
            class="inline-flex h-11 items-center gap-2 rounded-[14px] px-[18px] text-sm font-semibold transition-colors"
            :class="step >= 2 ? 'border border-line bg-white text-accent-600' : step === 1 ? 'bg-ink text-white hover:bg-brand-800' : 'border border-line bg-white text-ink hover:border-accent-500'"
            @click="copyImage"
          >
            <Icon v-if="step >= 2" name="lucide:check" class="size-4" />
            {{ step >= 2 ? t('posts.tg.copied') : t('posts.tg.copyImage') }}
          </button>
          <p class="mt-1.5 text-[13px] leading-normal text-muted">{{ t('posts.tg.step2', { key: pasteKey }) }}</p>
          <p v-if="failed" role="alert" class="mt-1.5 text-[13px] leading-normal text-red-700">{{ t('posts.tg.copyFailed') }}</p>
        </div>
      </li>
    </ol>

    <a :href="href" target="_blank" rel="noopener" class="mt-5 block border-t border-line/70 pt-3.5 text-[13px] font-semibold text-brand-700 hover:text-brand-900">
      {{ t('posts.tg.openLink') }} →
    </a>
  </AppDialog>
</template>
