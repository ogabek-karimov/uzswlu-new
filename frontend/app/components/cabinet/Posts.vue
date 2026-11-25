<script setup lang="ts">
import type { CabinetPostDoc, CabinetPostList } from '#shared/types/api'

// «Yangiliklar» menyusi ma'lumotlari: rol egasi yangilik, e'lon va tadbirni saytdagi kabinetdan turib yozadi, tahrirlaydi, o'chiradi.
// Ruxsat (qaysi tur, fakultet doirasi, «faqat o'zi yozgan») backendda admin paneldagi qoidalar bilan tekshiriladi; `own` — tahrirlash mumkinmi.
// Matn oddiy ko'rinishda (bo'sh qator — yangi abzats). Admin panelda yozilgan murakkab formatlash (jadval, rasm) tegilmaydi: matn o'zgartirilmasa yuborilmaydi.
type PostType = CabinetPostDoc['type']
const props = defineProps<{ types: PostType[] }>()

const { t } = useI18n()
const LANGS = ['uz', 'ru', 'en', 'zh'] as const
type Lang = typeof LANGS[number]
type PerLang = Record<Lang, string>
const blank = (): PerLang => ({ uz: '', ru: '', en: '', zh: '' })

// Profil menyusidan `?tur=events` bilan kelganda shu tur ochiladi
const route = useRoute()
const fromQuery = (q: unknown) => props.types.find(k => k === q)
const tab = ref<PostType>(fromQuery(route.query.tur) ?? props.types[0] ?? 'news')
watch(() => route.query.tur, (q) => { const k = fromQuery(q); if (k) { tab.value = k; editing.value = null } })
const page = ref(1)
const { data, refresh, status } = await useFetch<CabinetPostList>('/api/me/cms/posts', {
  key: 'cabinet-posts',
  server: false,
  query: computed(() => ({ 'where[type][equals]': tab.value, 'sort': '-publishedAt', 'limit': 10, page: page.value, 'depth': 1 })),
  default: () => ({ docs: [], totalDocs: 0, totalPages: 1, page: 1 }),
})
watch(tab, () => { page.value = 1 })

// ── Matn <-> HTML ──
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const textToHtml = (s: string) => s.trim().split(/\n{2,}/).map(p => `<p>${esc(p.trim()).replace(/\n/g, '<br>')}</p>`).join('\n')
function htmlToText(html: string) {
  if (!html || !html.includes('<')) return html ?? ''
  const doc = new DOMParser().parseFromString(html, 'text/html')
  return [...doc.body.children].map(el => (el.textContent ?? '').trim()).filter(Boolean).join('\n\n')
}
const isRich = (html: string) => /<(table|img|iframe|video|ul|ol|h[1-6])\b/i.test(html || '')

// ── Forma ──
const editing = ref<null | 'new' | CabinetPostDoc>(null)
const lang = ref<Lang>('uz')
const busy = ref(false)
const error = ref('')
const uploading = ref(false)
const form = reactive({ title: blank(), excerpt: blank(), body: blank(), location: '', status: 'published' as 'draft' | 'published', startsAt: '', endsAt: '', cover: null as null | { id: number, url: string } })
const orig = reactive({ body: blank(), bodyText: blank() })

const toLocal = (iso: string | null) => {
  if (!iso) return ''
  const d = new Date(iso)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}
const fromLocal = (v: string) => (v ? new Date(v).toISOString() : null)

function open(doc: CabinetPostDoc | 'new') {
  error.value = ''
  lang.value = 'uz'
  const p = doc === 'new' ? null : doc
  for (const l of LANGS) {
    form.title[l] = p?.title?.[l] ?? ''
    form.excerpt[l] = p?.excerpt?.[l] ?? ''
    orig.body[l] = p?.body?.[l] ?? ''
    orig.bodyText[l] = htmlToText(orig.body[l])
    form.body[l] = orig.bodyText[l]
  }
  form.location = p?.location?.uz ?? ''
  form.status = p?.status ?? 'published'
  form.startsAt = toLocal(p?.startsAt ?? null)
  form.endsAt = toLocal(p?.endsAt ?? null)
  form.cover = p?.cover ? { id: p.cover.id, url: p.cover.url } : null
  editing.value = doc
}
// Kabinet bosh sahifasidagi «Yangi yangilik/e'lon/tadbir» tezkor amali: ?yangi=1 — forma darhol ochiladi
// «Yangi …» — kabinetda emas, ADMIN PANELda qo'shiladi: yangi tabda admin panelning shu turdagi «yangi» sahifasi ochiladi
// (xodim o'z roli bilan, bir martalik havola orqali). Tab bosish paytida ochiladi — brauzer bloklamasin
const openingNew = ref(false)
async function addInAdmin() {
  openingNew.value = true
  const win = window.open('', '_blank')
  if (win) win.opener = null
  try {
    const link = await $fetch<{ url: string | null }>('/api/me/admin-link', { query: { next: tab.value, new: 1 } })
    if (link.url && win) win.location.href = link.url
    else if (link.url) window.location.assign(link.url)
    else win?.close()
  }
  catch {
    win?.close()
    error.value = t('cabinet.error')
  }
  finally {
    openingNew.value = false
  }
}
const richWarning = computed(() => editing.value && editing.value !== 'new' && LANGS.some(l => isRich(orig.body[l])))

const errMessage = (e: unknown) => (e as { data?: { data?: { message?: string } } })?.data?.data?.message || t('cabinet.posts.error')

async function upload(ev: Event) {
  const file = (ev.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  error.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await $fetch<{ doc: { id: number, url: string } }>('/api/me/cms/media', { method: 'POST', body: fd })
    form.cover = { id: res.doc.id, url: res.doc.url }
  }
  catch (e) {
    error.value = errMessage(e)
  }
  finally {
    uploading.value = false
    ;(ev.target as HTMLInputElement).value = ''
  }
}

async function save() {
  if (!form.title.uz.trim()) {
    error.value = t('cabinet.posts.needTitle')
    return
  }
  busy.value = true
  error.value = ''
  const body: Record<string, unknown> = {
    title: form.title,
    excerpt: form.excerpt,
    // O'zgarmagan tilning asl HTML'i qaytariladi (murakkab formatlash yo'qolmasin), o'zgargani — oddiy abzatslarga aylantiriladi
    body: Object.fromEntries(LANGS.map(l => [l, form.body[l] === orig.bodyText[l] ? orig.body[l] : textToHtml(form.body[l])])),
    status: form.status,
    cover: form.cover?.id ?? null,
  }
  if (tab.value === 'events') Object.assign(body, { startsAt: fromLocal(form.startsAt), endsAt: fromLocal(form.endsAt), location: { uz: form.location } })
  try {
    if (editing.value === 'new') await $fetch('/api/me/cms/posts', { method: 'POST', body: { ...body, type: tab.value } })
    else if (editing.value) await $fetch(`/api/me/cms/posts/${editing.value.id}`, { method: 'PATCH', body })
    editing.value = null
    await refresh()
  }
  catch (e) {
    error.value = errMessage(e)
  }
  finally {
    busy.value = false
  }
}

async function remove(doc: CabinetPostDoc) {
  if (!confirm(t('cabinet.posts.confirm'))) return
  busy.value = true
  error.value = ''
  try {
    await $fetch(`/api/me/cms/posts/${doc.id}`, { method: 'DELETE' })
    await refresh()
  }
  catch (e) {
    error.value = errMessage(e)
  }
  finally {
    busy.value = false
  }
}

const fmt = (d: string | null) => (d ? new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : '')
</script>

<template>
  <section class="rounded-[28px] border border-line bg-white p-5 sm:p-6" :aria-label="t('cabinet.posts.title')">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="font-display text-[28px] font-semibold text-ink">{{ t('cabinet.posts.title') }}</h2>
        <p class="mt-1 text-[15px] text-muted">{{ t('cabinet.posts.desc') }}</p>
      </div>
      <button v-if="!editing" type="button" class="inline-flex items-center gap-1.5 rounded-full bg-brand-700 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-900" :disabled="openingNew" @click="addInAdmin">
        <Icon name="lucide:plus" class="size-4" />{{ t(`cabinet.posts.add.${tab}`) }}<Icon name="lucide:arrow-up-right" class="size-4" />
      </button>
    </div>

    <div v-if="types.length > 1 && !editing" role="tablist" class="mt-4 inline-flex flex-wrap rounded-full bg-brand-50 p-1">
      <button v-for="k in types" :key="k" type="button" role="tab" :aria-selected="tab === k"
              class="rounded-full px-4 py-1.5 text-sm font-semibold transition-colors" :class="tab === k ? 'bg-white text-brand-900 shadow-sm' : 'text-muted'" @click="tab = k">
        {{ t(`cabinet.posts.types.${k}`) }}
      </button>
    </div>

    <p v-if="error" role="alert" class="mt-3 rounded-xl bg-[#fdecec] px-4 py-2.5 text-sm text-[#8e1b1b]">{{ error }}</p>

    <!-- Forma -->
    <form v-if="editing" class="mt-4 grid gap-4 rounded-2xl bg-brand-50 p-4" @submit.prevent="save">
      <div role="tablist" class="inline-flex w-fit rounded-full bg-white p-1">
        <button v-for="l in LANGS" :key="l" type="button" role="tab" :aria-selected="lang === l" class="rounded-full px-3.5 py-1 text-sm font-semibold uppercase transition-colors"
                :class="lang === l ? 'bg-brand-700 text-white' : 'text-muted'" @click="lang = l">
          {{ l }}<span v-if="l === 'uz'" aria-hidden="true"> *</span>
        </button>
      </div>
      <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.posts.name') }}
        <input v-model="form.title[lang]" :required="lang === 'uz'" maxlength="300" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
      </label>
      <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.posts.excerpt') }}
        <textarea v-model="form.excerpt[lang]" rows="2" maxlength="600" class="rounded-xl border border-line bg-white px-3 py-2 font-normal" />
      </label>
      <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.posts.text') }}
        <textarea v-model="form.body[lang]" rows="10" class="rounded-xl border border-line bg-white px-3 py-2 font-normal" />
        <span class="text-xs font-normal text-muted">{{ t('cabinet.posts.textHint') }}</span>
        <span v-if="richWarning" class="text-xs font-normal text-[#8a5a00]">{{ t('cabinet.posts.rich') }}</span>
      </label>

      <div v-if="tab === 'events'" class="grid gap-3 sm:grid-cols-3">
        <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.posts.starts') }}
          <input v-model="form.startsAt" type="datetime-local" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
        </label>
        <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.posts.ends') }}
          <input v-model="form.endsAt" type="datetime-local" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
        </label>
        <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.posts.place') }}
          <input v-model="form.location" maxlength="200" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
        </label>
      </div>

      <div class="grid items-start gap-3 sm:grid-cols-2">
        <div class="grid gap-1 text-sm font-medium text-ink">
          {{ t('cabinet.posts.cover') }}
          <div class="flex items-center gap-3">
            <img v-if="form.cover" :src="form.cover.url" alt="" loading="lazy" class="h-16 w-24 rounded-lg object-cover">
            <label class="inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-line bg-white px-4 py-2 text-sm font-semibold text-brand-900 hover:bg-brand-50">
              <Icon name="lucide:image-up" class="size-4" />{{ uploading ? t('cabinet.posts.uploading') : t('cabinet.posts.pick') }}
              <input type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" :disabled="uploading" @change="upload">
            </label>
            <button v-if="form.cover" type="button" class="text-sm text-muted hover:text-[#b42318]" @click="form.cover = null">{{ t('cabinet.posts.removeCover') }}</button>
          </div>
        </div>
        <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.posts.status') }}
          <select v-model="form.status" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
            <option value="published">{{ t('cabinet.posts.published') }}</option>
            <option value="draft">{{ t('cabinet.posts.draft') }}</option>
          </select>
        </label>
      </div>

      <div class="flex justify-end gap-2">
        <button type="button" class="rounded-full px-4 py-2 text-sm font-semibold text-muted hover:bg-white" @click="editing = null">{{ t('cabinet.posts.cancel') }}</button>
        <button type="submit" :disabled="busy || uploading" class="rounded-full bg-brand-700 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-900 disabled:opacity-60">{{ t('cabinet.posts.save') }}</button>
      </div>
    </form>

    <!-- Ro'yxat -->
    <template v-else>
      <ul v-if="data.docs.length" class="mt-4 grid gap-2">
        <li v-for="d in data.docs" :key="d.id" class="flex items-start gap-3 rounded-2xl border border-line px-4 py-3">
          <div class="min-w-0 flex-1">
            <p class="font-medium text-ink">{{ d.title.uz || '—' }}</p>
            <p class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted">
              <span class="rounded-full px-2 py-0.5 font-semibold" :class="d.status === 'published' ? 'bg-brand-50 text-brand-700' : 'bg-[#fff6db] text-[#8a5a00]'">{{ t(`cabinet.posts.${d.status}`) }}</span>
              <span v-if="d.publishedAt">{{ fmt(d.publishedAt) }}</span>
              <span v-if="!d.own">{{ t('cabinet.posts.foreign') }}</span>
            </p>
          </div>
          <template v-if="d.own">
            <button type="button" :aria-label="t('cabinet.posts.edit')" :disabled="busy" class="grid size-8 shrink-0 place-items-center rounded-full text-muted transition-colors hover:bg-brand-50 hover:text-brand-700" @click="open(d)">
              <Icon name="lucide:pencil" class="size-4" />
            </button>
            <button type="button" :aria-label="t('cabinet.posts.remove')" :disabled="busy" class="grid size-8 shrink-0 place-items-center rounded-full text-muted transition-colors hover:bg-brand-50 hover:text-[#b42318]" @click="remove(d)">
              <Icon name="lucide:trash-2" class="size-4" />
            </button>
          </template>
        </li>
      </ul>
      <p v-else-if="status !== 'pending'" class="mt-6 rounded-2xl bg-brand-50 px-4 py-6 text-center text-sm text-muted">{{ t('cabinet.posts.empty') }}</p>

      <div v-if="data.totalPages > 1" class="mt-4 flex items-center justify-center gap-3 text-sm">
        <button type="button" :disabled="page <= 1" class="rounded-full border border-line px-4 py-1.5 font-semibold disabled:opacity-40" @click="page--">{{ t('cabinet.posts.prev') }}</button>
        <span class="text-muted">{{ page }} / {{ data.totalPages }}</span>
        <button type="button" :disabled="page >= data.totalPages" class="rounded-full border border-line px-4 py-1.5 font-semibold disabled:opacity-40" @click="page++">{{ t('cabinet.posts.next') }}</button>
      </div>
    </template>
  </section>
</template>
