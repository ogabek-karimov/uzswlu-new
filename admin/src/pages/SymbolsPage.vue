<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc } from '@/lib/api'
import { LANGS, type Lang, SITE_URL } from '@/lib/constants'
import ImageField from '@/components/ImageField.vue'
import PdfSlot from '@/components/PdfSlot.vue'

// Davlat ramzlari: gerb, bayroq va madhiya (bosh sahifadagi blok)
type Key = 'emblem' | 'flag' | 'anthem'
type Symbol = { image: MediaDoc | null; audio: MediaDoc | null; title: I18n; description: I18n; link: string; source: string }

const KEYS: { key: Key; name: string }[] = [
  { key: 'emblem', name: 'Davlat gerbi' },
  { key: 'flag', name: 'Davlat bayroği' },
  { key: 'anthem', name: 'Davlat madhiyasi' },
]
const lang = ref<Lang>('uz')
const loading = ref(true)
const saving = ref(false)
const saved = ref(false)
const error = ref('')
const blank = (): Symbol => ({ image: null, audio: null, title: {}, description: {}, link: '', source: '' })
const form = reactive<Record<Key, Symbol>>({ emblem: blank(), flag: blank(), anthem: blank() })
const obj = (v: unknown) => (v && typeof v === 'object' ? v as MediaDoc : null)

onMounted(async () => {
  const g = await api.get<Record<Key, Record<string, any>>>('/globals/symbols', { depth: 1 })
  for (const { key } of KEYS) {
    const s = g[key] ?? {}
    form[key] = { image: obj(s.image), audio: obj(s.audio), title: { ...(s.title ?? {}) }, description: { ...(s.description ?? {}) }, link: s.link ?? '', source: s.source ?? '' }
  }
  loading.value = false
})

async function save() {
  saving.value = true
  error.value = ''
  saved.value = false
  try {
    const data = Object.fromEntries(KEYS.map(({ key }) => {
      const s = form[key]
      return [key, { image: s.image?.id ?? null, ...(key === 'anthem' ? { audio: s.audio?.id ?? null } : {}), title: s.title, description: s.description, link: s.link.trim() || null, source: s.source.trim() || null }]
    }))
    await api.post('/globals/symbols', data)
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-[18px]" @submit.prevent="save">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Ramzlar</h1>
        <p class="mt-1.5 text-[15px] text-muted">Davlat ramzlari: gerb, bayroq va madhiya — saytning boş sahifasidagi blok. <a :href="SITE_URL" target="_blank" rel="noopener" class="font-semibold text-brand-700 underline">Saytda köriş ↗</a></p>
      </div>
      <div class="flex items-center gap-2.5 rounded-[14px] border border-line bg-white py-1.5 pr-1.5 pl-3.5">
        <span class="text-[13px] font-semibold text-muted">Tahrirlaş tili</span>
        <div role="tablist" aria-label="Til" class="flex gap-1">
          <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-[30px] min-w-10 rounded-lg px-2 text-xs font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
        </div>
      </div>
    </div>

    <p v-if="loading" class="text-sm text-muted">Yuklanmoqda…</p>
    <div v-else class="grid items-start gap-[18px] lg:grid-cols-3">
      <section v-for="{ key, name } in KEYS" :key="key" class="card flex flex-col gap-3 p-[18px]" :aria-label="name">
        <h2 class="text-base font-bold">{{ name }}</h2>
        <div class="mx-auto w-full max-w-[260px]"><ImageField v-model="form[key].image" folder="logos" :label="key === 'anthem' ? 'Muqova rasmi (ixtiyoriy)' : 'Rasm yuklaş'" /></div>
        <div v-if="key === 'anthem'">
          <span class="label">Audio (MP3)</span>
          <PdfSlot v-model="form.anthem.audio" lang="Madhiya" note="MP3 fayl" accept="audio/mpeg" kind="all" />
          <audio v-if="form.anthem.audio?.url" :src="form.anthem.audio.url" controls class="mt-2 w-full" />
        </div>
        <div><label :for="`${key}-t`" class="label">Sarlavha · {{ LANGS.find(l => l.code === lang)?.label }}</label><input :id="`${key}-t`" v-model="form[key].title[lang]" class="field"></div>
        <div><label :for="`${key}-d`" class="label">Tavsif · {{ LANGS.find(l => l.code === lang)?.label }} <span class="font-normal">(ixtiyoriy)</span></label><textarea :id="`${key}-d`" v-model="form[key].description[lang]" rows="4" class="field h-auto! py-2.5 leading-relaxed" /></div>
        <div class="grid grid-cols-[1fr_110px] gap-2">
          <div><label :for="`${key}-l`" class="label">Rasmiy manba havolasi</label><input :id="`${key}-l`" v-model="form[key].link" class="field" type="url"></div>
          <div><label :for="`${key}-s`" class="label">Manba</label><input :id="`${key}-s`" v-model="form[key].source" class="field" placeholder="archive.uz"></div>
        </div>
      </section>
    </div>

    <div class="flex items-center justify-end gap-3">
      <span v-if="error" class="text-sm text-red-700">{{ error }}</span>
      <span v-else-if="saved" class="text-sm font-semibold text-mint-text">Saqlandi — saytda yangilandi ✓</span>
      <button type="submit" class="btn-primary h-[46px] px-[22px]" :disabled="saving || loading">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
    </div>
  </form>
</template>
