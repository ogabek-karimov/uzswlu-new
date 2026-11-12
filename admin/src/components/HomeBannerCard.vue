<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, ApiError, type I18n, type MediaDoc } from '@/lib/api'
import Icon from './Icon.vue'
import ImageField from './ImageField.vue'
import I18nFields from './I18nFields.vue'

// Bosh sahifadagi bayram banneri («Biz bilan bog'lanish» va «Davlat ramzlari» orasida).
// Faqat bitta rasm: yangisi yuklansa eskisining o'rniga turadi. Ko'z belgisi — saytda ko'rsatish/yashirish
type Banner = { image: MediaDoc | null; visible: boolean; alt: I18n; link?: string | null }

const form = reactive<Banner>({ image: null, visible: true, alt: {}, link: '' })
const saving = ref(false)
const message = ref('')
const failed = ref(false)

async function load() {
  const b = await api.get<Banner>('/globals/home-banner', { depth: 1 })
  Object.assign(form, { image: b.image ?? null, visible: b.visible, alt: b.alt ?? {}, link: b.link ?? '' })
}
onMounted(load)

async function save(text = 'Saqlandi — saytda yangilandi') {
  saving.value = true
  message.value = ''
  try {
    await api.post('/globals/home-banner', { image: form.image?.id ?? null, visible: form.visible, alt: form.alt, link: form.link })
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
  await save(form.visible ? 'Banner saytda körinadi' : 'Banner yaşirildi')
}
</script>

<template>
  <section class="card flex flex-col gap-4 p-[22px]">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-base font-bold">Bayram banneri</h2>
        <p class="mt-1 text-[13px] text-muted">Boş sahifada «Biz bilan bog‘laniş» va «Davlat ramzlari» orasida. Faqat bitta rasm — yangisi eskisining örniga turadi.</p>
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

    <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div :class="!form.visible && 'opacity-60'">
        <ImageField v-model="form.image" folder="carousel" label="Banner rasmini yuklaş (keng, masalan 1600×180)" />
      </div>
      <div class="flex flex-col gap-3.5">
        <div>
          <label for="banner-link" class="label">Havola (ixtiyoriy)</label>
          <input id="banner-link" v-model="form.link" class="field" placeholder="/universitet-haqida yoki https://…">
        </div>
        <I18nFields v-model="form.alt" label="Rasm tavsifi" layout="rows" id-prefix="banner-alt" />
      </div>
    </div>

    <p v-if="message" class="rounded-xl px-3.5 py-2.5 text-sm" :class="failed ? 'bg-red-50 text-red-800' : 'bg-[#DDFBF0] text-[#0B5A43]'">{{ message }}</p>
    <div>
      <button type="button" class="btn-primary h-[46px] px-5" :disabled="saving" @click="save()">{{ saving ? 'Saqlanmoqda…' : 'Bannerni saqlaş' }}</button>
    </div>
  </section>
</template>
