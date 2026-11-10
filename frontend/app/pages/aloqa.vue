<script setup lang="ts">
import type { AppealResult, ContactPage } from '#shared/types/api'

// Aloqa va Virtual qabulxona (canvas: "Aloqa va Virtual qabulxona")
const { t, locale } = useI18n()

const { data } = await useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale } })

const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`

// Virtual qabulxona
const form = reactive({ name: '', phone: '', email: '', recipient: '', message: '', consent: false })
const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()
const sending = ref(false)
const result = ref<AppealResult | null>(null)
const errorText = ref('')
const MAX_FILE = 10 * 1024 * 1024

watchEffect(() => {
  if (!form.recipient && data.value?.recipients[0]) form.recipient = data.value.recipients[0].id
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

function removeFile() {
  file.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function submit() {
  errorText.value = ''
  sending.value = true
  try {
    const body = new FormData()
    body.append('name', form.name.trim())
    body.append('phone', form.phone.trim())
    body.append('email', form.email.trim())
    body.append('recipient', form.recipient)
    body.append('message', form.message.trim())
    body.append('consent', form.consent ? 'yes' : 'no')
    if (file.value) body.append('file', file.value)
    result.value = await $fetch<AppealResult>('/api/appeals', { method: 'POST', body })
    trackEvent('Virtual qabulxona murojaati')
    Object.assign(form, { name: '', phone: '', email: '', message: '', consent: false })
    removeFile()
  }
  catch {
    errorText.value = t('contact.form.error')
  }
  finally {
    sending.value = false
  }
}

useSeo({ title: () => t('contact.title'), description: () => t('contact.lead') })
</script>

<template>
  <div v-if="data">
    <PageIntro :crumbs="[{ label: t('nav.contact') }]" :title="t('contact.title')" :lead="t('contact.lead')" />

    <section class="mx-auto max-w-7xl px-4 pt-9 sm:px-6 lg:px-8">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <a :href="tel(data.hotline.phone)" class="rounded-3xl bg-brand-900 p-6 text-white transition-colors hover:bg-brand-800">
          <span class="block text-[13px] text-white/60">{{ t('contact.hotline') }}</span>
          <span class="mt-1.5 block font-display text-[28px] font-semibold">{{ data.hotline.phone }}</span>
          <span v-if="data.hotline.ext" class="mt-1 block text-[13px] text-accent-400">{{ t('contact.ext', { ext: data.hotline.ext }) }}</span>
        </a>
        <div v-for="e in data.emails" :key="e.value" class="rounded-3xl border border-line bg-white p-6">
          <span class="block text-[13px] text-muted">{{ e.title }}</span>
          <a :href="`mailto:${e.value}`" class="mt-1.5 block text-lg font-semibold break-all hover:text-brand-700">{{ e.value }}</a>
          <span v-if="e.extra.length" class="mt-1 block text-[13px] break-all text-muted">{{ e.extra.join(' · ') }}</span>
        </div>
        <a href="https://t.me/UzSWLU" target="_blank" rel="noopener" class="rounded-3xl border border-line bg-white p-6 text-ink transition-colors hover:border-accent-500">
          <span class="block text-[13px] text-muted">Telegram</span>
          <span class="mt-1.5 block text-lg font-semibold">t.me/UzSWLU</span>
          <span class="mt-1 block text-[13px] text-brand-700">{{ t('contact.channel') }} →</span>
        </a>
      </div>
    </section>

    <!-- Binolar -->
    <section class="mx-auto max-w-7xl px-4 pt-16 sm:px-6 lg:px-8">
      <h2 class="font-display text-4xl font-semibold sm:text-[40px]">{{ t('contact.campuses') }}</h2>
      <ul class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <li v-for="c in data.campuses" :key="c.id" class="overflow-hidden rounded-3xl border border-line bg-white">
          <a :href="c.mapUrl" target="_blank" rel="noopener" :aria-label="`${t('contact.route')}: ${c.name}`" class="relative grid h-[150px] place-items-center bg-brand-100 transition-colors hover:bg-brand-200">
            <span class="size-10 -rotate-45 rounded-[999px_999px_999px_0] bg-brand-800 shadow-[0_8px_20px_-6px_rgba(42,32,102,0.6)]" aria-hidden="true" />
          </a>
          <div class="p-5">
            <h3 class="text-lg font-semibold">{{ c.name }}</h3>
            <p class="mt-2 text-sm leading-normal text-muted">{{ c.address }}</p>
            <a :href="tel(c.phone)" class="mt-2.5 block text-[15px] font-semibold hover:text-brand-700">{{ c.phone }}</a>
            <a :href="c.mapUrl" target="_blank" rel="noopener" class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700">{{ t('contact.route') }} →</a>
          </div>
        </li>
      </ul>
    </section>

    <!-- Rahbariyat telefonlari + Virtual qabulxona -->
    <section class="mx-auto grid max-w-7xl items-start gap-7 px-4 pt-16 pb-24 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:px-8">
      <div class="min-w-0">
        <h2 class="font-display text-[34px] font-semibold">{{ t('contact.leaders') }}</h2>
        <div class="mt-5 overflow-x-auto rounded-[22px] border border-line bg-white">
          <table class="w-full min-w-[520px] border-collapse text-sm">
            <thead>
              <tr class="text-left text-xs text-muted">
                <th scope="col" class="border-b border-line px-[18px] py-3.5 font-semibold">{{ t('contact.table.name') }}</th>
                <th scope="col" class="border-b border-line px-[18px] py-3.5 font-semibold">{{ t('contact.table.ext') }}</th>
                <th scope="col" class="border-b border-line px-[18px] py-3.5 font-semibold">{{ t('contact.table.phone') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in data.leaders" :key="l.name" class="border-b border-line/60 last:border-0">
                <td class="px-[18px] py-3.5"><span class="block font-semibold">{{ l.name }}</span><span class="mt-0.5 block text-muted">{{ l.role }}</span></td>
                <td class="px-[18px] py-3.5 font-semibold">{{ l.ext }}</td>
                <td class="px-[18px] py-3.5 whitespace-nowrap"><a :href="tel(l.phone)" class="hover:text-brand-700">{{ l.phone }}</a></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 text-[13px] text-muted">{{ t('contact.reception', { phone: data.reception }) }}</p>
      </div>

      <form id="appeal" class="scroll-mt-32 rounded-[28px] border border-line bg-white p-6 sm:p-8" aria-labelledby="appeal-title" @submit.prevent="submit">
        <h2 id="appeal-title" class="font-display text-[34px] font-semibold">{{ t('contact.form.title') }}</h2>
        <p class="mt-2 text-[15px] text-muted">{{ t('contact.form.text') }}</p>

        <div v-if="result" role="status" class="mt-6 rounded-2xl bg-accent-100 p-5 text-accent-700">
          <p class="flex items-center gap-2 font-semibold"><Icon name="lucide:circle-check" class="size-5" />{{ t('contact.form.success') }}</p>
          <p class="mt-1 text-sm">{{ t('contact.form.number', { number: result.number }) }}</p>
          <button type="button" class="mt-3 text-sm font-semibold underline underline-offset-4" @click="result = null">{{ t('contact.form.another') }}</button>
        </div>

        <template v-else>
          <div class="mt-6 grid gap-3.5 sm:grid-cols-2">
            <div>
              <label for="vq-name" class="mb-1.5 block text-[13px] font-semibold text-muted">{{ t('contact.form.name') }}</label>
              <input id="vq-name" v-model="form.name" type="text" autocomplete="name" required minlength="3" maxlength="200" class="h-[50px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
            </div>
            <div>
              <label for="vq-phone" class="mb-1.5 block text-[13px] font-semibold text-muted">{{ t('contact.form.phone') }}</label>
              <input id="vq-phone" v-model="form.phone" type="tel" autocomplete="tel" required placeholder="+998" pattern="\+?[\d\s\(\)\-]{7,20}" class="h-[50px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
            </div>
            <div>
              <label for="vq-email" class="mb-1.5 block text-[13px] font-semibold text-muted">{{ t('contact.form.email') }}</label>
              <input id="vq-email" v-model="form.email" type="email" autocomplete="email" required maxlength="200" class="h-[50px] w-full rounded-[14px] border border-line px-3.5 outline-none focus:border-accent-600">
            </div>
            <div>
              <label for="vq-to" class="mb-1.5 block text-[13px] font-semibold text-muted">{{ t('contact.form.to') }}</label>
              <select id="vq-to" v-model="form.recipient" required class="h-[50px] w-full rounded-[14px] border border-line bg-white px-3 outline-none focus:border-accent-600">
                <option v-for="r in data.recipients" :key="r.id" :value="r.id">{{ r.title }}</option>
              </select>
            </div>
          </div>
          <div class="mt-3.5">
            <label for="vq-msg" class="mb-1.5 block text-[13px] font-semibold text-muted">{{ t('contact.form.message') }}</label>
            <textarea id="vq-msg" v-model="form.message" rows="5" required minlength="10" maxlength="5000" class="w-full resize-y rounded-[14px] border border-line px-3.5 py-3 outline-none focus:border-accent-600" />
          </div>
          <label class="mt-3.5 flex items-start gap-2.5 text-[13px] leading-normal text-muted">
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
          <p class="mt-2 text-xs text-muted">{{ t('contact.form.fileHint') }}</p>
        </template>
      </form>
    </section>
  </div>
</template>
