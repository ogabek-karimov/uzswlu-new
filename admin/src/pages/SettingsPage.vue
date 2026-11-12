<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import LangTabs from '@/components/LangTabs.vue'
import TelegramIcon from '@/components/TelegramIcon.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'
import { api, ApiError, type I18n, type Paginated } from '@/lib/api'
import type { Lang } from '@/lib/constants'
import { dateTime } from '@/lib/format'
import { loadSiteSettings } from '@/lib/settings'

/** Bino: bosh sahifadagi «Biz bilan bog'lanish» kartasi va Aloqa sahifasi. coords — koordinata yoki Google Maps havolasi (backend koordinataga aylantiradi) */
type Campus = { key?: string; name: I18n; address: I18n; phone?: string | null; email?: string | null; coords?: string | null; mapUrl?: string | null }
type SettingsDoc = {
  site: { name: I18n; abbr: I18n; description: I18n }
  contact: { phone?: string; email?: string; address: I18n; telegram?: string; instagram?: string; facebook?: string; youtube?: string; campuses: Campus[] }
  support: { telegram?: string; text: I18n; showInAdmin: boolean; showOnSite: boolean; pages: string[]; place: 'float' | 'end' | 'footer' | 'header' }
  numbers: { auto: boolean; students?: number | null; staff?: number | null; faculties?: number | null; departments?: number | null }
}
type Version = { id: string; updatedAt: string; createdAt: string; version: SettingsDoc & { updatedAt?: string } }
type Section = keyof SettingsDoc

const TABS: [Section | 'campuses' | 'history', string][] = [['site', 'Umumiy'], ['contact', 'Aloqa'], ['campuses', 'Binolar va xarita'], ['support', 'Texnik yordam'], ['numbers', 'Raqamlar'], ['history', 'Özgarişlar tarixi']]
const PAGES = [['all', 'Barça sahifalar'], ['home', 'Boş sahifa'], ['contact', 'Aloqa'], ['staff', 'Xodim sahifalari'], ['admission', 'Qabul']] as const
const PLACES = [['float', 'Öng pastki burçakda', 'Suzib turadi, har doim körinadi'], ['end', 'Sahifa oxirida', 'Matndan keyin karta bölib'], ['footer', 'Footer içida', 'Pastki qismda kiçik havola'], ['header', 'Sarlavha qatorida', 'Menyu yonida kiçik tugma']] as const

const tab = ref<Section | 'campuses' | 'history'>('site')
const lang = ref<Lang>('uz')
const form = reactive<SettingsDoc>({
  site: { name: {}, abbr: {}, description: {} },
  contact: { address: {}, campuses: [] },
  support: { text: {}, showInAdmin: true, showOnSite: false, pages: [], place: 'float' },
  numbers: { auto: true },
})
const versions = ref<Version[]>([])
const saving = ref(false)
const message = ref('')

async function load() {
  const s = await api.get<SettingsDoc>('/globals/settings', { depth: 0 })
  for (const key of ['site', 'contact', 'support', 'numbers'] as const) Object.assign(form[key], s[key] ?? {})
  versions.value = (await api.get<Paginated<Version>>('/globals/settings/versions', { sort: '-updatedAt', limit: 30 })).docs
}
onMounted(load)

async function save(text = 'Saqlandi') {
  saving.value = true
  try {
    await api.post('/globals/settings', JSON.parse(JSON.stringify(form)))
    flash(text)
    await load()
    await loadSiteSettings()
  }
  catch (e) {
    flash(e instanceof ApiError ? e.message : 'Saqlab bölmadi')
  }
  finally {
    saving.value = false
  }
}

/** Bo'limni asl (birinchi saqlangan) holatiga qaytarish */
async function resetSection(section: Section) {
  const first = (await api.get<Paginated<Version>>('/globals/settings/versions', { sort: 'createdAt', limit: 1 })).docs[0]
  if (!first) return
  if (!window.confirm('Bu bölim asl holiga qaytarilsinmi? Hozirgi qiymatlar tarixda saqlanib qoladi.')) return
  Object.assign(form[section], JSON.parse(JSON.stringify(first.version[section])))
  await save('Asl holiga qaytarildi')
}

async function restoreVersion(v: Version) {
  if (!window.confirm(`Sozlamalar ${dateTime(v.updatedAt)} dagi holatiga qaytarilsinmi?`)) return
  await api.post(`/globals/settings/versions/${v.id}`)
  flash('Tanlangan holatga qaytarildi')
  await load()
  await loadSiteSettings()
}

function togglePage(p: string) {
  form.support.pages = form.support.pages.includes(p) ? form.support.pages.filter(x => x !== p) : [...form.support.pages, p]
}

function addCampus() {
  form.contact.campuses.push({ name: {}, address: {}, phone: form.contact.phone ?? '', email: form.contact.email ?? '', coords: '' })
}
function moveCampus(i: number, step: -1 | 1) {
  const list = form.contact.campuses
  const [item] = list.splice(i, 1)
  if (item) list.splice(i + step, 0, item)
}
function removeCampus(i: number) {
  if (window.confirm(`«${form.contact.campuses[i]?.name.uz || 'Yangi bino'}» öçirilsinmi? (Saqlaşdan keyin saytdan ham olinadi)`)) form.contact.campuses.splice(i, 1)
}

/** Xarita oldindan körinişi: koordinata (yoki havoladagi koordinata), bo'lmasa — manzil bo'yicha (backend ham şunday qiladi) */
const COORDS = [/!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/, /!2d(-?\d+(?:\.\d+)?)!3d(-?\d+(?:\.\d+)?)/, /@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/, /^\s*(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)\s*$/]
function mapPreview(c: Campus) {
  const raw = (c.coords ?? '').trim()
  for (const [i, re] of COORDS.entries()) {
    const m = raw.match(re)
    if (m) return `https://maps.google.com/maps?q=${i === 1 ? `${m[2]},${m[1]}` : `${m[1]},${m[2]}`}&z=16&output=embed`
  }
  return c.address.uz ? `https://maps.google.com/maps?q=${encodeURIComponent(c.address.uz)}&z=16&output=embed` : ''
}

function flash(text: string) {
  message.value = text
  setTimeout(() => { if (message.value === text) message.value = '' }, 3000)
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Sayt sozlamalari</h1>
        <p class="mt-1.5 text-[15px] text-muted">Saytning umumiy ma’lumotlari. Har bir saqlaş tarixga yoziladi — istalgan payt oldingi yoki asl holiga qaytariş mumkin.</p>
      </div>
      <button v-if="tab !== 'history'" type="button" class="btn-primary h-[46px] px-5" :disabled="saving" @click="save()">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
    </div>

    <div role="tablist" aria-label="Sozlamalar bölimlari" class="card flex flex-wrap gap-1 p-1">
      <button v-for="t in TABS" :key="t[0]" type="button" role="tab" :aria-selected="tab === t[0]" class="h-10 rounded-[10px] px-4 text-sm font-semibold" :class="tab === t[0] ? 'bg-ink text-white' : 'text-muted'" @click="tab = t[0]">{{ t[1] }}</button>
    </div>

    <!-- Umumiy -->
    <section v-if="tab === 'site'" class="card flex flex-col gap-4 p-[22px]">
      <div class="flex flex-wrap items-center justify-between gap-2.5">
        <h2 class="text-base font-bold">Universitet nomi va tavsifi</h2>
        <div class="flex items-center gap-2"><LangTabs v-model="lang" compact /><button type="button" class="btn-ghost h-[34px]! px-3! text-xs!" @click="resetSection('site')"><Icon name="undo" :size="14" />Asl holiga qaytariş</button></div>
      </div>
      <div><label for="s-name" class="label">Nomi · {{ lang.toUpperCase() }}</label><input id="s-name" v-model="form.site.name[lang]" class="field"></div>
      <div><label for="s-abbr" class="label">Qisqartma · {{ lang.toUpperCase() }}</label><input id="s-abbr" v-model="form.site.abbr[lang]" class="field max-w-xs"></div>
      <div><label for="s-desc" class="label">Sayt tavsifi (Google natijalarida) · {{ lang.toUpperCase() }}</label><textarea id="s-desc" v-model="form.site.description[lang]" rows="3" class="field h-auto! py-2.5" placeholder="150–160 belgi" /></div>
    </section>

    <!-- Aloqa -->
    <section v-if="tab === 'contact'" class="card flex flex-col gap-4 p-[22px]">
      <div class="flex flex-wrap items-center justify-between gap-2.5">
        <h2 class="text-base font-bold">Aloqa va ijtimoiy tarmoqlar</h2>
        <button type="button" class="btn-ghost h-[34px]! px-3! text-xs!" @click="resetSection('contact')"><Icon name="undo" :size="14" />Asl holiga qaytariş</button>
      </div>
      <div class="grid gap-3.5 sm:grid-cols-2">
        <div><label for="c-phone" class="label">Işonç telefoni</label><input id="c-phone" v-model="form.contact.phone" class="field"></div>
        <div><label for="c-mail" class="label">E-poçta</label><input id="c-mail" v-model="form.contact.email" class="field"></div>
      </div>
      <div>
        <div class="mb-1.5 flex items-center justify-between gap-2"><span class="label mb-0!">Manzil · {{ lang.toUpperCase() }}</span><LangTabs v-model="lang" compact /></div>
        <input v-model="form.contact.address[lang]" aria-label="Manzil" class="field">
      </div>
      <div class="grid gap-3.5 sm:grid-cols-2">
        <div v-for="k in (['telegram', 'instagram', 'facebook', 'youtube'] as const)" :key="k"><label :for="`c-${k}`" class="label capitalize">{{ k }}</label><input :id="`c-${k}`" v-model="form.contact[k]" class="field" placeholder="havola"></div>
      </div>
    </section>

    <!-- Binolar va xarita -->
    <section v-if="tab === 'campuses'" class="flex flex-col gap-4">
      <div class="card flex flex-wrap items-center justify-between gap-3 p-[22px]">
        <div>
          <h2 class="text-base font-bold">Binolar va xarita</h2>
          <p class="mt-1 text-[13px] text-muted">Boş sahifadagi «Biz bilan bog‘lanish» kartalari va Aloqa sahifasi. Saytda şu tartibda çiqadi.</p>
        </div>
        <div class="flex items-center gap-2">
          <LangTabs v-model="lang" compact />
          <button type="button" class="btn-ghost h-[34px]! px-3! text-xs!" @click="addCampus"><Icon name="plus" :size="14" />Bino qöşiş</button>
        </div>
      </div>

      <article v-for="(c, i) in form.contact.campuses" :key="c.key || `new-${i}`" class="card grid gap-5 p-[22px] lg:grid-cols-[minmax(0,1fr)_320px]">
        <div class="flex min-w-0 flex-col gap-3.5">
          <div class="flex items-center justify-between gap-2">
            <span class="chip bg-brand-100 text-brand-800">{{ String(i + 1).padStart(2, '0') }} · {{ c.name.uz || 'Yangi bino' }}</span>
            <div class="flex items-center gap-1">
              <button type="button" class="btn-ghost size-9! p-0!" :disabled="i === 0" aria-label="Yuqoriga" title="Yuqoriga" @click="moveCampus(i, -1)"><span class="rotate-180"><Icon name="chevronDown" :size="16" /></span></button>
              <button type="button" class="btn-ghost size-9! p-0!" :disabled="i === form.contact.campuses.length - 1" aria-label="Pastga" title="Pastga" @click="moveCampus(i, 1)"><Icon name="chevronDown" :size="16" /></button>
              <button type="button" class="btn-ghost size-9! p-0! text-[#B42318]!" aria-label="Öçiriş" title="Öçiriş" @click="removeCampus(i)"><Icon name="trash" :size="16" /></button>
            </div>
          </div>
          <div><label :for="`cp-name-${i}`" class="label">Nomi · {{ lang.toUpperCase() }}</label><input :id="`cp-name-${i}`" v-model="c.name[lang]" class="field" placeholder="Bosh bino"></div>
          <div><label :for="`cp-addr-${i}`" class="label">Manzil · {{ lang.toUpperCase() }}</label><input :id="`cp-addr-${i}`" v-model="c.address[lang]" class="field" placeholder="Toshkent sh., …"></div>
          <div class="grid gap-3.5 sm:grid-cols-2">
            <div><label :for="`cp-phone-${i}`" class="label">Telefon</label><input :id="`cp-phone-${i}`" v-model="c.phone" class="field" placeholder="+998 71 230 13 73"></div>
            <div><label :for="`cp-mail-${i}`" class="label">E-poçta</label><input :id="`cp-mail-${i}`" v-model="c.email" type="email" class="field" placeholder="uzdjtu@uzswlu.uz"></div>
          </div>
          <div>
            <label :for="`cp-geo-${i}`" class="label">Xaritadagi joy</label>
            <input :id="`cp-geo-${i}`" v-model="c.coords" class="field" placeholder="41.286038, 69.194908 yoki Google Maps havolasi">
            <p class="mt-1 text-xs text-subtle">Google Maps’da binoni toping → koordinatani yoki «Ulaşiş» havolasini nusxalab qöying. Saqlanganda koordinataga aylanadi; böş qolsa — manzil böyiça topiladi.</p>
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <span class="label mb-0!">Saytdagi xarita</span>
          <div class="overflow-hidden rounded-[14px] border border-[#E8E3D8] bg-[#FAF8F4]">
            <iframe v-if="mapPreview(c)" :src="mapPreview(c)" loading="lazy" referrerpolicy="no-referrer-when-downgrade" class="block aspect-[4/3] w-full" :title="`${c.name.uz || 'Bino'} — xarita`" />
            <div v-else class="grid aspect-[4/3] place-items-center px-4 text-center text-xs text-subtle">Manzil yoki xaritadagi joyni kiriting</div>
          </div>
        </div>
      </article>
      <p v-if="!form.contact.campuses.length" class="card p-6 text-center text-sm text-muted">Hali bino yöq — «Bino qöşiş» tugmasini bosing.</p>
    </section>

    <!-- Texnik yordam -->
    <div v-if="tab === 'support'" class="flex flex-wrap items-start gap-5">
      <section class="card flex min-w-0 flex-[1_1_460px] flex-col gap-4 p-[22px]">
        <div class="flex flex-wrap items-center justify-between gap-2.5">
          <h2 class="text-base font-bold">Texnik yordam</h2>
          <button type="button" class="btn-ghost h-[34px]! px-3! text-xs!" @click="resetSection('support')"><Icon name="undo" :size="14" />Asl holiga qaytariş</button>
        </div>
        <p class="-mt-2 text-[13px] text-muted">Admin panelda va saytda körinadigan Telegram tugmasi. Manzil özgarsa — şu yerda yangilang.</p>
        <div>
          <label for="sp-tg" class="label">Telegram manzili</label>
          <div class="flex h-[46px] items-center gap-2.5 rounded-xl border border-field px-3">
            <TelegramIcon :size="22" />
            <input id="sp-tg" v-model="form.support.telegram" class="min-w-0 flex-1 bg-transparent text-sm font-medium outline-none">
            <a :href="form.support.telegram" target="_blank" rel="noopener" class="text-xs font-semibold text-brand-700">Tekşiriş ↗</a>
          </div>
        </div>
        <div>
          <div class="mb-1.5 flex items-center justify-between gap-2"><span class="label mb-0!">Tugma matni · {{ lang.toUpperCase() }}</span><LangTabs v-model="lang" compact /></div>
          <input v-model="form.support.text[lang]" aria-label="Tugma matni" class="field">
        </div>
        <div class="flex items-center justify-between gap-3.5 rounded-[14px] border border-[#F0EEF6] px-3.5 py-3">
          <span class="text-sm leading-snug"><b class="block">Admin panelda körsatiş</b><span class="text-xs text-subtle">Yon menyu va pastki qatorda</span></span>
          <ToggleSwitch v-model="form.support.showInAdmin" label="Admin panelda körsatiş" />
        </div>
        <div class="flex items-center justify-between gap-3.5 rounded-[14px] border border-[#F0EEF6] px-3.5 py-3">
          <span class="text-sm leading-snug"><b class="block">Saytda körsatiş</b><span class="text-xs text-subtle">Taşrifçilar uçun — quyida sahifa va joyni tanlang</span></span>
          <ToggleSwitch v-model="form.support.showOnSite" label="Saytda körsatiş" />
        </div>
        <template v-if="form.support.showOnSite">
          <div>
            <span class="label">Qaysi sahifalarda</span>
            <div class="flex flex-wrap gap-1.5">
              <button v-for="p in PAGES" :key="p[0]" type="button" :aria-pressed="form.support.pages.includes(p[0])" class="h-[34px] rounded-full px-3 text-xs font-semibold" :class="form.support.pages.includes(p[0]) ? 'bg-ink text-white' : 'border border-field bg-white text-[#3D3958]'" @click="togglePage(p[0])">{{ p[1] }}</button>
            </div>
          </div>
          <div>
            <span class="label">Sahifaning qayerida</span>
            <div role="radiogroup" aria-label="Joylaşuv" class="grid gap-2 sm:grid-cols-2">
              <button v-for="p in PLACES" :key="p[0]" type="button" role="radio" :aria-checked="form.support.place === p[0]" class="rounded-xl px-3 py-2.5 text-left" :class="form.support.place === p[0] ? 'border-2 border-brand-700 bg-brand-50' : 'border border-field bg-white'" @click="form.support.place = p[0]">
                <b class="block text-[13px]">{{ p[1] }}</b><span class="mt-0.5 block text-xs text-muted">{{ p[2] }}</span>
              </button>
            </div>
          </div>
        </template>
      </section>
      <section class="card min-w-0 flex-[1_1_340px] p-[22px]">
        <h2 class="text-base font-bold">Saytda şunday körinadi</h2>
        <p class="mt-1 text-[13px] text-muted">{{ form.support.showOnSite ? 'Tanlangan joyda körinadi.' : 'Saytda körsatiş öçirilgan — faqat admin panelda turadi.' }}</p>
        <div aria-hidden="true" class="relative mt-3.5 aspect-[16/11] overflow-hidden rounded-[14px] border border-[#E8E3D8] bg-[#FAF8F4]">
          <div class="flex h-[34px] items-center gap-2 border-b border-[#E8E3D8] bg-white px-3"><img src="/mark.webp" alt="" class="size-5"><span class="h-1.5 w-[90px] rounded bg-[#DCD9E6]" /></div>
          <div class="flex flex-col gap-2 px-[18px] py-4"><span class="h-3 w-3/5 rounded bg-[#D9D6E5]" /><span class="h-1.5 w-full rounded bg-[#E6E3EE]" /><span class="h-1.5 w-11/12 rounded bg-[#E6E3EE]" /><span class="h-1.5 w-2/3 rounded bg-[#E6E3EE]" /></div>
          <div class="absolute inset-x-0 bottom-0 h-10 bg-night" />
          <span
            v-if="form.support.showOnSite"
            class="absolute inline-flex items-center gap-1.5 rounded-full font-bold whitespace-nowrap"
            :class="{
              'right-3 bottom-[52px] h-[34px] bg-white pr-3.5 pl-2.5 text-xs shadow-xl': form.support.place === 'float',
              'bottom-14 left-[18px] h-8 border border-[#BFE4F7] bg-[#E9F6FD] pr-3 pl-2.5 text-xs text-[#0E5E86]': form.support.place === 'end',
              'right-3 bottom-[9px] h-[22px] px-2 text-[11px] text-white': form.support.place === 'footer',
              'top-1.5 right-2.5 h-[22px] bg-[#E9F6FD] px-2 text-[11px] text-[#0E5E86]': form.support.place === 'header',
            }"
          ><TelegramIcon :size="16" />{{ form.support.text[lang] || form.support.text.uz }}</span>
        </div>
      </section>
    </div>

    <!-- Raqamlar -->
    <section v-if="tab === 'numbers'" class="card flex flex-col gap-4 p-[22px]">
      <div class="flex flex-wrap items-center justify-between gap-2.5">
        <h2 class="text-base font-bold">Boş sahifadagi raqamlar</h2>
        <button type="button" class="btn-ghost h-[34px]! px-3! text-xs!" @click="resetSection('numbers')"><Icon name="undo" :size="14" />Asl holiga qaytariş</button>
      </div>
      <div class="flex items-center justify-between gap-3.5 rounded-[14px] border border-[#F0EEF6] px-3.5 py-3">
        <span class="text-sm leading-snug"><b class="block">HEMIS’dan avtomatik</b><span class="text-xs text-subtle">Öçirilsa — quyidagi qiymatlar körsatiladi</span></span>
        <ToggleSwitch v-model="form.numbers.auto" label="HEMIS’dan avtomatik" />
      </div>
      <div class="grid gap-3 sm:grid-cols-4">
        <div v-for="k in ([['students', 'Talabalar'], ['staff', 'Akademik xodimlar'], ['faculties', 'Fakultetlar'], ['departments', 'Kafedralar']] as const)" :key="k[0]">
          <label :for="`n-${k[0]}`" class="label">{{ k[1] }}</label><input :id="`n-${k[0]}`" v-model.number="form.numbers[k[0]]" type="number" min="0" class="field text-lg! font-bold" :disabled="form.numbers.auto">
        </div>
      </div>
    </section>

    <!-- Tarix -->
    <section v-if="tab === 'history'" class="card p-[22px]">
      <div class="flex flex-wrap items-baseline justify-between gap-2.5">
        <h2 class="text-base font-bold">Özgarişlar tarixi</h2>
        <span class="text-xs text-subtle">Qaytarilganda joriy holat ham tarixda qoladi</span>
      </div>
      <ol class="mt-3.5 flex flex-col gap-2">
        <li v-for="(v, i) in versions" :key="v.id" class="flex flex-wrap items-center gap-3 rounded-[14px] px-3.5 py-3" :class="i === 0 ? 'bg-brand-50' : 'bg-[#FAF9FD]'">
          <span class="min-w-0 flex-[1_1_300px] text-sm"><b>{{ i === 0 ? 'Hozirgi holat' : i === versions.length - 1 ? 'Asl holat' : 'Saqlangan holat' }}</b><span class="block text-xs text-subtle">{{ dateTime(v.updatedAt) }}</span></span>
          <span class="chip" :class="i === 0 ? 'bg-brand-100 text-brand-800' : i === versions.length - 1 ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#F1F0F5] text-muted'">{{ i === 0 ? 'joriy' : i === versions.length - 1 ? 'asl' : 'versiya' }}</span>
          <button v-if="i > 0" type="button" class="btn-ghost h-9! px-3! text-xs!" @click="restoreVersion(v)"><Icon name="undo" :size="14" />{{ i === versions.length - 1 ? 'Asl holiga qaytariş' : 'Şu holatga qaytariş' }}</button>
        </li>
      </ol>
    </section>

    <div v-if="message" role="status" class="fixed right-6 bottom-6 z-50 rounded-2xl bg-night px-4 py-3 text-sm font-semibold text-white shadow-xl">{{ message }}</div>
  </div>
</template>
