<script setup lang="ts">
import type { AppealResult } from '#shared/types/api'
import { DEFAULT_RUDE_WORDS, junkFlags, makeRudeTest, textIssues, type TextIssue } from '#shared/utils/text-quality'

// Virtual qabulxona murojaati shakli: «Aloqa» va «Virtual qabulxona» sahifalarida bir xil ishlatiladi
const props = defineProps<{ recipients: { id: string; title: string }[]; rudeWords?: string[] }>()
// Haqoratli so'zlar — admin paneldagi ro'yxat (GET /contact → rudeWords); bo'lmasa zaxira ro'yxat
const rude = computed(() => makeRudeTest(props.rudeWords ?? DEFAULT_RUDE_WORDS))
const { t } = useI18n()

// Virtual qabulxona
const form = reactive({ lastName: '', firstName: '', middleName: '', pSeries: '', pNumber: '', phone: '', email: '', recipient: '', message: '', consent: false })
const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()
const sending = ref(false)
const result = ref<AppealResult | null>(null)
const errorText = ref('')
const MAX_FILE = 10 * 1024 * 1024

watchEffect(() => {
  if (!form.recipient && props.recipients[0]) form.recipient = props.recipients[0].id
})

function pickFile(event: Event) {
  const picked = (event.target as HTMLInputElement).files?.[0] ?? null
  errorText.value = ''
  if (picked && picked.size > MAX_FILE) {
    errorText.value = t('contact.form.fileTooBig')
    ;(event.target as HTMLInputElement).value = ''
    return
  }
  file.value = picked
}

// Yangi o'zbek alifbosi harflari: matn oynasi tepasidagi tugmalar kursor turgan joyga qo'yadi
const LETTERS = ['Ö', 'ö', 'Ğ', 'ğ', 'Ş', 'ş', 'Ç', 'ç', 'ʼ']
const msgEl = ref<HTMLTextAreaElement>()
function insertLetter(ch: string) {
  const el = msgEl.value
  if (!el) return
  const start = el.selectionStart ?? form.message.length
  const end = el.selectionEnd ?? start
  form.message = (form.message.slice(0, start) + ch + form.message.slice(end)).slice(0, 5000)
  nextTick(() => { el.focus(); el.setSelectionRange(start + ch.length, start + ch.length) })
}

// Yozish paytida ogohlantirish: yozish to'xtagach (0,7 s) matn tekshiriladi; qisqa matnda jim turadi
const msgIssues = ref<Exclude<TextIssue, null>[]>([])
const msgWarn = computed(() => msgIssues.value.length > 0)
let warnTimer: ReturnType<typeof setTimeout> | undefined
watch(() => form.message, (v) => {
  clearTimeout(warnTimer)
  if (!v.trim()) { msgIssues.value = []; checked.value = ''; return }
  warnTimer = setTimeout(() => {
    msgIssues.value = v.trim().length >= 12 ? textIssues(v, rude.value) : []
    checked.value = v   // tasodifiy so'zlar va ortiqcha takrorlar doim qizil, matn umuman o'tsa ham
  }, 700)
})
// Matn ostidagi qatlam: tasodifiy so'zlar qizil (textarea matni shaffof, kursor ko'rinadi)
const checked = ref('')
const segments = computed(() => {
  const ref = checked.value.split(/\s+/).filter(Boolean)
  const flags = junkFlags(checked.value, rude.value)
  let k = -1
  return form.message.split(/(\s+)/).map((p) => {
    if (!p.trim()) return { text: p, bad: false }
    k++
    return { text: p, bad: !!flags[k] && ref[k] === p }   // faqat tekshirilgan (0,7 s) holatdagi so'z
  })
})
const mirror = ref<HTMLElement>()
const syncScroll = () => { if (mirror.value && msgEl.value) mirror.value.scrollTop = msgEl.value.scrollTop }
onBeforeUnmount(() => clearTimeout(warnTimer))

function removeFile() {
  file.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function submit() {
  errorText.value = ''
  // Tasodifiy harflar yoki takroriy so'zlar bilan yozilgan matn yuborilmaydi
  const issues = textIssues(form.message, rude.value)
  if (issues.length) {
    msgIssues.value = issues
    errorText.value = issues.map(k => t(`contact.form.bad.${k}`)).join(' ')
    msgEl.value?.focus()
    return
  }
  sending.value = true
  try {
    const body = new FormData()
    body.append('name', [form.lastName, form.firstName, form.middleName].map(v => v.trim()).filter(Boolean).join(' '))
    body.append('passport', `${form.pSeries}${form.pNumber}`.replace(/\s/g, '').toUpperCase())
    body.append('phone', form.phone.trim())
    body.append('email', form.email.trim())
    body.append('recipient', form.recipient)
    body.append('message', form.message.trim())
    body.append('consent', form.consent ? 'yes' : 'no')
    if (file.value) body.append('file', file.value)
    result.value = await $fetch<AppealResult>('/api/appeals', { method: 'POST', body })
    trackEvent('Virtual qabulxona murojaati')
    Object.assign(form, { lastName: '', firstName: '', middleName: '', pSeries: '', pNumber: '', phone: '', email: '', message: '', consent: false })
    removeFile()
  }
  catch {
    errorText.value = t('contact.form.error')
  }
  finally {
    sending.value = false
  }
}
</script>

<template>
  <form id="appeal" class="relative scroll-mt-32 overflow-hidden rounded-[28px] border border-line bg-white p-6 shadow-[0_30px_60px_-40px_rgb(56_43_133/0.45)] sm:p-10" aria-labelledby="appeal-title" @submit.prevent="submit">
    <span class="absolute inset-x-0 top-0 h-1.5 bg-[linear-gradient(90deg,var(--color-brand-700),var(--color-accent-500))]" aria-hidden="true" />
    <div class="flex items-start gap-4">
      <span class="hidden size-14 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-700 sm:grid"><Icon name="lucide:mail-pen" class="text-[26px]" /></span>
      <div>
        <h2 id="appeal-title" class="font-display text-[34px] leading-tight font-semibold">{{ t('contact.form.title') }}</h2>
        <p class="mt-1.5 text-[17px] text-muted">{{ t('contact.form.text') }}</p>
      </div>
    </div>

    <div v-if="result" role="status" class="mt-6 rounded-2xl bg-accent-100 p-5 text-accent-700">
      <p class="flex items-center gap-2 font-semibold"><Icon name="lucide:circle-check" class="size-5" />{{ t('contact.form.success') }}</p>
      <p class="mt-1 text-sm">{{ t('contact.form.number', { number: result.number }) }}</p>
      <button type="button" class="mt-3 text-sm font-semibold underline underline-offset-4" @click="result = null">{{ t('contact.form.another') }}</button>
    </div>

    <template v-else>
      <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label for="vq-last" class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.lastName') }}</label>
          <input id="vq-last" v-model="form.lastName" type="text" autocomplete="family-name" required minlength="2" maxlength="70" class="h-14 text-[17px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
        </div>
        <div>
          <label for="vq-first" class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.firstName') }}</label>
          <input id="vq-first" v-model="form.firstName" type="text" autocomplete="given-name" required minlength="2" maxlength="60" class="h-14 text-[17px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
        </div>
        <div>
          <label for="vq-middle" class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.middleName') }}</label>
          <input id="vq-middle" v-model="form.middleName" type="text" autocomplete="additional-name" maxlength="60" class="h-14 text-[17px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
        </div>
        <fieldset class="min-w-0">
          <legend class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.passport') }}</legend>
          <div class="flex gap-2">
            <input v-model="form.pSeries" type="text" required pattern="[A-Za-z]{2}" maxlength="2" placeholder="AA" autocomplete="off" :aria-label="t('contact.form.pSeries')" class="h-14 text-[17px] w-[72px] rounded-[14px] border border-line px-3.5 text-center uppercase outline-none focus:border-accent-600" @input="form.pSeries = form.pSeries.replace(/[^a-z]/gi, '').toUpperCase()">
            <input v-model="form.pNumber" type="text" inputmode="numeric" required pattern="\d{7}" maxlength="7" placeholder="1234567" autocomplete="off" :aria-label="t('contact.form.pNumber')" class="h-14 text-[17px] min-w-0 flex-1 rounded-[14px] border border-line px-3.5 tabular-nums outline-none focus:border-accent-600" @input="form.pNumber = form.pNumber.replace(/\D/g, '')">
          </div>
        </fieldset>
        <div>
          <label for="vq-phone" class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.phone') }}</label>
          <input id="vq-phone" v-model="form.phone" type="tel" autocomplete="tel" required placeholder="+998" pattern="\+?[\d\s\(\)\-]{7,20}" class="h-14 text-[17px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
        </div>
        <div>
          <label for="vq-email" class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.email') }}</label>
          <input id="vq-email" v-model="form.email" type="email" autocomplete="email" required maxlength="200" class="h-14 text-[17px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
        </div>
        <div class="sm:col-span-2 lg:col-span-3">
          <label for="vq-to" class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.to') }}</label>
          <select id="vq-to" v-model="form.recipient" required class="h-14 text-[17px] w-full rounded-[14px] border border-line bg-white px-3 outline-none focus:border-accent-600">
            <option v-for="r in recipients" :key="r.id" :value="r.id">{{ r.title }}</option>
          </select>
        </div>
      </div>
      <div class="mt-3.5">
        <label for="vq-msg" class="mb-2 block text-[15px] font-semibold text-ink/75">{{ t('contact.form.message') }}</label>
        <div class="overflow-hidden rounded-[14px] border transition-colors" :class="msgWarn ? 'border-amber-400 ring-4 ring-amber-100' : 'border-line focus-within:border-accent-600'">
          <div class="flex flex-wrap items-center gap-1.5 border-b border-line bg-brand-50/60 px-2.5 py-2" role="toolbar" :aria-label="t('contact.form.letters')">
            <span class="mr-1 text-sm font-semibold text-muted">{{ t('contact.form.letters') }}:</span>
            <button
              v-for="ch in LETTERS"
              :key="ch"
              type="button"
              class="grid h-9 min-w-9 place-items-center rounded-lg border border-line bg-white px-2 text-[17px] font-semibold text-brand-800 transition hover:border-brand-300 hover:bg-brand-50 active:scale-95"
              :aria-label="t('contact.form.insertLetter', { ch })"
              @mousedown.prevent
              @click="insertLetter(ch)"
            >{{ ch }}</button>
          </div>
          <div class="relative">
            <div ref="mirror" aria-hidden="true" class="pointer-events-none absolute inset-0 overflow-hidden px-4 py-3.5 text-[17px] leading-relaxed break-words whitespace-pre-wrap text-ink"><template v-for="(sg, i) in segments" :key="i"><span v-if="sg.bad" class="text-red-600 underline decoration-red-500 decoration-wavy underline-offset-4">{{ sg.text }}</span><template v-else>{{ sg.text }}</template></template><br></div>
            <textarea id="vq-msg" ref="msgEl" v-model="form.message" :aria-invalid="msgWarn" aria-describedby="vq-msg-warn" rows="6" required minlength="10" maxlength="5000" spellcheck="false" class="relative block w-full resize-y bg-transparent px-4 py-3.5 text-[17px] leading-relaxed break-words text-transparent caret-ink outline-none selection:bg-brand-100 selection:text-ink" @scroll="syncScroll" />
          </div>
        </div>
        <div class="mt-1.5 flex items-start justify-between gap-3">
          <ul id="vq-msg-warn" aria-live="polite" class="grid gap-1 text-[15px] font-medium text-amber-700">
            <li v-for="k in msgIssues" :key="k" class="flex items-start gap-2"><Icon name="lucide:triangle-alert" class="mt-0.5 size-[18px] shrink-0" />{{ t(`contact.form.bad.${k}`) }}</li>
          </ul>
          <span class="shrink-0 pt-0.5 text-xs text-muted tabular-nums">{{ form.message.length }} / 5000</span>
        </div>
      </div>
      <label class="mt-4 flex items-start gap-2.5 text-[15px] leading-normal text-muted">
        <input v-model="form.consent" type="checkbox" required class="mt-0.5 size-[18px] shrink-0 accent-brand-800">
        {{ t('contact.form.consent') }}
      </label>

      <p v-if="errorText" role="alert" class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{{ errorText }}</p>

      <div class="mt-5 flex flex-wrap items-center gap-3">
        <button type="submit" :disabled="sending" class="inline-flex h-[52px] items-center gap-2 rounded-full bg-brand-800 px-[26px] font-semibold text-white transition-colors hover:bg-brand-700 disabled:opacity-60">
          <Icon v-if="sending" name="lucide:loader-circle" class="size-4 animate-spin" />
          {{ sending ? t('contact.form.sending') : t('contact.form.submit') }}
        </button>
        <input ref="fileInput" type="file" class="sr-only" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" :aria-label="t('contact.form.attach')" @change="pickFile">
        <span v-if="file" class="inline-flex h-[52px] items-center gap-2 rounded-full bg-brand-50 pr-2 pl-4 text-sm font-semibold text-brand-800">
          <Icon name="lucide:paperclip" class="size-4" />
          <span class="max-w-[180px] truncate">{{ file.name }}</span>
          <button type="button" :aria-label="t('cabinet.remove')" class="grid size-8 place-items-center rounded-full hover:bg-white" @click="removeFile"><Icon name="lucide:x" class="size-4" /></button>
        </span>
        <button v-else type="button" class="h-[52px] rounded-full border border-dashed border-brand-200 px-5 text-sm font-semibold text-brand-700 transition-colors hover:bg-brand-50" @click="fileInput?.click()">+ {{ t('contact.form.attach') }}</button>
      </div>
      <p class="mt-2 text-sm text-muted">{{ t('contact.form.fileHint') }}</p>
    </template>
  </form>
</template>
