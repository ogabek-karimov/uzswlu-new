<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import { api, ApiError, type Paginated, type User } from '@/lib/api'
import { auth, initials, ROLE_LABELS } from '@/lib/auth'
import { relative } from '@/lib/format'

const users = ref<User[]>([])
const lastLogin = ref<Record<number, string>>({})
const open = ref(false)
const error = ref('')
const message = ref('')
const form = reactive({ name: '', username: '', password: '', role: 'editor' as User['role'], position: '', scope: '' })

const ROLE_SCOPE: Record<User['role'], string> = {
  superadmin: 'Hammasi, adminlarni tayinlaş va sozlamalar',
  editor: 'Yangiliklar, e’lonlar, tadbirlar, media',
  faculty: 'Faqat öz fakulteti sahifasi va yangiliklari',
  pages: 'Sahifalar, hujjatlar, video darsliklar',
  sdg: 'Faqat BRM: 17 maqsad matni, rasmlari va PDF hisobotlari',
}
const STATUS: Record<string, [string, string]> = {
  active: ['Faol', 'bg-[#DDFBF0] text-[#0B5A43]'],
  invited: ['Taklif qilingan', 'bg-[#FEF3DC] text-[#8A5A00]'],
  disabled: ['Yopilgan', 'bg-[#F1F0F5] text-muted'],
}

async function load() {
  users.value = (await api.get<Paginated<User>>('/users', { limit: 200, sort: 'name', depth: 0 })).docs
  const events = await api.get<Paginated<{ user: number | null; createdAt: string }>>('/login-events', { where: { result: { equals: 'success' } }, sort: '-createdAt', limit: 300, depth: 0 })
  const map: Record<number, string> = {}
  for (const e of events.docs) if (e.user && !map[e.user]) map[e.user] = e.createdAt
  lastLogin.value = map
}
onMounted(load)

function genPassword() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
  const bytes = crypto.getRandomValues(new Uint8Array(12))
  form.password = [...bytes].map(b => chars[b % chars.length]).join('')
}

async function create() {
  error.value = ''
  try {
    await api.post('/users', { ...form, status: 'active' })
    flash(`${form.name} qöşildi. Login va parolni unga xavfsiz yöl bilan bering.`)
    Object.assign(form, { name: '', username: '', password: '', role: 'editor', position: '', scope: '' })
    open.value = false
    await load()
  }
  catch (e) {
    error.value = e instanceof ApiError ? e.message : 'Saqlab bölmadi'
  }
}

async function update(u: User, data: Partial<User> & { password?: string }, done: string) {
  try {
    await api.patch(`/users/${u.id}`, data)
    flash(done)
    await load()
  }
  catch (e) {
    flash(e instanceof ApiError ? e.message : 'Xato')
  }
}

async function resetPassword(u: User) {
  const pw = window.prompt(`${u.name} uçun yangi parol (kamida 10 belgi):`)
  if (!pw) return
  if (pw.length < 10) return flash('Parol juda qisqa — kamida 10 belgi')
  await update(u, { password: pw }, 'Parol almaştirildi')
}

async function unlock(u: User) {
  await api.post('/users/unlock', { username: u.username })
  flash('Blokdan çiqarildi')
  await load()
}

async function resetTwoFactor(u: User) {
  if (!confirm(`${u.name} uçun 2FA bekor qilinsinmi? Foydalanuvchi uni qaytadan sozlaydi.`)) return
  await api.post('/users/2fa/reset', { username: u.username })
  flash('2FA bekor qilindi')
  await load()
}

function flash(text: string) {
  message.value = text
  setTimeout(() => { if (message.value === text) message.value = '' }, 4000)
}

const locked = (u: User) => !!u.lockUntil && new Date(u.lockUntil).getTime() > Date.now()
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Foydalanuvçilar va rollar</h1>
        <p class="mt-1.5 max-w-[700px] text-[15px] leading-relaxed text-muted">Adminlar login va parol bilan kiradi. HEMIS ulangandan keyin muharrirlar HEMIS orqali kiradi — rasm va lavozimi öz-özidan olinadi.</p>
      </div>
      <button type="button" class="btn-primary h-[46px]" :aria-expanded="open" @click="open = !open"><Icon name="plus" :size="16" />Admin qöşiş</button>
    </div>

    <section v-if="open" class="card overflow-hidden border-2! border-brand-700!">
      <div class="flex items-center justify-between gap-3 bg-brand-50 px-5 py-4">
        <h2 class="text-base font-bold">Yangi admin</h2>
        <button type="button" aria-label="Yopiş" class="grid size-9 place-items-center rounded-full bg-white text-muted" @click="open = false"><Icon name="x" :size="16" /></button>
      </div>
      <form class="grid gap-3.5 p-5 sm:grid-cols-2" @submit.prevent="create">
        <div><label for="u-name" class="label">F.I.Ş. *</label><input id="u-name" v-model="form.name" class="field" required placeholder="Masalan: Karimova Dilnoza"></div>
        <div><label for="u-pos" class="label">Lavozim</label><input id="u-pos" v-model="form.position" class="field" placeholder="Masalan: Matbuot xizmati"></div>
        <div><label for="u-login" class="label">Login *</label><input id="u-login" v-model="form.username" class="field" required autocomplete="off" pattern="[A-Za-z0-9._-]{3,40}" title="Lotin harflari, raqam, nuqta va çiziqça"></div>
        <div>
          <label for="u-pw" class="label">Parol * <span class="font-normal">(kamida 10 belgi)</span></label>
          <div class="flex gap-2"><input id="u-pw" v-model="form.password" class="field font-mono" required minlength="10" autocomplete="new-password"><button type="button" class="btn-ghost shrink-0" @click="genPassword">Yaratiş</button></div>
        </div>
        <div class="sm:col-span-2">
          <span class="label">Rol</span>
          <div role="radiogroup" aria-label="Rol" class="grid gap-2 sm:grid-cols-3 xl:grid-cols-5">
            <button
              v-for="(label, r) in ROLE_LABELS" :key="r" type="button" role="radio" :aria-checked="form.role === r"
              class="min-h-[76px] rounded-[14px] px-3.5 py-3 text-left" :class="form.role === r ? 'border-2 border-brand-700 bg-brand-50' : 'border border-field bg-white'"
              @click="form.role = r"
            ><b class="block text-sm">{{ label }}</b><span class="mt-1 block text-xs leading-snug text-muted">{{ ROLE_SCOPE[r] }}</span></button>
          </div>
        </div>
        <div v-if="form.role === 'faculty'" class="sm:col-span-2"><label for="u-scope" class="label">Qaysi fakultet?</label><input id="u-scope" v-model="form.scope" class="field" placeholder="Masalan: Ingliz filologiyasi fakulteti"></div>
        <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800 sm:col-span-2">{{ error }}</p>
        <div class="flex justify-end gap-2.5 sm:col-span-2">
          <button type="button" class="btn-ghost" @click="open = false">Bekor qiliş</button>
          <button type="submit" class="btn-primary">Saqlaş</button>
        </div>
      </form>
    </section>

    <section class="card overflow-hidden">
      <div class="px-5 py-4"><h2 class="text-base font-bold">Adminlar <span class="font-medium text-subtle">· {{ users.length }}</span></h2></div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[960px] border-collapse text-sm">
          <thead>
            <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
              <th class="px-5 py-3 font-semibold">Xodim</th>
              <th class="px-3.5 py-3 font-semibold">Rol</th>
              <th class="px-3.5 py-3 font-semibold">Oxirgi kiriş</th>
              <th class="px-3.5 py-3 font-semibold">Holati</th>
              <th class="px-5 py-3 font-semibold"><span class="sr-only">Amallar</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" class="border-t border-[#F0EEF6] hover:bg-[#FAF9FD]">
              <td class="px-5 py-3.5">
                <span class="flex items-center gap-3">
                  <span class="grid size-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-700 to-night text-[13px] font-bold text-mint" :class="u.status === 'disabled' && 'opacity-50'">{{ initials(u.name) }}</span>
                  <span class="leading-snug"><b class="block">{{ u.name }} <span v-if="u.id === auth.user.value?.id" class="text-xs font-semibold text-mint-text">· siz</span></b><span class="text-xs text-muted">{{ u.username }}{{ u.position ? ` · ${u.position}` : '' }}</span></span>
                </span>
              </td>
              <td class="px-3.5 py-3.5">
                <select :value="u.role" :disabled="u.id === auth.user.value?.id" class="field h-9! w-auto! text-[13px]!" :aria-label="`${u.name} roli`" @change="update(u, { role: ($event.target as HTMLSelectElement).value as User['role'] }, 'Rol özgartirildi')">
                  <option v-for="(label, r) in ROLE_LABELS" :key="r" :value="r">{{ label }}</option>
                </select>
              </td>
              <td class="px-3.5 py-3.5 whitespace-nowrap text-muted tabular-nums">{{ lastLogin[u.id] ? relative(lastLogin[u.id]) : 'hali kirmagan' }}</td>
              <td class="px-3.5 py-3.5 whitespace-nowrap">
                <span class="chip" :class="STATUS[u.status ?? 'active']![1]">{{ STATUS[u.status ?? 'active']![0] }}</span>
                <span v-if="locked(u)" class="chip ml-1 bg-red-50 text-red-700">bloklangan</span>
              </td>
              <td class="px-5 py-3.5 text-right whitespace-nowrap">
                <button v-if="locked(u)" type="button" class="btn-ghost h-8! px-3! text-xs!" @click="unlock(u)">Blokdan çiqariş</button>
                <button type="button" class="btn-ghost ml-1 h-8! px-3! text-xs!" @click="resetPassword(u)">Parol</button>
                <button v-if="u.twoFactorEnabled" type="button" class="btn-ghost ml-1 h-8! px-3! text-xs!" title="Telefon yoqotilgan bölsa" @click="resetTwoFactor(u)">2FA</button>
                <button
                  v-if="u.id !== auth.user.value?.id" type="button" class="ml-1 h-8! px-3! text-xs!" :class="u.status === 'disabled' ? 'btn-ghost' : 'btn-danger'"
                  @click="update(u, { status: u.status === 'disabled' ? 'active' : 'disabled' }, u.status === 'disabled' ? 'Hisob oçildi' : 'Hisob yopildi')"
                >{{ u.status === 'disabled' ? 'Oçiş' : 'Yopiş' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="message" role="status" class="fixed right-6 bottom-6 z-50 max-w-sm rounded-2xl bg-night px-4 py-3 text-sm font-semibold text-white shadow-xl">{{ message }}</div>
  </div>
</template>
