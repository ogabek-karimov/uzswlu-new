<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import { api, ApiError, type Paginated } from '@/lib/api'
import { HEMIS_ROLES, SECTIONS, type RoleDoc } from '@/lib/roles'

// Superadmin rol yaratadi: har bir bo'lim uchun «yöq / körish / yozish» tanlanadi
const roles = ref<RoleDoc[]>([])
const editing = ref<number | 'new' | null>(null)
const error = ref('')
const message = ref('')
const saving = ref(false)
const form = reactive({ name: '', description: '', scoped: false, editAll: false, hemisRole: '', permissions: {} as Record<string, string> })
const current = computed(() => roles.value.find(r => r.id === editing.value))
const locked = computed(() => !!current.value?.system)
const groups = [...new Set(SECTIONS.map(s => s.group))]

async function load() {
  roles.value = (await api.get<Paginated<RoleDoc>>('/roles', { limit: 100 })).docs
}
onMounted(load)

function pick(r: RoleDoc | null) {
  error.value = ''
  editing.value = r ? r.id : 'new'
  Object.assign(form, { name: r?.name ?? '', description: r?.description ?? '', scoped: r?.scoped ?? false, editAll: r?.editAll ?? false, hemisRole: r?.hemisRole ?? '', permissions: { ...(r?.permissions ?? { dashboard: 'read' }) } })
}

function setLevel(key: string, level: string) {
  if (locked.value) return
  if (level) form.permissions[key] = level
  else delete form.permissions[key]
}

async function save() {
  error.value = ''
  if (!form.name.trim()) { error.value = 'Rol nomi majburiy'; return }
  saving.value = true
  try {
    const body = { name: form.name.trim(), description: form.description.trim(), scoped: form.scoped, editAll: form.editAll, hemisRole: form.hemisRole, permissions: form.permissions }
    if (editing.value === 'new') await api.post('/roles', body)
    else await api.patch(`/roles/${editing.value}`, body)
    flash('Rol saqlandi')
    editing.value = null
    await load()
  }
  catch (e) {
    error.value = e instanceof ApiError ? e.message : 'Saqlab bölmadi'
  }
  finally { saving.value = false }
}

async function remove(r: RoleDoc) {
  if (!confirm(`«${r.name}» roli öçirilsinmi?` + (r.users ? ` ${r.users} ta foydalanuvçi ruxsatsiz qoladi (hisobi saqlanadi) — keyin ularga yangi rol bering.` : ''))) return
  try {
    await api.del(`/roles/${r.id}`)
    flash('Rol öçirildi')
    if (editing.value === r.id) editing.value = null
    await load()
  }
  catch (e) {
    flash(e instanceof ApiError ? e.message : 'Öçirib bölmadi')
  }
}

function flash(text: string) {
  message.value = text
  setTimeout(() => { if (message.value === text) message.value = '' }, 4000)
}
const count = (r: RoleDoc) => Object.keys(r.permissions).length
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Rollar va ruxsatlar</h1>
        <p class="mt-1.5 max-w-[700px] text-[15px] leading-relaxed text-muted">Har bir rol uçun qaysi bölimlar menyuda çiqishini belgilang. Foydalanuvçi kirganda faqat öz rolidagi bölimlarni kördi.</p>
      </div>
      <button type="button" class="btn-primary h-[46px]" @click="pick(null)"><Icon name="plus" :size="16" />Yangi rol</button>
    </div>

    <p v-if="message" role="status" class="rounded-xl bg-mint/20 px-3.5 py-2.5 text-sm font-semibold">{{ message }}</p>

    <section v-if="editing !== null" class="card overflow-hidden border-2! border-brand-700!">
      <div class="flex items-center justify-between gap-3 bg-brand-50 px-5 py-4">
        <h2 class="text-base font-bold">{{ editing === 'new' ? 'Yangi rol' : current?.name }}</h2>
        <button type="button" aria-label="Yopiş" class="grid size-9 place-items-center rounded-full bg-white text-muted" @click="editing = null"><Icon name="x" :size="16" /></button>
      </div>
      <form class="grid gap-3.5 p-5" @submit.prevent="save">
        <div class="grid gap-3.5 sm:grid-cols-2">
          <div><label for="r-name" class="label">Nomi *</label><input id="r-name" v-model="form.name" class="field" required placeholder="Masalan: Dekan"></div>
          <div><label for="r-desc" class="label">Izoh</label><input id="r-desc" v-model="form.description" class="field" placeholder="Bu rol nima qiladi"></div>
        </div>
        <p v-if="locked" class="rounded-xl bg-[#FEF3DC] px-3.5 py-2.5 text-sm text-[#8A5A00]">Superadmin rolining bölimlari qat’iy (aks holda hech kim kira olmay qolishi mümkin) — faqat nomi va izohini özgartirsa böladi.</p>
        <div v-for="g in groups" :key="g">
          <p class="mb-1.5 text-[11px] font-bold tracking-[0.14em] text-muted uppercase">{{ g }}</p>
          <div class="grid gap-1.5 sm:grid-cols-2">
            <div v-for="s in SECTIONS.filter(x => x.group === g)" :key="s.key" class="flex items-center justify-between gap-3 rounded-xl border border-field px-3.5 py-2">
              <span class="text-sm font-medium">{{ s.label }}</span>
              <select :value="form.permissions[s.key] ?? ''" :disabled="locked" class="field h-9! w-auto! text-[13px]!" :aria-label="`${s.label} ruxsati`" @change="setLevel(s.key, ($event.target as HTMLSelectElement).value)">
                <option value="">Yöq</option>
                <option value="read">Körish</option>
                <option value="write">Yozish</option>
              </select>
            </div>
          </div>
        </div>
        <div v-if="!locked" class="rounded-xl border border-field px-3.5 py-3">
          <label for="r-hemis" class="label">HEMIS lavozimi bo‘yicha avtomatik berish</label>
          <select id="r-hemis" v-model="form.hemisRole" class="field">
            <option value="">O‘chiq — hisobni qo‘lda yarataman</option>
            <option v-for="h in HEMIS_ROLES" :key="h.key" :value="h.key">{{ h.label }} — HEMIS orqali kirganda shu rol beriladi</option>
          </select>
          <p class="mt-1.5 text-xs leading-snug text-muted">Yoqilsa, shu lavozimdagi xodim HEMIS orqali kirganda hisob parolsiz o‘zi yaratiladi, rol va fakultet doirasi HEMIS bo‘yicha yangilanadi. Lavozim bog‘lanishi o‘chirilsa, avtomatik hisoblar yopiladi. Bir HEMIS lavozimi faqat bitta rolga bog‘lanadi.</p>
        </div>
        <label v-if="!locked" class="flex items-center gap-2.5 text-sm"><input v-model="form.scoped" type="checkbox" class="size-4">Faqat öz fakulteti/kafedrasi bilan çegaralansin (foydalanuvçida «qamrov» belgilanadi)</label>
        <label v-if="!locked" class="flex items-center gap-2.5 text-sm"><input v-model="form.editAll" type="checkbox" class="size-4">Boshqalarning yangilik, e’lon va tadbirlarini ham tahrirlay va öçira olsin (belgilanmasa — faqat özi yozganini)</label>
        <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <div class="flex justify-end gap-2.5">
          <button type="button" class="btn-ghost" @click="editing = null">Bekor qiliş</button>
          <button type="submit" class="btn-primary" :disabled="saving">Saqlaş</button>
        </div>
      </form>
    </section>

    <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="r in roles" :key="r.id" class="card flex flex-col gap-2 p-4">
        <div class="flex items-start justify-between gap-2">
          <b class="text-base">{{ r.name }}</b>
          <div class="flex shrink-0 items-center gap-1.5">
            <span v-if="r.system" class="rounded-full bg-[#F1F0F5] px-2 py-0.5 text-[11px] font-semibold text-muted">tizim</span>
            <span v-else-if="r.hemisRole" class="rounded-full bg-mint/20 px-2 py-0.5 text-[11px] font-semibold">HEMIS: {{ HEMIS_ROLES.find(h => h.key === r.hemisRole)?.label }}</span>
            <!-- Rollar sahifasi faqat superadmin uçun (rollar — PRIVATE kolleksiya): tahrirlaş belgisi barça rollarda -->
            <button type="button" class="grid size-8 place-items-center rounded-lg border border-line text-muted hover:border-brand-700 hover:text-brand-700" :aria-label="`${r.name} — tahrirlaş`" :title="'Tahrirlaş'" @click="pick(r)"><Icon name="edit" :size="14" /></button>
          </div>
        </div>
        <p class="text-[13px] leading-snug text-muted">{{ r.description || '—' }}</p>
        <p class="text-xs text-muted">{{ count(r) }} ta bölim · {{ r.users }} foydalanuvçi<span v-if="r.scoped"> · çegaralangan</span></p>
        <div class="mt-auto flex gap-2 pt-2">
          <button v-if="!r.system" type="button" class="btn-ghost h-9" @click="remove(r)">Öçirish</button>
        </div>
      </article>
    </div>
  </div>
</template>
