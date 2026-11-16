<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, ApiError, type I18n, type MediaDoc } from '@/lib/api'
import Icon from './Icon.vue'
import ImageField from './ImageField.vue'
import I18nFields from './I18nFields.vue'

// «Universitet haqida» bölimining video turi (boş sahifadagi 3 daqiqalik sayohat kartasi).
// Media va ma'lumot faqat şu yerdan kiritiladi. Havola: YouTube, Vimeo yoki to'g'ridan-to'g'ri https://…/video.mp4
type Tour = { url: string; poster: MediaDoc | null; title: I18n; text: I18n; visible: boolean }

const form = reactive<Tour>({ url: '', poster: null, title: {}, text: {}, visible: true })
const saving = ref(false)
const message = ref('')
const failed = ref(false)

async function load() {
  const v = await api.get<Tour>('/globals/video-tour', { depth: 1 })
  Object.assign(form, { url: v.url ?? '', poster: v.poster ?? null, title: v.title ?? {}, text: v.text ?? {}, visible: v.visible })
}
onMounted(load)

async function save(text = 'Saqlandi — saytda yangilandi') {
  saving.value = true
  message.value = ''
  try {
    await api.post('/globals/video-tour', { url: form.url.trim(), poster: form.poster?.id ?? null, title: form.title, text: form.text, visible: form.visible })
    failed.value = false
    message.value = text
    await load()
  }
  catch (e) {
    failed.value = true
    message.value = e instanceof ApiError ? e.message : 'Saqlab bölmadi'
  }
  finally {
    saving.value = false
  }
}

async function toggleVisible() {
  form.visible = !form.visible
  await save(form.visible ? 'Video tur saytda körinadi' : 'Video tur yaşirildi')
}
</script>

<template>
  <section class="card flex flex-col gap-4 p-[22px]">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-base font-bold">Video tur — universitet böylab 3 daqiqalik sayohat</h2>
        <p class="mt-1 text-[13px] text-muted">Boş sahifadagi «Universitet haqida» blokida çiqadi. Video havolasi bölmasa, karta «Video darsliklar» sahifasiga olib boradi.</p>
      </div>
      <button
        type="button"
        class="inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm font-semibold transition-colors"
        :class="form.visible ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#F1F0F5] text-muted'"
        :aria-pressed="form.visible"
        :disabled="saving"
        :title="form.visible ? 'Saytda körinadi — yaşiriş uçun bosing' : 'Yaşirilgan — körsatiş uçun bosing'"
        @click="toggleVisible"
      >
        <Icon :name="form.visible ? 'eye' : 'eyeOff'" :size="18" />
        {{ form.visible ? 'Saytda körinadi' : 'Yaşirilgan' }}
      </button>
    </div>

    <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]" :class="!form.visible && 'opacity-60'">
      <div class="flex flex-col gap-3.5">
        <div>
          <label for="vt-url" class="label">Video havolasi</label>
          <input id="vt-url" v-model="form.url" class="field" placeholder="https://www.youtube.com/watch?v=… yoki https://vimeo.com/… yoki https://…/tur.mp4">
          <p class="mt-1 text-xs text-muted">YouTube, Vimeo yoki to‘g‘ridan-to‘g‘ri video fayl (mp4, webm, ogg) havolasi.</p>
        </div>
        <I18nFields v-model="form.title" label="Sarlavha" layout="rows" id-prefix="vt-title" />
        <I18nFields v-model="form.text" label="Qisqa ma’lumot" textarea :rows="3" layout="rows" id-prefix="vt-text" />
      </div>
      <ImageField v-model="form.poster" folder="carousel" label="Muqova rasmini yuklaş" />
    </div>

    <p v-if="message" class="rounded-xl px-3.5 py-2.5 text-sm" :class="failed ? 'bg-red-50 text-red-800' : 'bg-[#DDFBF0] text-[#0B5A43]'">{{ message }}</p>
    <div>
      <button type="button" class="btn-primary h-[46px] px-5" :disabled="saving" @click="save()">{{ saving ? 'Saqlanmoqda…' : 'Video turni saqlaş' }}</button>
    </div>
  </section>
</template>
