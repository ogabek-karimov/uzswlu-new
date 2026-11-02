<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import TelegramIcon from '@/components/TelegramIcon.vue'
import { ApiError } from '@/lib/api'
import { auth } from '@/lib/auth'
import { SITE_URL } from '@/lib/constants'
import { siteSettings } from '@/lib/settings'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const remember = ref(true)
const show = ref(false)
const busy = ref(false)
const error = ref('')

async function submit() {
  if (busy.value) return
  error.value = ''
  busy.value = true
  try {
    await auth.login(username.value.trim(), password.value, remember.value)
    const back = typeof route.query.r === 'string' && route.query.r.startsWith('/') ? route.query.r : '/'
    router.push(back)
  }
  catch (e) {
    if (e instanceof ApiError && e.status === 423) error.value = 'Juda köp xato urinişlar — hisob 15 daqiqaga bloklandi.'
    else if (e instanceof ApiError && e.status === 403) error.value = 'Bu hisob yopilgan. Superadminga murojaat qiling.'
    else if (e instanceof ApiError && e.status === 401) error.value = 'Login yoki parol notöğri. 5 marta xato kiritilsa, hisob 15 daqiqaga bloklanadi.'
    else error.value = 'Server bilan aloqa yöq. Birozdan keyin qayta urinib köring.'
  }
  finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="flex min-h-dvh flex-wrap bg-white">
    <!-- Brend paneli -->
    <section class="relative flex min-h-[320px] min-w-0 flex-[1_1_520px] flex-col overflow-hidden bg-night px-8 py-10 text-white sm:px-14 sm:py-12">
      <span aria-hidden="true" class="absolute -top-40 -right-44 size-[560px] rounded-full border-[70px] border-white/4" />
      <span aria-hidden="true" class="absolute -bottom-56 -left-32 size-[460px] rounded-full border-[50px] border-mint/6" />
      <div class="relative flex items-center gap-3.5">
        <img src="/mark.webp" alt="" class="size-[52px] object-contain">
        <span class="text-[15px] leading-tight font-semibold">Özbekiston davlat<br>jahon tillari universiteti</span>
      </div>
      <div class="relative my-auto py-12">
        <p class="text-xs font-bold tracking-[0.2em] text-mint uppercase">Boşqaruv paneli</p>
        <h2 class="mt-3.5 max-w-[520px] font-display text-[2.6rem] leading-[1.08] font-semibold sm:text-[52px]">Saytni boşqariş — <span class="text-mint italic">bir joyda</span></h2>
        <ul class="mt-7 flex flex-col gap-3.5 text-base text-white/80">
          <li v-for="p in ['Yangilik, e’lon va tadbirlarni 4 tilda joylaş', 'Sahifalar, karusel va hujjatlarni tahrirlaş', 'Taşriflar statistikasi va kiriş tarixi']" :key="p" class="flex items-center gap-3">
            <span class="grid size-[26px] shrink-0 place-items-center rounded-full bg-mint/14 text-mint"><Icon name="check" :size="14" /></span>{{ p }}
          </li>
        </ul>
      </div>
      <p class="relative text-[13px] text-white/45">© 2026 ÖzDJTU · Işlab çiqdi: Oğabek Karimov</p>
    </section>

    <!-- Kirish -->
    <section class="flex min-w-0 flex-[1_1_480px] items-center justify-center px-6 py-12 sm:px-8">
      <div class="w-full max-w-[420px]">
        <h1 class="text-[32px] font-bold tracking-tight">Admin panelga kiriş</h1>
        <p class="mt-2.5 text-base text-muted">Login va parolingizni kiriting.</p>

        <div v-if="error" role="alert" class="mt-5 rounded-xl bg-red-50 px-3.5 py-3 text-sm leading-relaxed text-red-800">{{ error }}</div>

        <form class="mt-6 flex flex-col gap-3.5" @submit.prevent="submit">
          <div>
            <label for="login" class="label text-[13px]! text-ink!">Login</label>
            <input id="login" v-model="username" class="field h-[50px]!" autocomplete="username" required autofocus>
          </div>
          <div>
            <label for="password" class="label text-[13px]! text-ink!">Parol</label>
            <div class="relative">
              <input id="password" v-model="password" :type="show ? 'text' : 'password'" class="field h-[50px]! pr-13" autocomplete="current-password" required>
              <button type="button" class="absolute top-1.5 right-1.5 grid size-[38px] place-items-center rounded-lg text-muted hover:bg-canvas" :aria-label="show ? 'Parolni yaşiriş' : 'Parolni körsatiş'" :aria-pressed="show" @click="show = !show">
                <Icon :name="show ? 'eyeOff' : 'eye'" :size="18" />
              </button>
            </div>
          </div>
          <label class="flex cursor-pointer items-center gap-2.5 text-sm text-[#3D3958]">
            <input v-model="remember" type="checkbox" class="size-[18px] accent-brand-800"> Bu kompyuterda eslab qoliş
          </label>
          <button type="submit" class="btn-primary h-[52px] text-base" :disabled="busy">{{ busy ? 'Tekşirilmoqda…' : 'Kiriş' }}</button>
        </form>

        <div class="mt-6 flex items-center gap-3 text-[13px] text-subtle"><span class="h-px flex-1 bg-line" />yoki xodim sifatida<span class="h-px flex-1 bg-line" /></div>
        <button type="button" disabled title="HEMIS ulangandan keyin işlaydi" class="mt-4 flex h-[52px] w-full items-center gap-3 rounded-2xl border border-field pr-4 pl-2 text-left opacity-70">
          <span class="grid size-9 place-items-center rounded-xl bg-mint text-[13px] font-extrabold text-night">H</span>
          <span class="flex-1 text-[15px] font-bold">HEMIS orqali kiriş</span>
          <span class="chip bg-[#FEF3DC] text-[#8A5A00]">tez orada</span>
        </button>
        <p class="mt-2.5 text-[13px] leading-relaxed text-subtle">Superadmin tayinlagan muharrirlar uçun. IT bölimi HEMIS ruxsatini bergandan keyin yoqiladi.</p>

        <p class="mt-5 rounded-xl bg-canvas px-3.5 py-3 text-xs leading-relaxed text-muted">Har bir kiriş tarixga yoziladi: vaqt, IP manzil, qurilma va brauzer.</p>

        <div class="mt-5 flex flex-wrap items-center justify-between gap-3">
          <a :href="SITE_URL" class="text-sm font-semibold text-brand-700">← Saytga qaytiş</a>
          <a :href="siteSettings.supportUrl" target="_blank" rel="noopener" class="inline-flex items-center gap-1.5 text-sm font-semibold text-[#3D3958]"><TelegramIcon :size="16" /> {{ siteSettings.supportText }}</a>
        </div>
      </div>
    </section>
  </div>
</template>
