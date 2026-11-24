<script setup lang="ts">
import type { AppealResult, FacultyList, ProgramList } from '#shared/types/api'

// Xorijiy abituriyent arizasi («Xalqaro talabalar» → «Ariza şakli»): şaxsiy ma'lumot, ta'lim tanlovi va 3 ta fayl (pasport, diplom/sertifikat, 3x4 surat).
// Ariza admin panelga tuşadi (Arizalar), fayllar yopiq saqlanadi.
const { t, locale } = useI18n()
const MAX_FILE = 5 * 1024 * 1024

const blank = () => ({ lastName: '', firstName: '', middleName: '', passport: '', country: '', address: '', gender: '', faculty: '', studyForm: '', degree: '', program: '', phone: '', email: '', consent: false })
const form = reactive(blank())
const FILES = ['passportFile', 'diplomaFile', 'photoFile'] as const
type FileKey = (typeof FILES)[number]
const files = reactive<Record<FileKey, File | null>>({ passportFile: null, diplomaFile: null, photoFile: null })
const sending = ref(false)
const result = ref<AppealResult | null>(null)
const errorText = ref('')

const { data: faculties } = await useFetch<FacultyList>('/api/faculties', { query: { lang: locale }, key: 'app-faculties' })
// Yönalişlar — bakalavriat/magistratura uçun ro'yxatdan, doktoranturada — qölda
const level = computed(() => (form.degree === 'master' ? 'master' : 'bachelor'))
const { data: programs } = await useFetch<ProgramList>('/api/programs', { query: { lang: locale, level }, key: 'app-programs' })
const programOptions = computed(() => [...new Set((programs.value?.items ?? []).map(p => `${p.code} — ${p.title}`))])
watch(() => form.degree, () => { form.program = '' })

function pick(key: FileKey, event: Event) {
  const input = event.target as HTMLInputElement
  const f = input.files?.[0] ?? null
  errorText.value = ''
  if (f && f.size > MAX_FILE) {
    errorText.value = t('application.fileTooBig')
    input.value = ''
    return
  }
  files[key] = f
}

async function submit() {
  errorText.value = ''
  if (FILES.some(k => !files[k])) {
    errorText.value = t('application.filesRequired')
    return
  }
  sending.value = true
  try {
    const body = new FormData()
    for (const [k, v] of Object.entries(form)) body.append(k, k === 'consent' ? (v ? 'yes' : 'no') : String(v).trim())
    body.append('lang', locale.value)
    for (const k of FILES) body.append(k, files[k]!)
    result.value = await $fetch<AppealResult>('/api/applications', { method: 'POST', body })
    trackEvent('Xorijiy abituriyent arizasi')
    Object.assign(form, blank())
    for (const k of FILES) files[k] = null
  }
  catch {
    errorText.value = t('application.error')
  }
  finally {
    sending.value = false
  }
}

const input = 'h-14 w-full rounded-[14px] border border-line bg-white px-3.5 text-[17px] outline-none focus:border-accent-600'
const label = 'mb-2 block text-[15px] font-semibold text-ink/75'
</script>

<template>
  <form id="application" class="relative scroll-mt-32 overflow-hidden rounded-[28px] border border-line bg-white p-6 shadow-[0_30px_60px_-40px_rgb(56_43_133/0.45)] sm:p-10" aria-labelledby="application-title" @submit.prevent="submit">
    <span class="absolute inset-x-0 top-0 h-1.5 bg-[linear-gradient(90deg,var(--color-brand-700),var(--color-accent-500))]" aria-hidden="true" />
    <div class="flex items-start gap-4">
      <span class="hidden size-14 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-700 sm:grid"><Icon name="lucide:file-pen-line" class="text-[26px]" /></span>
      <div>
        <h2 id="application-title" class="font-display text-[34px] leading-tight font-semibold">{{ t('application.title') }}</h2>
        <p class="mt-1.5 text-[17px] text-muted">{{ t('application.text') }}</p>
      </div>
    </div>

    <div v-if="result" role="status" class="mt-6 rounded-2xl bg-accent-100 p-5 text-accent-700">
      <p class="flex items-center gap-2 font-semibold"><Icon name="lucide:circle-check" class="size-5" />{{ t('application.success') }}</p>
      <p class="mt-1 text-sm">{{ t('application.number', { number: result.number }) }}</p>
      <button type="button" class="mt-3 text-sm font-semibold underline underline-offset-4" @click="result = null">{{ t('application.another') }}</button>
    </div>

    <template v-else>
      <h3 class="mt-8 text-sm font-bold tracking-wide text-brand-700 uppercase">{{ t('application.personal') }}</h3>
      <div class="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div><label for="ap-last" :class="label">{{ t('application.lastName') }}</label><input id="ap-last" v-model="form.lastName" required minlength="2" maxlength="70" autocomplete="family-name" :class="input"></div>
        <div><label for="ap-first" :class="label">{{ t('application.firstName') }}</label><input id="ap-first" v-model="form.firstName" required minlength="2" maxlength="60" autocomplete="given-name" :class="input"></div>
        <div><label for="ap-middle" :class="label">{{ t('application.middleName') }}</label><input id="ap-middle" v-model="form.middleName" maxlength="60" autocomplete="additional-name" :class="input"></div>
        <div><label for="ap-pass" :class="label">{{ t('application.passport') }}</label><input id="ap-pass" v-model="form.passport" required pattern="[A-Za-z0-9 ]{5,24}" maxlength="24" placeholder="AB1234567" autocomplete="off" :class="[input, 'uppercase']"></div>
        <div><label for="ap-country" :class="label">{{ t('application.country') }}</label><input id="ap-country" v-model="form.country" required minlength="2" maxlength="80" autocomplete="country-name" :class="input"></div>
        <div>
          <label for="ap-gender" :class="label">{{ t('application.gender') }}</label>
          <select id="ap-gender" v-model="form.gender" required :class="input">
            <option value="" disabled>{{ t('application.choose') }}</option>
            <option value="male">{{ t('application.male') }}</option>
            <option value="female">{{ t('application.female') }}</option>
          </select>
        </div>
        <div class="sm:col-span-2 lg:col-span-3"><label for="ap-addr" :class="label">{{ t('application.address') }}</label><input id="ap-addr" v-model="form.address" required minlength="5" maxlength="300" autocomplete="street-address" :class="input"></div>
        <div><label for="ap-phone" :class="label">{{ t('application.phone') }}</label><input id="ap-phone" v-model="form.phone" type="tel" required pattern="\+?[\d\s\(\)\-]{7,20}" placeholder="+" autocomplete="tel" :class="input"></div>
        <div><label for="ap-email" :class="label">{{ t('application.email') }}</label><input id="ap-email" v-model="form.email" type="email" required maxlength="200" autocomplete="email" :class="input"></div>
      </div>

      <h3 class="mt-8 text-sm font-bold tracking-wide text-brand-700 uppercase">{{ t('application.study') }}</h3>
      <div class="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label for="ap-degree" :class="label">{{ t('application.degree') }}</label>
          <select id="ap-degree" v-model="form.degree" required :class="input">
            <option value="" disabled>{{ t('application.choose') }}</option>
            <option v-for="d in ['bachelor', 'master', 'doctorate']" :key="d" :value="d">{{ t(`application.degrees.${d}`) }}</option>
          </select>
        </div>
        <div>
          <label for="ap-form" :class="label">{{ t('application.studyForm') }}</label>
          <select id="ap-form" v-model="form.studyForm" required :class="input">
            <option value="" disabled>{{ t('application.choose') }}</option>
            <option v-for="f in ['day', 'distance', 'evening']" :key="f" :value="f">{{ t(`application.forms.${f}`) }}</option>
          </select>
        </div>
        <div>
          <label for="ap-fac" :class="label">{{ t('application.faculty') }}</label>
          <select id="ap-fac" v-model="form.faculty" required :class="input">
            <option value="" disabled>{{ t('application.choose') }}</option>
            <option v-for="f in faculties?.items ?? []" :key="f.id" :value="f.name">{{ f.name }}</option>
          </select>
        </div>
        <div class="sm:col-span-2 lg:col-span-3">
          <label for="ap-prog" :class="label">{{ t('application.program') }}</label>
          <select v-if="form.degree !== 'doctorate' && programOptions.length" id="ap-prog" v-model="form.program" required :class="input">
            <option value="" disabled>{{ form.degree ? t('application.choose') : t('application.degreeFirst') }}</option>
            <option v-for="p in programOptions" :key="p" :value="p">{{ p }}</option>
          </select>
          <input v-else id="ap-prog" v-model="form.program" required minlength="2" maxlength="300" :placeholder="t('application.programHint')" :class="input">
        </div>
      </div>

      <h3 class="mt-8 text-sm font-bold tracking-wide text-brand-700 uppercase">{{ t('application.files') }}</h3>
      <div class="mt-3 grid gap-3 sm:grid-cols-3">
        <label v-for="k in FILES" :key="k" class="group relative flex min-h-[112px] cursor-pointer flex-col justify-between gap-2 rounded-2xl border border-dashed p-4 transition-colors" :class="files[k] ? 'border-accent-500 bg-accent-100/40' : 'border-brand-200 hover:bg-brand-50'">
          <span class="flex items-center gap-2 font-semibold text-ink">
            <Icon :name="files[k] ? 'lucide:circle-check' : 'lucide:upload'" class="size-5 shrink-0" :class="files[k] ? 'text-accent-700' : 'text-brand-700'" />
            {{ t(`application.${k}`) }}
          </span>
          <span class="truncate text-sm" :class="files[k] ? 'font-medium text-accent-700' : 'text-muted'">{{ files[k]?.name ?? t('application.pick') }}</span>
          <input type="file" class="sr-only" accept=".pdf,.jpg,.jpeg,.png" @change="pick(k, $event)">
        </label>
      </div>
      <p class="mt-2 text-sm text-muted">{{ t('application.fileHint') }}</p>

      <label class="mt-5 flex items-start gap-2.5 text-[15px] leading-normal text-muted">
        <input v-model="form.consent" type="checkbox" required class="mt-0.5 size-[18px] shrink-0 accent-brand-800">
        {{ t('application.consent') }}
      </label>
      <p v-if="errorText" role="alert" class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{{ errorText }}</p>
      <button type="submit" :disabled="sending" class="mt-5 inline-flex h-[52px] items-center gap-2 rounded-full bg-brand-800 px-[26px] font-semibold text-white transition-colors hover:bg-brand-700 disabled:opacity-60">
        <Icon v-if="sending" name="lucide:loader-circle" class="size-4 animate-spin" />
        {{ sending ? t('application.sending') : t('application.submit') }}
      </button>
    </template>
  </form>
</template>
