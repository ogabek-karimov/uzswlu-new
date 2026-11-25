<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import PermissionMatrix from '@/components/PermissionMatrix.vue'
import { type Action, api, ApiError, type Paginated } from '@/lib/api'
import { actionsLabel, type PermissionSetDoc, SECTIONS } from '@/lib/roles'

// Ruxsatlar kutubxonasi (faqat superadmin): qayta ishlatiladigan to'plamlar — masalan, «Yangilik muharriri» (yangiliklar: ko'rish,
// qo'shish, tahrirlash). «Rollar» sahifasida rolga bir nechta to'plam biriktiriladi; to'plam o'zgarsa — unga bog'langan rollar ham o'zgaradi.
const sets = ref<PermissionSetDoc[]>([])
const editing = ref<number | 'new' | null>(null)
const form = reactive({ name: '', description: '', permissions: {} as Record<string, Action[]> })
const error = ref('')
const message = ref('')
const saving = ref(false)
const current = computed(() => sets.value.find(s => s.id === editing.value))

async function load() {
  sets.value = (await api.get<Paginated<PermissionSetDoc>>('/permission-sets', { limit: 200 })).docs
}
onMounted(load)

function pick(s: PermissionSetDoc | null) {
  error.value = ''
  editing.value = s ? s.id : 'new'
  Object.assign(form, { name: s?.name ?? '', description: s?.description ?? '', permissions: JSON.parse(JSON.stringify(s?.permissions ?? {})) })
}

async function save() {
  error.value = ''
  if (!form.name.trim()) { error.value = 'To‘plam nomi majburiy'; return }
  if (!Object.keys(form.permissions).length) { error.value = 'Kamida bitta bölimda amal belgilang'; return }
  saving.value = true
  try {
    const body = { name: form.name.trim(), description: form.description.trim(), permissions: form.permissions }
    if (editing.value === 'new') await api.post('/permission-sets', body)
    else await api.patch(`/permission-sets/${editing.value}`, body)
    flash('Töplam saqlandi')
    editing.value = null
    await load()
  }
  catch (e) { error.value = e instanceof ApiError ? e.message : 'Saqlab bölmadi' }
  finally { saving.value = false }
}

async function remove(s: PermissionSetDoc) {
  if (!confirm(`«${s.name}» töplami öçirilsinmi?` + (s.roles ? ` U ${s.roles} ta roldan olib taşlanadi (rollarning öz belgilari qoladi).` : ''))) return
  try {
    await api.del(`/permission-sets/${s.id}`)
    flash('Töplam öçirildi')
    if (editing.value === s.id) editing.value = null
    await load()
  }
  catch (e) { flash(e instanceof ApiError ? e.message : 'Öçirib bölmadi') }
}

function flash(text: string) {
  message.value = text
  setTimeout(() => { if (message.value === text) message.value = '' }, 4000)
}
const lines = (s: PermissionSetDoc) => SECTIONS.filter(x => s.permissions[x.key]).map(x => `${x.label}: ${actionsLabel(s.permissions[x.key])}`)
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Ruxsatlar</h1>
        <p class="mt-1.5 max-w-[720px] text-[15px] leading-relaxed text-muted">Tayyor ruxsat töplamlari: bir marta yarating — keyin <RouterLink to="/rollar" class="font-semibold text-brand-700 underline">Rollar</RouterLink> sahifasida istalgan rolga biriktiring. Töplam özgarsa, u biriktirilgan rollar ham darhol özgaradi.</p>
      </div>
      <button type="button" class="btn-primary h-[46px]" @click="pick(null)"><Icon name="plus" :size="16" />Yangi töplam</button>
    </div>

    <p v-if="message" role="status" class="rounded-xl bg-mint/20 px-3.5 py-2.5 text-sm font-semibold">{{ message }}</p>

    <section v-if="editing !== null" class="card overflow-hidden border-2! border-brand-700!">
      <div class="flex items-center justify-between gap-3 bg-brand-50 px-5 py-4">
        <h2 class="text-base font-bold">{{ editing === 'new' ? 'Yangi töplam' : current?.name }}</h2>
        <button type="button" aria-label="Yopiş" class="grid size-9 place-items-center rounded-full bg-white text-muted" @click="editing = null"><Icon name="x" :size="16" /></button>
      </div>
      <form class="grid gap-4 p-5" @submit.prevent="save">
        <div class="grid gap-3.5 sm:grid-cols-2">
          <div><label for="ps-name" class="label">Nomi *</label><input id="ps-name" v-model="form.name" class="field" required placeholder="Masalan: Yangilik muharriri"></div>
          <div><label for="ps-desc" class="label">Izoh</label><input id="ps-desc" v-model="form.description" class="field" placeholder="Nimaga ruxsat beradi"></div>
        </div>
        <div>
          <p class="label">Bölimlar bo‘yiça amallar</p>
          <PermissionMatrix v-model="form.permissions" />
        </div>
        <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <div class="flex justify-end gap-2.5">
          <button type="button" class="btn-ghost" @click="editing = null">Bekor qiliş</button>
          <button type="submit" class="btn-primary" :disabled="saving">Saqlaş</button>
        </div>
      </form>
    </section>

    <p v-if="!sets.length && editing === null" class="card px-5 py-10 text-center text-sm text-muted">Hali töplam yöq. «Yangi töplam» bilan boşlang — masalan, «Yangilik muharriri»: yangiliklar — köriş, qöşiş, tahrirlaş.</p>
    <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="s in sets" :key="s.id" class="card flex flex-col gap-2 p-4">
        <div class="flex items-start justify-between gap-2">
          <b class="text-base">{{ s.name }}</b>
          <button type="button" class="grid size-8 shrink-0 place-items-center rounded-lg border border-line text-muted hover:border-brand-700 hover:text-brand-700" :aria-label="`${s.name} — tahrirlaş`" title="Tahrirlaş" @click="pick(s)"><Icon name="edit" :size="14" /></button>
        </div>
        <p class="text-[13px] leading-snug text-muted">{{ s.description || '—' }}</p>
        <ul class="flex flex-col gap-0.5 text-xs text-muted"><li v-for="l in lines(s)" :key="l">{{ l }}</li></ul>
        <p class="text-xs text-muted">{{ s.roles }} ta rolga biriktirilgan</p>
        <div class="mt-auto pt-2"><button type="button" class="btn-ghost h-9" @click="remove(s)">Öçirish</button></div>
      </article>
    </div>
  </div>
</template>
