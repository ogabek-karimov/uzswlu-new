<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import ImageField from '@/components/ImageField.vue'
import LangTabs from '@/components/LangTabs.vue'
import PdfAttachments from '@/components/PdfAttachments.vue'
import RichEditor from '@/components/RichEditor.vue'
import SdgPicker from '@/components/SdgPicker.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'
import { api, ApiError, type I18n, type MediaDoc, type Paginated } from '@/lib/api'
import { auth, initials } from '@/lib/auth'
import { LANGS, type Lang, POST_TYPES, type PostType, SITE_URL } from '@/lib/constants'
import { dateTime, fromInputs, longDateTime, toInputs } from '@/lib/format'
import { type Attachment, langFill, type Post, postState, STATE_BADGE } from '@/lib/posts'

const route = useRoute()
const router = useRouter()
const id = computed(() => (route.params.id ? Number(route.params.id) : null))

const empty = (): I18n => ({ uz: '', ru: '', en: '', zh: '' })
type Category = { id: number; name: I18n }

const form = reactive({
  type: (route.params.type as PostType) ?? 'news',
  title: empty(),
  excerpt: empty(),
  body: empty(),
  location: empty(),
  slug: '',
  category: null as number | null,
  sdg: 0,
  cover: null as MediaDoc | null,
  coverByLang: { ru: null as MediaDoc | null, en: null as MediaDoc | null, zh: null as MediaDoc | null },
  gallery: [] as MediaDoc[],
  attachments: [] as Attachment[],
  tags: { uz: [] as string[], ru: [] as string[], en: [] as string[], zh: [] as string[] },
  status: 'draft' as 'draft' | 'published',
  publishedAt: null as string | null,
  hidden: false,
  startsAt: null as string | null,
  endsAt: null as string | null,
})
const authorName = ref(auth.user.value?.name ?? '')
const authorRole = ref(auth.user.value?.position ?? '')
const lang = ref<Lang>('uz')
const categories = ref<Category[]>([])
const when = ref<'now' | 'custom'>('now')
const pub = reactive(toInputs())
const evStart = reactive(toInputs())
const evEnd = reactive({ date: '', time: '' })
const tagInput = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const savedAt = ref<string | null>(null)
const dirty = ref(false)
let ready = false

const meta = computed(() => POST_TYPES.find(t => t.value === form.type)!)
const fill = computed(() => Object.fromEntries(LANGS.map(l => [l.code, langFill(form, l.code)])) as Record<Lang, 0 | 0.5 | 1>)
const customAt = computed(() => fromInputs(pub.date, pub.time))
const isFuture = computed(() => when.value === 'custom' && !!customAt.value && new Date(customAt.value).getTime() > Date.now())
const shownAt = computed(() => (when.value === 'custom' ? customAt.value : form.status === 'published' && form.publishedAt ? form.publishedAt : new Date().toISOString()))
const langLabel = computed(() => LANGS.find(l => l.code === lang.value)!.label)

const NOTES: Record<Lang, (f: 0 | 0.5 | 1) => [string, string]> = {
  uz: () => ['Özbekça — majburiy. Rus, ingliz va xitoy tillarini ham töldiring: tarjimasi yöq til saytida post çiqmaydi.', 'bg-brand-50 text-brand-800'],
  ru: f => f ? ['Rusça töldirilgan — rus saytida çiqadi.', 'bg-[#DDFBF0] text-[#0B5A43]'] : ['Rusça böş — bu post rus tilidagi saytda körinmaydi.', 'bg-[#F1F0F5] text-muted'],
  en: f => f ? ['Inglizça töldirilgan — ingliz saytida çiqadi.', 'bg-[#DDFBF0] text-[#0B5A43]'] : ['Inglizça böş — bu post ingliz tilidagi saytda körinmaydi.', 'bg-[#F1F0F5] text-muted'],
  zh: f => f ? ['Xitoyça töldirilgan — xitoy saytida çiqadi.', 'bg-[#DDFBF0] text-[#0B5A43]'] : ['Xitoyça böş — bu post xitoy tilidagi saytda körinmaydi.', 'bg-[#F1F0F5] text-muted'],
}
const note = computed(() => NOTES[lang.value](fill.value[lang.value]))

async function load() {
  categories.value = (await api.get<Paginated<Category>>('/categories', { limit: 100, sort: 'key' })).docs
  if (!id.value) { ready = true; return }
  loading.value = true
  try {
    const p = await api.get<Post>(`/posts/${id.value}`, { depth: 1 })
    form.type = p.type
    for (const key of ['title', 'excerpt', 'body', 'location'] as const) Object.assign(form[key], empty(), p[key] ?? {})
    form.slug = p.slug ?? ''
    form.category = p.category && typeof p.category === 'object' ? p.category.id : (p.category as number | null) ?? null
    form.sdg = p.sdg ?? 0
    form.cover = typeof p.cover === 'object' ? p.cover : null
    form.coverByLang = {
      ru: typeof p.coverByLang?.ru === 'object' ? p.coverByLang.ru : null,
      en: typeof p.coverByLang?.en === 'object' ? p.coverByLang.en : null,
      zh: typeof p.coverByLang?.zh === 'object' ? p.coverByLang.zh : null,
    }
    form.gallery = (p.gallery ?? []).filter((m): m is MediaDoc => typeof m === 'object')
    form.attachments = (p.attachments ?? []).map(a => ({ ...a, title: { ...empty(), ...(a.title ?? {}) } }))
    form.tags = { uz: [], ru: [], en: [], zh: [], ...(p.tags ?? {}) } as typeof form.tags
    form.status = p.status
    form.publishedAt = p.publishedAt ?? null
    form.hidden = !!p.hidden
    form.startsAt = p.startsAt ?? null
    form.endsAt = p.endsAt ?? null
    Object.assign(pub, toInputs(p.publishedAt))
    if (p.startsAt) Object.assign(evStart, toInputs(p.startsAt))
    if (p.endsAt) Object.assign(evEnd, toInputs(p.endsAt))
    if (p.publishedAt && p.status === 'published') when.value = 'custom'
    if (p.author && typeof p.author === 'object') { authorName.value = p.author.name; authorRole.value = p.author.position ?? '' }
  }
  catch (e) {
    error.value = e instanceof ApiError && e.status === 404 ? 'Post topilmadi.' : 'Postni yuklab bölmadi.'
  }
  finally {
    loading.value = false
    setTimeout(() => { ready = true }, 0)
  }
}

onMounted(load)
watch(form, () => { if (ready) dirty.value = true }, { deep: true })
watch(() => route.params.type, (t) => { if (!id.value && t) form.type = t as PostType })

function addTag() {
  const t = tagInput.value.trim().replace(/,$/, '')
  if (t && !form.tags[lang.value].includes(t)) form.tags[lang.value] = [...form.tags[lang.value], t]
  tagInput.value = ''
}

function payload(status: 'draft' | 'published') {
  let publishedAt = form.publishedAt
  if (status === 'published') publishedAt = when.value === 'custom' ? customAt.value : (form.status === 'published' && form.publishedAt ? form.publishedAt : new Date().toISOString())
  else if (when.value === 'custom') publishedAt = customAt.value
  return {
    type: form.type,
    title: form.title,
    excerpt: form.excerpt,
    body: form.body,
    location: form.location,
    slug: form.slug || undefined,
    category: form.category,
    sdg: form.sdg,
    cover: form.cover?.id ?? null,
    coverByLang: { ru: form.coverByLang.ru?.id ?? null, en: form.coverByLang.en?.id ?? null, zh: form.coverByLang.zh?.id ?? null },
    gallery: form.gallery.map(m => m.id),
    attachments: form.attachments.map(a => ({ file: typeof a.file === 'object' ? a.file.id : a.file, title: a.title, display: a.display, height: a.height ?? 680 })),
    tags: form.tags,
    status,
    publishedAt,
    hidden: form.hidden,
    startsAt: form.type === 'events' ? fromInputs(evStart.date, evStart.time) : null,
    endsAt: form.type === 'events' ? fromInputs(evEnd.date, evEnd.time) : null,
  }
}

async function save(status: 'draft' | 'published') {
  error.value = ''
  if (!form.title.uz?.trim()) {
    lang.value = 'uz'
    error.value = 'Özbekça sarlavha majburiy.'
    return
  }
  saving.value = true
  try {
    const data = payload(status)
    const res = id.value
      ? await api.patch<{ doc: Post }>(`/posts/${id.value}`, data)
      : await api.post<{ doc: Post }>('/posts', data)
    form.status = res.doc.status
    form.publishedAt = res.doc.publishedAt ?? null
    form.slug = res.doc.slug ?? form.slug
    savedAt.value = new Date().toISOString()
    dirty.value = false
    if (!id.value) router.replace(`/postlar/${res.doc.type}/${res.doc.id}`)
  }
  catch (e) {
    error.value = e instanceof ApiError ? e.message : 'Saqlab bölmadi.'
  }
  finally {
    saving.value = false
  }
}

onBeforeRouteLeave(() => !dirty.value || window.confirm('Saqlanmagan özgarişlar bor. Sahifadan çiqasizmi?'))

const state = computed(() => postState({ status: form.status, publishedAt: form.publishedAt }))
const publishLabel = computed(() => (!form.hidden && isFuture.value ? 'Rejalaştiriş' : form.status === 'published' ? 'Saqlaş va naşr' : 'Naşr qiliş'))
const siteLink = computed(() => (form.slug ? `${SITE_URL}${lang.value === 'uz' ? '' : `/${lang.value}`}/${meta.value.path}/${form.slug}` : ''))
</script>

<template>
  <div class="flex flex-col gap-5">
    <!-- Sarlavha va asosiy tugmalar -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <nav aria-label="Yöl" class="text-[13px] text-muted">
          <RouterLink to="/">Boşqaruv paneli</RouterLink> /
          <RouterLink :to="`/postlar/${form.type}`">{{ meta.plural }}</RouterLink> /
          <span aria-current="page" class="text-ink">{{ id ? 'Tahrirlaş' : 'Yangi' }}</span>
        </nav>
        <h1 class="mt-2 text-[28px] font-bold tracking-tight">{{ id ? (form.title.uz || 'Post') : meta.newLabel }}</h1>
      </div>
      <div class="flex flex-wrap items-center gap-2.5">
        <span v-if="id" class="chip" :class="STATE_BADGE[state].cls">{{ STATE_BADGE[state].label }}</span>
        <span v-if="savedAt" class="flex items-center gap-1.5 text-[13px] text-subtle"><span class="size-[7px] rounded-full bg-[#12B76A]" />Saqlandi · {{ dateTime(savedAt).split(' · ')[1] }}</span>
        <span v-else-if="dirty" class="text-[13px] text-[#8A5A00]">Saqlanmagan özgarişlar bor</span>
        <a v-if="id && state === 'published' && !form.hidden && siteLink" :href="siteLink" target="_blank" rel="noopener" class="btn-ghost"><Icon name="external" :size="16" />Saytda köriş</a>
        <button type="button" class="btn-ghost" :disabled="saving" @click="save('draft')">Qoralama saqlaş</button>
        <button type="button" class="btn-primary px-5" :disabled="saving" @click="save('published')">{{ saving ? 'Saqlanmoqda…' : publishLabel }}</button>
      </div>
    </div>

    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{{ error }}</p>
    <p v-if="loading" class="text-muted">Yuklanmoqda…</p>

    <div v-else class="flex flex-wrap items-start gap-5">
      <!-- Chap ustun: mazmun -->
      <div class="flex min-w-0 flex-[999_1_560px] flex-col gap-5">
        <section class="card p-[22px]">
          <h2 class="text-base font-bold">Turi</h2>
          <div role="radiogroup" aria-label="Post turi" class="mt-3.5 grid gap-2.5 sm:grid-cols-3">
            <button
              v-for="t in POST_TYPES" :key="t.value" type="button" role="radio" :aria-checked="form.type === t.value"
              class="flex min-h-16 items-center gap-3 rounded-[14px] px-3.5 py-3 text-left"
              :class="form.type === t.value ? 'border-2 border-brand-700 bg-brand-50' : 'border border-field bg-white'"
              @click="form.type = t.value"
            >
              <Icon :name="t.value" :size="22" :class="form.type === t.value ? 'text-brand-700' : 'text-subtle'" />
              <span><span class="block text-[15px] font-bold">{{ t.label }}</span><span class="mt-0.5 block text-xs text-muted">{{ t.value === 'events' ? 'Taqvimga ham qöşiladi' : `${t.plural} bölimi` }}</span></span>
            </button>
          </div>
        </section>

        <section class="card overflow-hidden">
          <div class="border-b border-line bg-[#FAF9FD] px-3.5 pt-2.5"><LangTabs v-model="lang" :fill="fill" /></div>
          <div class="flex flex-col gap-[18px] p-[22px]">
            <p class="rounded-xl px-3.5 py-2.5 text-[13px] leading-relaxed" :class="note[1]">{{ note[0] }}</p>
            <div>
              <label for="p-title" class="label text-[13px]! text-ink!">Sarlavha · {{ langLabel }} <span v-if="lang === 'uz'" class="text-red-700">*</span></label>
              <input id="p-title" v-model="form.title[lang]" class="field h-12! text-[17px]! font-semibold" :placeholder="lang === 'zh' ? '中文标题' : lang === 'ru' ? 'Заголовок на русском' : lang === 'en' ? 'Title in English' : 'Masalan: ÖzDJTUda xalqaro anjuman bölib ötdi'">
              <p class="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-subtle">Manzil:
                <span class="font-semibold text-brand-700">{{ SITE_URL.replace(/^https?:\/\//, '') }}/{{ meta.path }}/</span>
                <input v-model="form.slug" aria-label="Manzil (slug)" class="min-w-[160px] flex-1 rounded-md border border-transparent px-1 font-semibold text-brand-700 outline-none hover:border-field focus:border-brand-700" placeholder="özbekça sarlavhadan öz-özidan">
              </p>
            </div>
            <div>
              <label for="p-excerpt" class="label text-[13px]! text-ink!">Qisqa tavsif · {{ langLabel }} <span class="font-normal text-subtle">— kartoçkada va ijtimoiy tarmoqlarda çiqadi</span></label>
              <textarea id="p-excerpt" v-model="form.excerpt[lang]" rows="3" class="field h-auto! py-3 leading-relaxed" placeholder="Bir-ikki gapda: nima bölib ötdi?" />
            </div>
            <div>
              <span class="label text-[13px]! text-ink!">Matn · {{ langLabel }}</span>
              <RichEditor v-model="form.body[lang]!" placeholder="Matnni şu yerga yozing yoki Word’dan nusxa oling…" />
            </div>
          </div>
        </section>

        <section v-if="form.type === 'events'" class="card p-[22px]">
          <h2 class="text-base font-bold">Tadbir vaqti va joyi</h2>
          <p class="mt-1 text-[13px] text-muted">Saytdagi tadbirlar taqvimiga öz-özidan qöşiladi. Vaqt 24 soatlik formatda.</p>
          <div class="mt-4 grid gap-3.5 sm:grid-cols-2">
            <div><span class="label">Boşlaniş</span><div class="flex gap-2"><input v-model="evStart.date" type="date" class="field" aria-label="Boşlaniş sanasi"><input v-model="evStart.time" type="time" step="300" class="field w-32!" aria-label="Boşlaniş vaqti"></div></div>
            <div><span class="label">Tugaş (ixtiyoriy)</span><div class="flex gap-2"><input v-model="evEnd.date" type="date" class="field" aria-label="Tugaş sanasi"><input v-model="evEnd.time" type="time" step="300" class="field w-32!" aria-label="Tugaş vaqti"></div></div>
          </div>
          <div class="mt-3.5"><label for="p-place" class="label">Ötkaziladigan joy · {{ langLabel }}</label><input id="p-place" v-model="form.location[lang]" class="field" placeholder="Masalan: Boş bino, 2-qavat, Majlislar zali"></div>
        </section>

        <!-- Rasmlar: asosiy rasm (4 til) va galereya bitta kartada — chalkashmasligi uchun -->
        <section class="card p-[22px]">
          <h2 class="text-base font-bold">Rasmlar</h2>
          <p class="mt-3.5 text-sm font-bold">1. Asosiy rasm <span class="font-medium text-subtle">— sarlavha ustida va kartoçkada çiqadi, har til uçun</span></p>
          <div class="mt-2.5 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            <ImageField v-model="form.cover" badge="UZ · asosiy" />
            <ImageField v-for="l in (['ru', 'en', 'zh'] as const)" :key="l" v-model="form.coverByLang[l]" :badge="l.toUpperCase()" />
          </div>
          <p class="mt-2 text-xs text-subtle">Böş qolgan tilda özbekça rasm körsatiladi. Rasm yuklanganda öz-özidan WebP’ga ögiriladi.</p>

          <div class="mt-5 flex items-baseline justify-between gap-2.5 border-t border-[#F0EEF6] pt-[18px]">
            <p class="text-sm font-bold">2. Galereya <span class="font-medium text-subtle">— maqola ostidagi qöşimça rasmlar</span></p>
            <span class="text-[13px] text-subtle">{{ form.gallery.length }} ta rasm</span>
          </div>
          <div class="mt-2.5 grid grid-cols-3 gap-2.5 sm:grid-cols-5">
            <div v-for="(m, i) in form.gallery" :key="m.id" class="relative aspect-[4/3] overflow-hidden rounded-xl bg-brand-100">
              <img :src="m.sizes?.thumb?.url ?? m.url ?? ''" alt="" class="size-full object-cover">
              <button type="button" aria-label="Rasmni olib taşlaş" class="absolute top-1.5 right-1.5 grid size-[26px] place-items-center rounded-full bg-night/60 text-white" @click="form.gallery.splice(i, 1)"><Icon name="x" :size="13" /></button>
            </div>
            <ImageField :model-value="null" compact label="Rasm qöşiş" @update:model-value="m => m && form.gallery.push(m)" />
          </div>
        </section>

        <section class="card p-[22px]">
          <PdfAttachments v-model="form.attachments" :lang="lang" />
        </section>
      </div>

      <!-- O'ng ustun -->
      <aside class="flex min-w-0 flex-[1_1_340px] flex-col gap-5">
        <section class="card p-[22px]">
          <h2 class="text-base font-bold">Naşr</h2>
          <div role="radiogroup" aria-label="Qaçon naşr qilinadi" class="mt-3.5 grid grid-cols-2 gap-1 rounded-xl bg-canvas p-1">
            <button v-for="w in [['now', 'Hozir'], ['custom', 'Boşqa sana va vaqt']] as const" :key="w[0]" type="button" role="radio" :aria-checked="when === w[0]" class="h-[38px] rounded-[9px] text-[13px] font-semibold" :class="when === w[0] ? 'bg-white text-ink shadow-sm' : 'text-muted'" @click="when = w[0]">{{ w[1] }}</button>
          </div>
          <div v-if="when === 'custom'" class="mt-3.5 grid grid-cols-[1fr_auto] gap-2.5">
            <div><label for="p-date" class="label">Sana</label><input id="p-date" v-model="pub.date" type="date" class="field"></div>
            <div><label for="p-time" class="label">Vaqt (24 soat)</label><input id="p-time" v-model="pub.time" type="time" step="60" class="field w-32!"></div>
          </div>
          <p class="mt-3 rounded-[10px] px-3 py-2.5 text-[13px] leading-relaxed" :class="when === 'now' ? 'bg-canvas text-muted' : isFuture ? 'bg-[#FEF3DC] text-[#6B4600]' : 'bg-brand-50 text-brand-800'">
            <template v-if="when === 'now'">Naşr tugmasi bosilgan vaqt yoziladi (24 soatlik).</template>
            <template v-else-if="isFuture">Kelajak vaqt: {{ dateTime(customAt) }} da öz-özidan saytda çiqadi — kompyuter yoqiq turişi şart emas.</template>
            <template v-else>Ötgan vaqt: post darhol çiqadi, saytda {{ dateTime(customAt) }} deb körinadi va röyxatda şu sana örnida turadi.</template>
          </p>

          <div class="mt-3.5 flex items-center justify-between gap-3 border-t border-[#F0EEF6] pt-3.5">
            <span><span class="block text-sm font-semibold">Saytda körinadi</span><span class="block text-xs text-subtle">Öçirib qöysangiz — vaqtinça yaşiriladi</span></span>
            <ToggleSwitch :model-value="!form.hidden" label="Saytda körinadi" on="#0E7A5A" @update:model-value="v => form.hidden = !v" />
          </div>
          <p v-if="form.hidden" class="mt-2.5 rounded-[10px] bg-[#EEF0F6] px-3 py-2.5 text-[13px] leading-relaxed text-[#3D4466]"><b>Yaşirilgan.</b> Post saytda, qidiruvda va BRM sahifasida körinmaydi, lekin öçirilmaydi.</p>

          <div class="mt-4 border-t border-[#F0EEF6] pt-4">
            <p class="text-[13px] font-semibold">Muallif</p>
            <div class="mt-2.5 flex items-center gap-3">
              <span class="grid size-11 shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-700 to-night font-bold text-mint">{{ initials(authorName) }}</span>
              <span class="leading-snug"><b class="block text-sm">{{ authorName }}</b><span class="text-xs text-muted">{{ authorRole || 'Lavozim profil sahifasida kiritiladi' }}</span></span>
            </div>
            <div class="mt-3.5 rounded-2xl border border-dashed border-[#E1DCCF] bg-[#FAF8F4] px-3.5 py-3">
              <p class="text-[11px] font-bold tracking-[0.12em] text-subtle uppercase">Saytda şunday körinadi</p>
              <p class="mt-2 flex flex-wrap items-center gap-2 text-[13px] text-muted">
                <span class="grid size-[26px] place-items-center rounded-full bg-brand-800 text-[10px] font-bold text-mint">{{ initials(authorName) }}</span>
                <b class="text-ink">{{ authorName }}</b><span aria-hidden="true">·</span><span>{{ longDateTime(shownAt) }}</span>
              </p>
            </div>
          </div>
        </section>

        <section class="card p-[22px]">
          <h2 class="text-base font-bold">BRM — barqaror rivojlaniş maqsadi</h2>
          <p class="mt-1 text-[13px] text-muted">Bitta maqsadni tanlang yoki böş qoldiring.</p>
          <SdgPicker v-model="form.sdg" />
        </section>

        <section class="card p-[22px]">
          <h2 class="text-base font-bold">Kategoriya va teglar</h2>
          <label for="p-cat" class="label mt-3.5">Kategoriya</label>
          <select id="p-cat" v-model="form.category" class="field">
            <option :value="null">— tanlanmagan —</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name.uz }}</option>
          </select>
          <span class="label mt-3.5">Teglar · {{ langLabel }}</span>
          <div class="flex flex-wrap gap-1.5 rounded-xl border border-field p-2">
            <span v-for="(t, i) in form.tags[lang]" :key="t" class="inline-flex items-center gap-1 rounded-full bg-[#F0EEF6] py-1.5 pr-1.5 pl-2.5 text-[13px] font-semibold">
              {{ t }} <button type="button" :aria-label="`${t} tegini olib taşlaş`" class="grid size-5 place-items-center rounded-full hover:bg-white" @click="form.tags[lang].splice(i, 1)"><Icon name="x" :size="12" /></button>
            </span>
            <input v-model="tagInput" aria-label="Yangi teg" placeholder="Teg qöşiş… (Enter)" class="min-w-[100px] flex-1 bg-transparent px-1 text-[13px] outline-none" @keydown.enter.prevent="addTag" @keydown.,.prevent="addTag">
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>
