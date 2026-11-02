<script setup lang="ts">
import type { StaffProfile } from '#shared/types/api'
import { renderSVG } from 'uqr'

// "QR kod" va "Ulashish" (vizitka) oynalari — Staff sahifasi va xodim kabinetida bir xil (oldingi saytdagidek).
// url — xodimning ommaviy Staff sahifasi manzili (QR ichida shu bo'ladi)
const qrOpen = defineModel<boolean>('qr', { default: false })
const shareOpen = defineModel<boolean>('share', { default: false })
const props = defineProps<{ person: StaffProfile; url: string }>()

const { t, locale } = useI18n()

const names = computed(() => staffName(props.person.name, props.person.patronymic))
const roles = computed(() => staffRoles(props.person.employments))
const departments = computed(() => roles.value.departments.map(d => d.name))
const positionText = computed(() => roles.value.positions.join(', '))

const buttonClass = 'flex h-12 w-full items-center justify-center gap-2 rounded-[14px] text-[15px] font-semibold transition-colors'
const qrSvg = computed(() => renderSVG(props.url, { border: 1, blackColor: '#13112F', whiteColor: '#FFFFFF' }))

const shareTo = computed(() => {
  const url = encodeURIComponent(props.url)
  const text = encodeURIComponent(names.value.full)
  return [
    { key: 'telegram', label: t('staff.profile.shareTelegram'), icon: 'simple-icons:telegram', tile: 'bg-[#229ed9]', href: `https://t.me/share/url?url=${url}&text=${text}` },
    { key: 'whatsapp', label: t('staff.profile.shareWhatsapp'), icon: 'simple-icons:whatsapp', tile: 'bg-[#25d366]', href: `https://wa.me/?text=${text}%20${url}` },
    { key: 'facebook', label: t('staff.profile.shareFacebook'), icon: 'simple-icons:facebook', tile: 'bg-[#1877f2]', href: `https://www.facebook.com/sharer/sharer.php?u=${url}` },
  ]
})

const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined
async function copyLink() {
  try {
    await navigator.clipboard.writeText(props.url)
    copied.value = true
    trackEvent('Xodim vizitkasi ulaşildi', props.person.id)
    clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => { copied.value = false }, 2500)
  }
  catch {
    // Clipboard ruxsati bo'lmasa — hech narsa qilmaymiz
  }
}

const fileBase = computed(() => `uzswlu-xodim-${props.person.id}`)

async function downloadQr() {
  saveBlob(await renderQrPng(props.url), `${fileBase.value}-qr.png`)
}

// Vizitka rasmi oyna ochilishi bilan tayyorlanadi: "Yuborish" bosilganda telefon
// ulashish oynasi darhol ochilishi uchun (kechiksa brauzer ruxsat bermaydi)
const cardBlob = shallowRef<Blob | null>(null)
const preparing = ref(false)
async function prepareCard() {
  if (cardBlob.value || preparing.value) return
  preparing.value = true
  try {
    cardBlob.value = await renderStaffCard({
      nameMain: names.value.main,
      nameSharif: names.value.sharif,
      position: positionText.value,
      department: departments.value.join(', '),
      university: t('university.name'),
      url: props.url,
      photo: props.person.photo,
      photoFallback: props.person.photoFallback,
    })
  }
  finally {
    preparing.value = false
  }
}
watch(shareOpen, (open) => { if (open) prepareCard() })
// Til yoki surat o'zgarsa — vizitka qayta chiziladi
watch([locale, () => props.person.photo], () => { cardBlob.value = null })

async function downloadCard() {
  if (props.person.cardImage) {
    window.open(props.person.cardImage, '_blank', 'noopener')
    return
  }
  await prepareCard()
  if (cardBlob.value) saveBlob(cardBlob.value, `${fileBase.value}.png`)
  trackEvent('Xodim vizitkasi ulaşildi', props.person.id)
}

const canSendFiles = ref(false)
onMounted(() => {
  const probe = new File([''], 'probe.png', { type: 'image/png' })
  const touch = window.matchMedia('(pointer: coarse)').matches
  canSendFiles.value = touch && typeof navigator.canShare === 'function' && navigator.canShare({ files: [probe] })
})
function sendCard() {
  if (!cardBlob.value) return
  const file = new File([cardBlob.value], `${fileBase.value}.png`, { type: 'image/png' })
  navigator.share({ files: [file], title: names.value.full, text: props.url }).catch(() => {})
  trackEvent('Xodim vizitkasi ulaşildi', props.person.id)
}
</script>

<template>
  <!-- QR kod -->
  <AppDialog v-model:open="qrOpen" :title="t('staff.profile.qrTitle')" class="max-w-[420px]">
    <div class="mx-auto mt-4 w-60 rounded-[20px] border border-line p-3">
      <div role="img" :aria-label="t('staff.profile.qrAlt')" class="aspect-square [&>svg]:size-full" v-html="qrOpen ? qrSvg : ''" />
    </div>
    <ul class="mt-4 flex justify-center gap-3">
      <li v-for="s in shareTo" :key="s.key">
        <a :href="s.href" target="_blank" rel="noopener" class="grid size-12 place-items-center rounded-full text-white transition-transform hover:-translate-y-0.5" :class="s.tile">
          <Icon :name="s.icon" class="size-[22px]" />
          <span class="sr-only">{{ s.label }} ({{ t('staff.profile.newTab') }})</span>
        </a>
      </li>
    </ul>
    <div class="mt-4.5 grid gap-2.5">
      <button type="button" :class="[buttonClass, 'border border-line bg-white text-ink hover:border-accent-500']" @click="copyLink">
        <Icon :name="copied ? 'lucide:check' : 'lucide:copy'" class="size-[17px]" />
        <span aria-live="polite">{{ copied ? t('staff.profile.copied') : t('staff.profile.copyLink') }}</span>
      </button>
      <button type="button" :class="[buttonClass, 'bg-brand-900 text-white hover:bg-brand-800']" @click="downloadQr">
        <Icon name="lucide:download" class="size-[17px]" />
        {{ t('staff.profile.downloadQr') }}
      </button>
      <button type="button" :class="[buttonClass, 'bg-[#f2f0ea] text-ink hover:bg-line']" @click="qrOpen = false">
        {{ t('staff.profile.close') }}
      </button>
    </div>
  </AppDialog>

  <!-- Ulashish: vizitka (oldingi saytdagi tuzilish — bejik nisbatida; QR ostida havola yozilmaydi) -->
  <AppDialog v-model:open="shareOpen" :title="t('staff.profile.cardTitle')" hide-title class="max-w-[400px]" body-class="p-4">
    <div class="relative overflow-hidden rounded-[18px] bg-[linear-gradient(170deg,var(--color-brand-800)_0%,var(--color-brand-900)_60%,var(--color-brand-950)_100%)] px-[18px] pt-[22px] pb-[18px] text-center text-white">
      <!-- Universitet belgisi — yarim halqa markazida (profil kartasidagidek) -->
      <span aria-hidden="true" class="decor pointer-events-none absolute -top-6 -right-12 size-50 rounded-full border-[26px] border-accent-400/7" />
      <img src="/logos/mark.webp" alt="" aria-hidden="true" class="decor pointer-events-none absolute top-9 right-5 w-16 opacity-20 select-none">
      <small class="relative block text-xs text-white/80">{{ t('university.name') }}</small>
      <span class="relative mx-auto mt-3.5 mb-2.5 block size-[104px] rounded-full bg-[linear-gradient(135deg,var(--color-accent-400),var(--color-brand-500))] p-[3px]">
        <StaffAvatar :id="person.id" :name="names.full" :photo="person.photo" :fallback="person.photoFallback" decorative class="size-full rounded-full bg-brand-100! font-sans! text-[30px] font-bold! text-brand-900!" />
      </span>
      <h3 class="relative mb-1 text-[19px] leading-tight font-bold">
        {{ names.main }}<span v-if="names.sharif" class="block">{{ names.sharif }}</span>
      </h3>
      <p class="relative mb-0.5 text-sm text-white/85">{{ positionText }}</p>
      <!-- Har bir bo'lim butun bo'lak: sig'masa butunicha pastga tushadi, "4-kurs" o'rtasidan uzilmaydi -->
      <p class="relative mb-3 text-xs text-white/65">
        <template v-for="(d, i) in departments" :key="i"><span class="inline-block max-w-full">{{ d }}{{ i < departments.length - 1 ? ',' : '' }}</span>{{ ' ' }}</template>
      </p>
      <div class="relative mx-auto mt-3 w-[200px] max-w-[70%] rounded-2xl bg-white p-3">
        <div role="img" :aria-label="t('staff.profile.qrAlt')" class="aspect-square [&>svg]:size-full" v-html="shareOpen ? qrSvg : ''" />
      </div>
    </div>

    <div class="mt-3 grid gap-2">
      <button type="button" :class="[buttonClass, 'bg-accent-400 font-bold text-ink hover:bg-accent-300']" :disabled="preparing" @click="downloadCard">
        <Icon :name="preparing ? 'lucide:loader-circle' : 'lucide:download'" class="size-[17px]" :class="preparing && 'animate-spin'" />
        {{ preparing ? t('staff.profile.preparing') : t('staff.profile.downloadCard') }}
      </button>
      <!-- Faqat telefonda (sensorli ekran + ulashish imkoni bor) — oldingi saytdagidek -->
      <button v-if="canSendFiles" type="button" :class="[buttonClass, 'border border-line bg-white text-ink hover:border-accent-500']" :disabled="!cardBlob" @click="sendCard">
        <Icon name="lucide:share-2" class="size-[17px]" />
        {{ t('staff.profile.send') }}
      </button>
      <button type="button" :class="[buttonClass, 'border border-line bg-white text-ink hover:border-accent-500']" @click="copyLink">
        <Icon :name="copied ? 'lucide:check' : 'lucide:copy'" class="size-[17px]" />
        <span aria-live="polite">{{ copied ? t('staff.profile.copied') : t('staff.profile.copyLink') }}</span>
      </button>
      <button type="button" :class="[buttonClass, 'border border-line bg-white text-ink hover:border-accent-500']" @click="shareOpen = false">
        {{ t('staff.profile.close') }}
      </button>
    </div>
  </AppDialog>
</template>
