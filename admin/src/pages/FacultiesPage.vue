<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { LANGS, type Lang, SITE_URL } from '@/lib/constants'
import { hemisBadge, useHemis } from '@/lib/hemis'
import { mediaUrl } from '@/lib/posts'
import { useSortable } from '@/lib/sortable'
import I18nFields from '@/components/I18nFields.vue'

// Fakultetlar: matn, logo va aloqa — shu yerda; dekan, kafedralar, sonlar — HEMIS'dan
type Faculty = { id: number; slug: string; name: I18n; logo?: MediaDoc | number | null; cover?: MediaDoc | number | null; about?: I18n; phone?: string | null; email?: string | null; address?: I18n; mapUrl?: string | null; order?: number | null }

const COLORS = ['#382B85', '#2A2066', '#4C3FA0', '#6D5FD3', '#1C1548', '#0A97D9', '#C5192D', '#DD1367', '#0E7A5A', '#FD6925', '#8C88A0']
const list = ref<Faculty[]>([])
const sel = ref<number | null>(null)
const lang = ref<Lang>('uz')
const saving = ref(false)
const saved = ref(false)
const error = ref('')
const hemis = useHemis()
const badge = computed(() => hemisBadge(hemis.value))
const { bind, over } = useSortable(list, 'faculties')

const form = reactive({ name: {} as I18n, about: {} as I18n, address: {} as I18n, phone: '', email: '', mapUrl: '', logo: null as MediaDoc | null, cover: null as MediaDoc | null })
const current = computed(() => list.value.find(f => f.id === sel.value) ?? null)
const h = computed(() => hemis.value?.faculties.find(f => f.slug === current.value?.slug) ?? null)
const hOf = (slug: string) => hemis.value?.faculties.find(f => f.slug === slug)
const obj = (v: unknown) => (v && typeof v === 'object' ? v as MediaDoc : null)

async function load() {
  list.value = (await api.get<Paginated<Faculty>>('/faculties', { sort: 'order', limit: 100, depth: 1 })).docs
  const q = new URLSearchParams(location.search).get('f')
  if (sel.value === null) pick(list.value.find(f => f.slug === q)?.id ?? list.value[0]?.id ?? null)
}
onMounted(load)

function pick(id: number | null) {
  sel.value = id
  saved.value = false
  error.value = ''
  const f = list.value.find(x => x.id === id)
  if (!f) return
  Object.assign(form, { name: { ...f.name }, about: { ...(f.about ?? {}) }, address: { ...(f.address ?? {}) }, phone: f.phone ?? '', email: f.email ?? '', mapUrl: f.mapUrl ?? '', logo: obj(f.logo), cover: obj(f.cover) })
}

async function save() {
  if (!current.value || !form.name.uz?.trim()) { error.value = 'Özbekça nomi majburiy'; return }
  saving.value = true
  error.value = ''
  try {
    await api.patch(`/faculties/${current.value.id}`, {
      name: form.name, about: form.about, address: form.address, phone: form.phone.trim() || null, email: form.email.trim() || null, mapUrl: form.mapUrl.trim() || null,
      logo: form.logo?.id ?? null, cover: form.cover?.id ?? null,
    })
    await load()
    pick(sel.value)
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

// Logo va muqova: tanlangan zahoti yuklanadi, "Saqlash" bilan fakultetga biriktiriladi
const logoInput = ref<HTMLInputElement>()
const coverInput = ref<HTMLInputElement>()
const uploading = ref<'' | 'logo' | 'cover'>('')
async function onImage(e: Event, kind: 'logo' | 'cover') {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = kind
  try {
    form[kind] = await uploadMedia(file, { folder: 'logos' })
  }
  catch (err) {
    error.value = (err as Error).message
  }
  finally {
    uploading.value = ''
    ;(e.target as HTMLInputElement).value = ''
  }
}
const color = (i: number) => COLORS[i % COLORS.length]
const idx = computed(() => list.value.findIndex(f => f.id === sel.value))
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Fakultetlar</h1>
        <p class="mt-1.5 text-[15px] text-muted">Matn, logo va aloqa — şu yerda. Dekan, kafedralar, talaba va öqituvçilar soni — HEMIS’dan öz-özidan.</p>
      </div>
      <span class="flex items-center gap-2 rounded-full px-3 py-2 text-[13px] font-semibold" :class="badge.ok ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#FEF3DC] text-[#8A5A00]'">
        <span class="size-[7px] rounded-full" :class="badge.ok ? 'bg-[#12B76A]' : 'bg-[#F79009]'" />{{ badge.text }}
      </span>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <aside class="card min-w-0 flex-[1_1_300px] p-3 xl:max-w-[340px]">
        <ul class="flex flex-col gap-0.5">
          <li v-for="(f, i) in list" :key="f.id" v-bind="bind(i)" :class="over === i && 'rounded-xl ring-2 ring-mint'">
            <button
              type="button" :aria-current="sel === f.id ? 'page' : undefined"
              class="flex min-h-[52px] w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left text-[13px]"
              :class="sel === f.id ? 'bg-brand-50 font-semibold shadow-[inset_3px_0_0_var(--color-brand-700)]' : 'font-medium'" @click="pick(f.id)"
            >
              <span aria-hidden="true" title="Surib tartiblaş" class="cursor-grab tracking-[-2px] text-[#C9C5D6]">⋮⋮</span>
              <img v-if="mediaUrl(f.logo)" :src="mediaUrl(f.logo)!" alt="" class="size-[34px] shrink-0 rounded-full bg-white object-contain ring-1 ring-line" draggable="false">
              <span v-else aria-hidden="true" class="grid size-[34px] shrink-0 place-items-center rounded-full text-[11px] font-bold text-white" :style="{ background: color(i) }">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="min-w-0 flex-1 leading-tight">
                <span class="block">{{ f.name.uz }}</span>
                <span v-if="hOf(f.slug)" class="block text-[11px] font-medium text-subtle">{{ hOf(f.slug)!.stats.departments }} kafedra · {{ hOf(f.slug)!.stats.students.toLocaleString('ru-RU') }} talaba</span>
              </span>
            </button>
          </li>
        </ul>
      </aside>

      <div v-if="current" class="flex min-w-0 flex-[999_1_520px] flex-col gap-[18px]">
        <section class="card overflow-hidden p-0!">
          <div class="relative h-[120px] overflow-hidden" :style="{ background: color(idx) }">
            <img v-if="mediaUrl(form.cover, 'hero')" :src="mediaUrl(form.cover, 'hero')!" alt="" class="absolute inset-0 size-full object-cover">
            <span aria-hidden="true" class="absolute -top-[120px] -right-[60px] size-[320px] rounded-full border-[40px] border-white/8" />
            <input ref="coverInput" type="file" accept="image/*" class="hidden" @change="onImage($event, 'cover')">
            <span class="absolute right-3.5 bottom-3.5 left-32 flex flex-wrap justify-end gap-1.5">
              <button v-if="form.cover" type="button" class="h-[34px] rounded-full bg-night/60 px-3 text-xs font-semibold text-white" @click="form.cover = null">Olib taşlaş</button>
              <button type="button" class="h-[34px] rounded-full bg-white/92 px-3 text-xs font-semibold text-ink" :disabled="uploading === 'cover'" @click="coverInput?.click()">{{ uploading === 'cover' ? 'Yuklanmoqda…' : 'Muqovani almaştiriş' }}</button>
            </span>
          </div>
          <div class="relative -mt-9 flex flex-wrap items-end gap-4 px-[22px] pb-5">
            <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="onImage($event, 'logo')">
            <button type="button" class="relative grid size-[84px] shrink-0 place-items-center overflow-hidden rounded-full bg-white text-[13px] font-extrabold shadow-[0_0_0_4px_#fff,0_8px_20px_-8px_rgba(19,17,47,0.4)]" :style="{ color: color(idx) }" :aria-label="'Logoni almaştiriş'" @click="logoInput?.click()">
              <img v-if="mediaUrl(form.logo)" :src="mediaUrl(form.logo)!" alt="" class="size-[86%] object-contain">
              <template v-else>LOGO</template>
              <span class="absolute inset-x-0 bottom-0 bg-night/60 py-0.5 text-[10px] font-semibold text-white">{{ uploading === 'logo' ? '…' : 'almaştiriş' }}</span>
            </button>
            <div class="min-w-0 flex-[1_1_260px] pt-10 pb-1">
              <h2 class="text-[22px] font-bold [overflow-wrap:anywhere]">{{ form.name.uz || current.name.uz }}</h2>
              <p class="mt-1 text-[13px] text-muted">/faculty/{{ current.slug }}</p>
            </div>
            <a :href="`${SITE_URL}/faculty/${current.slug}`" target="_blank" rel="noopener" class="btn-ghost mb-1 h-10!">Saytda köriş ↗</a>
          </div>
        </section>

        <div class="flex flex-wrap items-start gap-[18px]">
          <form class="card flex min-w-0 flex-[1_1_380px] flex-col gap-3 px-5 py-[18px]" @submit.prevent="save">
            <h2 class="text-base font-bold">Ma’lumotlar</h2>
            <I18nFields v-model="form.name" label="Nomi" required />
            <div>
              <div class="mb-1.5 flex items-center justify-between gap-2">
                <span class="label mb-0!">Fakultet haqida va manzil</span>
                <div role="tablist" aria-label="Til" class="flex gap-1">
                  <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
                </div>
              </div>
              <textarea v-model="form.about[lang]" rows="5" class="field h-auto! py-2.5 leading-relaxed" :aria-label="`Fakultet haqida · ${lang}`" placeholder="Böş qolsa, saytda HEMIS’dagi / namunaviy matn körinadi" />
              <input v-model="form.address[lang]" class="field mt-2" :aria-label="`Manzil · ${lang}`" placeholder="Manzil / xona: Boş bino, 2-qavat, 214-xona">
            </div>
            <div class="grid grid-cols-2 gap-2.5">
              <div><label for="fc-ph" class="label">Telefon</label><input id="fc-ph" v-model="form.phone" class="field" type="tel" placeholder="+998 71 …"></div>
              <div><label for="fc-mail" class="label">E-poçta</label><input id="fc-mail" v-model="form.email" class="field" type="email" :placeholder="`${current.slug}@uzswlu.uz`"></div>
            </div>
            <div><label for="fc-map" class="label">Xarita havolasi <span class="font-normal">(Google Maps, ixtiyoriy)</span></label><input id="fc-map" v-model="form.mapUrl" class="field" type="url"></div>
            <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
            <p v-else-if="saved" class="rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi — saytda yangilandi.</p>
            <div class="flex justify-end"><button type="submit" class="btn-primary h-[42px]!" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button></div>
          </form>

          <section class="card flex min-w-0 flex-[1_1_320px] flex-col gap-3 px-5 py-[18px]">
            <h2 class="text-base font-bold">HEMIS’dan <span class="text-[13px] font-medium text-subtle">· faqat öqiş</span></h2>
            <template v-if="h">
              <div><span class="label">Dekan</span><p class="flex items-center gap-2 rounded-[10px] bg-canvas px-3 py-2.5 text-[13px] text-[#3D3958]">🔒 {{ h.dean || '—' }}</p></div>
              <div class="grid grid-cols-3 gap-2">
                <div v-for="s in [[h.stats.students, 'talaba'], [h.stats.teachers, 'öqituvçi'], [h.stats.departments, 'kafedra']]" :key="s[1]" class="rounded-xl bg-canvas p-3"><p class="text-xl font-bold">{{ Number(s[0]).toLocaleString('ru-RU') }}</p><p class="mt-0.5 text-xs text-muted">{{ s[1] }}</p></div>
              </div>
              <div>
                <span class="label">Kafedralar</span>
                <ul class="flex flex-col gap-1.5">
                  <li v-for="d in h.departments" :key="d.id" class="flex items-center justify-between gap-2 rounded-[10px] bg-canvas px-3 py-2.5 text-[13px]">
                    <span>{{ d.name }}</span>
                    <RouterLink :to="{ path: '/kafedralar', query: { d: d.id } }" class="shrink-0 text-xs font-semibold text-brand-700">Ta’rif →</RouterLink>
                  </li>
                </ul>
              </div>
            </template>
            <p v-else class="text-sm text-muted">Bu fakultet HEMIS’da topilmadi.</p>
            <p class="text-xs leading-normal text-subtle">Bu ma’lumotlar HEMIS’da özgarsa, saytda ertasi kuni öz-özidan yangilanadi.</p>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>
