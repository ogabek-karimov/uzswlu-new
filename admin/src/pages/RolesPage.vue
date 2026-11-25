<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import PermissionMatrix from '@/components/PermissionMatrix.vue'
import { type Action, api, ApiError, type Paginated } from '@/lib/api'
import { actionsLabel, type PermissionSetDoc, type RoleDoc, SECTIONS } from '@/lib/roles'

// Superadmin rol yaratadi: har bo'lim uchun amallar (ko'rish / qo'shish / tahrirlash / o'chirish) va ruxsatlar kutubxonasidan to'plamlar.
// Rolning yakuniy ruxsati — o'z belgilari + to'plamlar yig'indisi (server ham shunday hisoblaydi).
const roles = ref<RoleDoc[]>([])
const sets = ref<PermissionSetDoc[]>([])
const editing = ref<number | 'new' | null>(null)
const error = ref('')
const message = ref('')
const saving = ref(false)
const form = reactive({ name: '', description: '', scoped: false, editAll: false, permissions: {} as Record<string, Action[]>, permissionSets: [] as number[] })
const current = computed(() => roles.value.find(r => r.id === editing.value))
const locked = computed(() => !!current.value?.system)

// Tanlangan to'plamlardan keladigan amallar (jadvalda kulrang ko'rinadi)
const inherited = computed(() => {
  const out: Record<string, Action[]> = {}
  for (const ps of sets.value.filter(x => form.permissionSets.includes(x.id))) {
    for (const [k, acts] of Object.entries(ps.permissions)) out[k] = [...new Set([...(out[k] ?? []), ...acts])]
  }
  return out
})

async function load() {
  const [r, s] = await Promise.all([
    api.get<Paginated<RoleDoc>>('/roles', { limit: 100 }),
    api.get<Paginated<PermissionSetDoc>>('/permission-sets', { limit: 200 }),
  ])
  roles.value = r.docs
  sets.value = s.docs
}
onMounted(load)

function pick(r: RoleDoc | null) {
  error.value = ''
  editing.value = r ? r.id : 'new'
  Object.assign(form, {
    name: r?.name ?? '', description: r?.description ?? '', scoped: r?.scoped ?? false, editAll: r?.editAll ?? false,
    permissions: JSON.parse(JSON.stringify(r?.permissions ?? { dashboard: ['read'] })), permissionSets: [...(r?.permissionSets ?? [])],
  })
}
function toggleSet(id: number) {
  if (locked.value) return
  form.permissionSets = form.permissionSets.includes(id) ? form.permissionSets.filter(x => x !== id) : [...form.permissionSets, id]
}

async function save() {
  error.value = ''
  if (!form.name.trim()) { error.value = 'Rol nomi majburiy'; return }
  saving.value = true
  try {
    const body = { name: form.name.trim(), description: form.description.trim(), scoped: form.scoped, editAll: form.editAll, permissions: form.permissions, permissionSets: form.permissionSets }
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
const eff = (r: RoleDoc) => r.effective ?? r.permissions
const count = (r: RoleDoc) => Object.keys(eff(r)).length
const setNames = (r: RoleDoc) => sets.value.filter(s => r.permissionSets?.includes(s.id)).map(s => s.name)
const preview = (r: RoleDoc) => SECTIONS.filter(s => eff(r)[s.key]).slice(0, 3).map(s => `${s.label}: ${actionsLabel(eff(r)[s.key])}`)
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Rollar va ruxsatlar</h1>
        <p class="mt-1.5 max-w-[720px] text-[15px] leading-relaxed text-muted">Har rol uçun har bölimda nima qiliş mumkinligini belgilang: körish, qöşiş, tahrirlaş, öçiriş. Tayyor töplamlarni <RouterLink to="/ruxsatlar" class="font-semibold text-brand-700 underline">Ruxsatlar</RouterLink> sahifasida yarating va rolga biriktiring.</p>
      </div>
      <button type="button" class="btn-primary h-[46px]" @click="pick(null)"><Icon name="plus" :size="16" />Yangi rol</button>
    </div>

    <p v-if="message" role="status" class="rounded-xl bg-mint/20 px-3.5 py-2.5 text-sm font-semibold">{{ message }}</p>

    <section v-if="editing !== null" class="card overflow-hidden border-2! border-brand-700!">
      <div class="flex items-center justify-between gap-3 bg-brand-50 px-5 py-4">
        <h2 class="text-base font-bold">{{ editing === 'new' ? 'Yangi rol' : current?.name }}</h2>
        <button type="button" aria-label="Yopiş" class="grid size-9 place-items-center rounded-full bg-white text-muted" @click="editing = null"><Icon name="x" :size="16" /></button>
      </div>
      <form class="grid gap-4 p-5" @submit.prevent="save">
        <div class="grid gap-3.5 sm:grid-cols-2">
          <div><label for="r-name" class="label">Nomi *</label><input id="r-name" v-model="form.name" class="field" required placeholder="Masalan: Matbuot xizmati"></div>
          <div><label for="r-desc" class="label">Izoh</label><input id="r-desc" v-model="form.description" class="field" placeholder="Bu rol nima qiladi"></div>
        </div>
        <p v-if="locked" class="rounded-xl bg-[#FEF3DC] px-3.5 py-2.5 text-sm text-[#8A5A00]">Superadmin rolining ruxsatlari qat’iy (aks holda hech kim kira olmay qolişi mümkin) — faqat nomi va izohini özgartirsa böladi.</p>

        <div v-if="!locked">
          <p class="label">Ruxsat töplamlari <span class="font-normal">(ixtiyoriy — tanlanganlari rolga qöşiladi)</span></p>
          <div v-if="sets.length" class="flex flex-wrap gap-2">
            <button
              v-for="s in sets" :key="s.id" type="button" :aria-pressed="form.permissionSets.includes(s.id)" :title="s.description || ''"
              class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[13px] font-semibold transition-colors"
              :class="form.permissionSets.includes(s.id) ? 'border-brand-700 bg-brand-700 text-white' : 'border-line bg-white text-ink hover:border-brand-700'"
              @click="toggleSet(s.id)"
            >{{ form.permissionSets.includes(s.id) ? '✓ ' : '+ ' }}{{ s.name }}</button>
          </div>
          <p v-else class="text-[13px] text-muted">Hali töplam yöq — <RouterLink to="/ruxsatlar" class="font-semibold text-brand-700 underline">Ruxsatlar</RouterLink> sahifasida yarating.</p>
        </div>

        <div>
          <p class="label">Bölimlar bo‘yiça amallar <span class="font-normal">— kulrang ✓ töplamdan keladi</span></p>
          <PermissionMatrix v-model="form.permissions" :disabled="locked" :inherited="inherited" />
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
            <button type="button" class="grid size-8 place-items-center rounded-lg border border-line text-muted hover:border-brand-700 hover:text-brand-700" :aria-label="`${r.name} — tahrirlaş`" title="Tahrirlaş" @click="pick(r)"><Icon name="edit" :size="14" /></button>
          </div>
        </div>
        <p class="text-[13px] leading-snug text-muted">{{ r.description || '—' }}</p>
        <ul class="flex flex-col gap-0.5 text-xs text-muted">
          <li v-for="line in preview(r)" :key="line">{{ line }}</li>
          <li v-if="count(r) > 3">… yana {{ count(r) - 3 }} ta bölim</li>
        </ul>
        <div v-if="setNames(r).length" class="flex flex-wrap gap-1"><span v-for="n in setNames(r)" :key="n" class="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700">{{ n }}</span></div>
        <p class="text-xs text-muted">{{ count(r) }} ta bölim · {{ r.users }} foydalanuvçi<span v-if="r.scoped"> · çegaralangan</span></p>
        <div class="mt-auto flex gap-2 pt-2">
          <button v-if="!r.system" type="button" class="btn-ghost h-9" @click="remove(r)">Öçirish</button>
        </div>
      </article>
    </div>
  </div>
</template>
