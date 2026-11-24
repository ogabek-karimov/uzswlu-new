<script setup lang="ts">
import { computed, reactive } from 'vue'
import { api } from '@/lib/api'
import { auth } from '@/lib/auth'
import Icon from '../Icon.vue'

// Profil → «Xavfsizlik»: parolni almashtirish va ikki bosqichli tasdiq (2FA). Natija xabari ota sahifaga `done` bilan
const emit = defineEmits<{ done: [string] }>()
const me = auth.user
const pw = reactive({ current: '', next: '', repeat: '', error: '', busy: false })

const checks = computed(() => [
  [pw.next.length >= 10, 'Kamida 10 ta belgi'],
  [/[A-Z]/.test(pw.next) && /[a-z]/.test(pw.next), 'Katta va kiçik harf'],
  [/\d/.test(pw.next), 'Kamida bitta raqam'],
  [/[^A-Za-z0-9]/.test(pw.next), 'Belgi: ! ? # @ …'],
] as [boolean, string][])
const score = computed(() => checks.value.filter(c => c[0]).length)
const LEVEL = [['Juda kuçsiz', '#B42318'], ['Kuçsiz', '#B42318'], ['Örtaça', '#8A5A00'], ['Yaxşi', '#0E7A5A'], ['Kuçli', '#0B5A43']]

async function changePassword() {
  pw.error = ''
  if (pw.next !== pw.repeat) { pw.error = 'Yangi parollar bir xil emas'; return }
  if (pw.next.length < 10) { pw.error = 'Parol kamida 10 ta belgidan iborat bölsin'; return }
  pw.busy = true
  try {
    // Hozirgi parolni server tekshiradi (currentPassword): o'g'irlangan sessiya bilan parol almashtirib bo'lmaydi
    await api.patch(`/users/${me.value!.id}`, { password: pw.next, currentPassword: pw.current })
    await api.post('/users/login', { username: me.value!.username, password: pw.next })
    Object.assign(pw, { current: '', next: '', repeat: '' })
    emit('done', 'Parol almaştirildi')
  }
  catch (e) { pw.error = (e as Error).message }
  finally { pw.busy = false }
}

// ─── Ikki bosqichli tasdiq (2FA) ───
const tf = reactive({ step: 'idle' as 'idle' | 'setup' | 'codes', secret: '', uri: '', code: '', password: '', disableCode: '', recovery: [] as string[], busy: false, error: '' })
const tfOn = computed(() => !!me.value?.twoFactorEnabled)
const groupedSecret = computed(() => tf.secret.replace(/(.{4})/g, '$1 ').trim())

async function tfStart() {
  tf.error = ''
  try {
    const res = await api.post<{ secret: string; otpauthUri: string }>('/users/2fa/setup')
    Object.assign(tf, { step: 'setup', secret: res.secret, uri: res.otpauthUri, code: '' })
  }
  catch (e) { tf.error = (e as Error).message }
}

async function tfEnable() {
  tf.error = ''
  tf.busy = true
  try {
    const res = await api.post<{ recoveryCodes: string[] }>('/users/2fa/enable', { code: tf.code.trim() })
    tf.recovery = res.recoveryCodes
    tf.step = 'codes'
    await auth.me()
  }
  catch (e) { tf.error = (e as Error).message }
  finally { tf.busy = false }
}

async function tfDisable() {
  tf.error = ''
  tf.busy = true
  try {
    await api.post('/users/2fa/disable', { password: tf.password, code: tf.disableCode.trim() })
    Object.assign(tf, { step: 'idle', password: '', disableCode: '', recovery: [] })
    await auth.me()
    emit('done', '2FA öçirildi')
  }
  catch (e) { tf.error = (e as Error).message }
  finally { tf.busy = false }
}

async function tfNewCodes() {
  tf.error = ''
  try {
    const res = await api.post<{ recoveryCodes: string[] }>('/users/2fa/recovery', { password: tf.password, code: tf.disableCode.trim() })
    tf.recovery = res.recoveryCodes
    tf.step = 'codes'
  }
  catch (e) { tf.error = (e as Error).message }
}
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-2">
    <section class="card flex min-w-0 flex-col gap-3.5 p-[22px]">
      <div class="flex items-center gap-3">
        <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700"><Icon name="lock" :size="18" /></span>
        <div><h2 class="text-base font-bold">Parolni almaştiriş</h2><p class="text-[13px] text-muted">Boşqa joyda işlatmagan parol tanlang.</p></div>
      </div>
      <p v-if="pw.error" role="alert" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ pw.error }}</p>
      <form class="flex flex-col gap-3.5" @submit.prevent="changePassword">
        <input :value="me?.username" autocomplete="username" class="hidden" readonly>
        <div><label for="pw-cur" class="label">Hozirgi parol</label><input id="pw-cur" v-model="pw.current" type="password" class="field" autocomplete="current-password" required></div>
        <div>
          <label for="pw-new" class="label">Yangi parol</label><input id="pw-new" v-model="pw.next" type="password" class="field" autocomplete="new-password" required>
          <div aria-hidden="true" class="mt-2.5 grid grid-cols-4 gap-1.5"><span v-for="i in 4" :key="i" class="h-1.5 rounded-full transition-colors" :style="{ background: i <= score ? LEVEL[score]![1] : '#ECEAF3' }" /></div>
          <p class="mt-2 text-[13px] font-semibold" :style="{ color: LEVEL[score]![1] }">Parol kuçi: {{ LEVEL[score]![0] }}</p>
        </div>
        <ul class="grid gap-x-3.5 gap-y-1.5 text-[13px] sm:grid-cols-2">
          <li v-for="c in checks" :key="c[1]" class="flex items-center gap-2" :class="c[0] ? 'text-[#0B5A43]' : 'text-subtle'"><span aria-hidden="true" class="font-bold">{{ c[0] ? '✓' : '○' }}</span>{{ c[1] }}</li>
        </ul>
        <div><label for="pw-rep" class="label">Yangi parolni takrorlang</label><input id="pw-rep" v-model="pw.repeat" type="password" class="field" autocomplete="new-password" required></div>
        <div class="flex justify-end"><button type="submit" class="btn-primary" :disabled="pw.busy">Parolni saqlaş</button></div>
      </form>
    </section>

    <section class="card flex min-w-0 flex-col gap-3.5 p-[22px]">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div class="flex items-center gap-3">
          <span class="grid size-10 shrink-0 place-items-center rounded-xl" :class="tfOn ? 'bg-[#E3F6EE] text-[#0B5A43]' : 'bg-[#FEF3DC] text-[#8A5A00]'"><Icon name="shield" :size="18" /></span>
          <div><h2 class="text-base font-bold">Ikki bosqichli tasdiq (2FA)</h2><p class="text-[13px] text-muted">Parol o‘g‘irlansa ham hisob himoyada.</p></div>
        </div>
        <span class="chip" :class="tfOn ? 'bg-[#E3F6EE] text-[#0B5A43]' : 'bg-[#FEF3DC] text-[#8A5A00]'">{{ tfOn ? 'yoqilgan' : 'öçiq' }}</span>
      </div>
      <p class="text-[13px] leading-relaxed text-muted">Kirişda parol bilan birga telefondagi ilova (Google yoki Microsoft Authenticator) kodi soraladi.</p>
      <div v-if="tf.error" role="alert" class="rounded-xl bg-red-50 px-3.5 py-3 text-sm text-red-800">{{ tf.error }}</div>

      <template v-if="tf.step === 'codes'">
        <p class="text-sm font-semibold">Zaxira kodlar — hozir saqlab qoying, ular boşqa körsatilmaydi:</p>
        <ul class="grid grid-cols-2 gap-2 sm:grid-cols-4"><li v-for="c in tf.recovery" :key="c" class="rounded-lg bg-canvas px-3 py-2 text-center font-mono text-sm">{{ c }}</li></ul>
        <p class="text-[13px] text-muted">Telefonni yöqotsangiz, har bir kod bilan bir marta kiriş mumkin.</p>
        <div class="flex justify-end"><button type="button" class="btn-primary" @click="tf.step = 'idle'; tf.password = ''; tf.disableCode = ''">Saqladim</button></div>
      </template>

      <template v-else-if="tf.step === 'setup'">
        <ol class="list-decimal space-y-1.5 pl-5 text-sm">
          <li>Telefonda authenticator ilovasini oçing → «Kalit kiritiş» (qölda).</li>
          <li>Hisob: <b>{{ me?.username }}</b>, kalit: <code class="rounded bg-canvas px-2 py-0.5 font-mono text-[13px] select-all">{{ groupedSecret }}</code></li>
          <li>Ilovada körinayotgan 6 xonali kodni kiriting.</li>
        </ol>
        <p class="text-[13px] text-muted">Telefonda bu sahifani oçgan bölsangiz: <a :href="tf.uri" class="font-semibold text-brand-700">ilovada oçiş</a>.</p>
        <form class="flex flex-wrap items-end gap-3" @submit.prevent="tfEnable">
          <div class="min-w-[180px] flex-1"><label for="tf-code" class="label">Kod</label><input id="tf-code" v-model="tf.code" class="field font-mono tracking-[0.3em]" inputmode="numeric" autocomplete="one-time-code" maxlength="6" required></div>
          <button type="submit" class="btn-primary" :disabled="tf.busy || tf.code.trim().length !== 6">Yoqiş</button>
          <button type="button" class="btn-ghost" @click="tf.step = 'idle'">Bekor</button>
        </form>
      </template>

      <div v-else-if="!tfOn" class="mt-auto flex justify-end"><button type="button" class="btn-primary" @click="tfStart">Sozlaş</button></div>

      <form v-else class="flex flex-wrap items-end gap-3" @submit.prevent="tfDisable">
        <div class="min-w-[160px] flex-1"><label for="tf-pw" class="label">Parol</label><input id="tf-pw" v-model="tf.password" type="password" class="field" autocomplete="current-password" required></div>
        <div class="min-w-[160px] flex-1"><label for="tf-dc" class="label">Joriy kod yoki zaxira kod</label><input id="tf-dc" v-model="tf.disableCode" class="field font-mono" autocomplete="one-time-code" required></div>
        <button type="button" class="btn-ghost" :disabled="tf.busy" @click="tfNewCodes">Yangi zaxira kodlar</button>
        <button type="submit" class="btn-danger" :disabled="tf.busy">2FA ni öçiriş</button>
      </form>
    </section>
  </div>
</template>
