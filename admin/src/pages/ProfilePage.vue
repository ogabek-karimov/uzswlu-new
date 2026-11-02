<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { api, ApiError } from '@/lib/api'
import { auth, initials, ROLE_LABELS } from '@/lib/auth'

const me = auth.user
const info = reactive({ name: me.value?.name ?? '', position: me.value?.position ?? '', department: me.value?.department ?? '' })
const pw = reactive({ current: '', next: '', repeat: '' })
const message = ref('')
const error = ref('')

const checks = computed(() => [
  [pw.next.length >= 10, 'Kamida 10 ta belgi'],
  [/[A-Z]/.test(pw.next) && /[a-z]/.test(pw.next), 'Katta va kiçik harf'],
  [/\d/.test(pw.next), 'Kamida bitta raqam'],
  [/[^A-Za-z0-9]/.test(pw.next), 'Belgi: ! ? # @ …'],
] as [boolean, string][])
const score = computed(() => checks.value.filter(c => c[0]).length)
const LEVEL = [['Juda kuçsiz', '#B42318'], ['Kuçsiz', '#B42318'], ['Örtaça', '#8A5A00'], ['Yaxşi', '#0E7A5A'], ['Kuçli', '#0B5A43']]

async function saveInfo() {
  try {
    await api.patch(`/users/${me.value!.id}`, info)
    await auth.me()
    flash('Ma’lumotlar saqlandi')
  }
  catch (e) {
    error.value = e instanceof ApiError ? e.message : 'Saqlab bölmadi'
  }
}

async function changePassword() {
  error.value = ''
  if (pw.next !== pw.repeat) { error.value = 'Yangi parollar bir xil emas'; return }
  if (pw.next.length < 10) { error.value = 'Parol kamida 10 ta belgidan iborat bölsin'; return }
  try {
    // Avval hozirgi parol tekshiriladi
    await api.post('/users/login', { username: me.value!.username, password: pw.current })
    await api.patch(`/users/${me.value!.id}`, { password: pw.next })
    await api.post('/users/login', { username: me.value!.username, password: pw.next })
    Object.assign(pw, { current: '', next: '', repeat: '' })
    flash('Parol almaştirildi')
  }
  catch (e) {
    error.value = e instanceof ApiError && e.status === 401 ? 'Hozirgi parol notöğri' : (e as Error).message
  }
}

function flash(text: string) {
  message.value = text
  setTimeout(() => { if (message.value === text) message.value = '' }, 3000)
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <section class="card overflow-hidden">
      <div class="relative h-[110px] overflow-hidden bg-night"><span aria-hidden="true" class="absolute -top-36 -right-20 size-[360px] rounded-full border-[44px] border-mint/8" /></div>
      <div class="-mt-11 flex flex-wrap items-end gap-[18px] px-6 pb-[22px]">
        <span class="grid size-24 place-items-center rounded-full bg-gradient-to-br from-brand-700 to-night text-[34px] font-bold text-mint shadow-[0_0_0_5px_#fff]">{{ initials(me?.name) }}</span>
        <div class="flex-[1_1_260px] pb-1">
          <h1 class="text-[26px] font-bold">{{ me?.name }}</h1>
          <p class="mt-1 text-sm text-muted">{{ ROLE_LABELS[me?.role ?? 'editor'] }} · login: <b>{{ me?.username }}</b></p>
        </div>
      </div>
    </section>

    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{{ error }}</p>

    <div class="flex flex-wrap items-start gap-5">
      <section class="card flex min-w-0 flex-[1_1_420px] flex-col gap-3.5 p-[22px]">
        <h2 class="text-base font-bold">Ma’lumotlarim</h2>
        <p class="-mt-2 text-[13px] text-muted">Yangilik muallifi sifatida saytda şu ism va lavozim çiqadi.</p>
        <div><label for="pr-name" class="label">F.I.Ş.</label><input id="pr-name" v-model="info.name" class="field"></div>
        <div class="grid gap-3.5 sm:grid-cols-2">
          <div><label for="pr-pos" class="label">Lavozim</label><input id="pr-pos" v-model="info.position" class="field" placeholder="Masalan: Matbuot xizmati"></div>
          <div><label for="pr-dep" class="label">Bölim</label><input id="pr-dep" v-model="info.department" class="field"></div>
        </div>
        <div class="flex justify-end"><button type="button" class="btn-primary" @click="saveInfo">Saqlaş</button></div>
      </section>

      <section class="card flex min-w-0 flex-[1_1_420px] flex-col gap-3.5 p-[22px]">
        <h2 class="text-base font-bold">Parolni almaştiriş</h2>
        <form class="flex flex-col gap-3.5" @submit.prevent="changePassword">
          <input :value="me?.username" autocomplete="username" class="hidden" readonly>
          <div><label for="pw-cur" class="label">Hozirgi parol</label><input id="pw-cur" v-model="pw.current" type="password" class="field" autocomplete="current-password" required></div>
          <div>
            <label for="pw-new" class="label">Yangi parol</label><input id="pw-new" v-model="pw.next" type="password" class="field" autocomplete="new-password" required>
            <div aria-hidden="true" class="mt-2.5 grid grid-cols-4 gap-1.5"><span v-for="i in 4" :key="i" class="h-1.5 rounded-full" :style="{ background: i <= score ? LEVEL[score]![1] : '#ECEAF3' }" /></div>
            <p class="mt-2 text-[13px] font-semibold" :style="{ color: LEVEL[score]![1] }">Parol kuçi: {{ LEVEL[score]![0] }}</p>
          </div>
          <ul class="grid grid-cols-2 gap-x-3.5 gap-y-1.5 text-[13px]">
            <li v-for="c in checks" :key="c[1]" class="flex items-center gap-2" :class="c[0] ? 'text-[#0B5A43]' : 'text-subtle'"><span aria-hidden="true" class="font-bold">{{ c[0] ? '✓' : '○' }}</span>{{ c[1] }}</li>
          </ul>
          <div><label for="pw-rep" class="label">Yangi parolni takrorlang</label><input id="pw-rep" v-model="pw.repeat" type="password" class="field" autocomplete="new-password" required></div>
          <div class="flex justify-end"><button type="submit" class="btn-primary">Parolni saqlaş</button></div>
        </form>
      </section>
    </div>

    <div v-if="message" role="status" class="fixed right-6 bottom-6 z-50 rounded-2xl bg-night px-4 py-3 text-sm font-semibold text-white shadow-xl">{{ message }}</div>
  </div>
</template>
