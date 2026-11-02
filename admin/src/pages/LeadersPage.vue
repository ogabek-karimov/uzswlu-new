<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated } from '@/lib/api'
import { initials } from '@/lib/auth'
import { LANGS, type Lang, SITE_URL } from '@/lib/constants'
import { mediaUrl } from '@/lib/posts'
import { useSortable } from '@/lib/sortable'
import Icon from '@/components/Icon.vue'
import ImageField from '@/components/ImageField.vue'

// Saytdagi "Rektorat" sahifasi: rektor, prorektorlar, matbuot kotibi
type Kind = 'rector' | 'prorector' | 'press'
type Leader = { id: number; kind: Kind; name: string; staffId?: string | null; photo?: MediaDoc | number | null; role: I18n; hours?: I18n; phone?: string | null; ext?: string | null; email?: string | null; reception?: boolean; order?: number | null }

const KINDS: { value: Kind; label: string }[] = [
  { value: 'rector', label: 'Rektor' },
  { value: 'prorector', label: 'Prorektor' },
  { value: 'press', label: 'Matbuot kotibi / maslahatçi' },
]
const COLORS = ['#110C2E', '#382B85', '#4C3FA0', '#2A2066', '#6D5FD3', '#1C1548', '#0E7A5A']

const people = ref<Leader[]>([])
const sel = ref<number | 'new' | null>(null)
const lang = ref<Lang>('uz')
const saving = ref(false)
const error = ref('')
const saved = ref(false)
const { bind, move, over } = useSortable(people, 'leaders')

const empty = () => ({ kind: 'prorector' as Kind, name: '', staffId: '', photo: null as MediaDoc | null, role: {} as I18n, hours: {} as I18n, phone: '', ext: '', email: '', reception: true })
const form = reactive(empty())

async function load() {
  people.value = (await api.get<Paginated<Leader>>('/leaders', { sort: 'order', limit: 100, depth: 1 })).docs
  if (sel.value === null && people.value[0]) pick(people.value[0].id)
}
onMounted(load)

function pick(id: number | 'new') {
  sel.value = id
  error.value = ''
  saved.value = false
  const p = id === 'new' ? null : people.value.find(x => x.id === id)
  Object.assign(form, empty(), p
    ? { kind: p.kind, name: p.name, staffId: p.staffId ?? '', photo: typeof p.photo === 'object' ? p.photo : null, role: { ...p.role }, hours: { ...(p.hours ?? {}) }, phone: p.phone ?? '', ext: p.ext ?? '', email: p.email ?? '', reception: p.reception !== false }
    : {})
}

const contact = (p: Leader) => [p.phone, p.ext ? `içki ${p.ext}` : '', p.email].filter(Boolean).join(' · ') || 'Aloqa ma’lumotlari kiritilmagan'
const current = computed(() => (typeof sel.value === 'number' ? people.value.find(p => p.id === sel.value) : null))

async function save() {
  if (!form.name.trim() || !form.role.uz?.trim()) { error.value = 'F.I.Ş. va özbekça lavozim majburiy'; return }
  saving.value = true
  error.value = ''
  const data = {
    kind: form.kind, name: form.name.trim(), staffId: form.staffId.trim() || null, photo: form.photo?.id ?? null,
    role: form.role, hours: form.hours, phone: form.phone.trim() || null, ext: form.ext.trim() || null, email: form.email.trim() || null, reception: form.reception,
  }
  try {
    if (sel.value === 'new') {
      const res = await api.post<{ doc: Leader }>('/leaders', { ...data, order: people.value.length + 1 })
      sel.value = res.doc.id
    }
    else await api.patch(`/leaders/${sel.value}`, data)
    await load()
    pick(sel.value as number)
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

async function remove() {
  if (typeof sel.value !== 'number' || !confirm(`${form.name} — rektorat sahifasidan olib taşlansinmi?`)) return
  await api.del(`/leaders/${sel.value}`)
  sel.value = null
  await load()
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Rahbariyat</h1>
        <p class="mt-1.5 text-[15px] text-muted">Saytdagi “Rektorat” sahifasi. Kartalarni surib tartibini özgartiring.</p>
      </div>
      <span class="flex gap-2">
        <a :href="`${SITE_URL}/rektorat`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
        <button type="button" class="btn-primary h-[46px]" @click="pick('new')"><Icon name="plus" :size="16" />Rahbar qöşiş</button>
      </span>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <ol class="flex min-w-0 flex-[999_1_560px] flex-col gap-2.5">
        <li
          v-for="(p, i) in people" :key="p.id" v-bind="bind(i)"
          class="flex items-center gap-3.5 rounded-[18px] bg-white px-4 py-3.5"
          :class="[sel === p.id ? 'border-2 border-brand-700' : 'border border-line', over === i && 'ring-2 ring-mint']"
        >
          <span aria-hidden="true" title="Surib köçiriş" class="cursor-grab tracking-[-2px] text-[#C9C5D6]">⋮⋮</span>
          <img v-if="mediaUrl(p.photo)" :src="mediaUrl(p.photo)!" alt="" class="size-[52px] shrink-0 rounded-full object-cover" draggable="false">
          <span v-else aria-hidden="true" class="grid size-[52px] shrink-0 place-items-center rounded-full font-bold text-white" :style="{ background: COLORS[i % COLORS.length] }">{{ initials(p.name) }}</span>
          <button type="button" class="min-w-0 flex-1 text-left" :aria-pressed="sel === p.id" @click="pick(p.id)">
            <span class="block text-[15px] font-bold">{{ p.name }}</span>
            <span class="mt-0.5 block text-[13px] leading-snug text-muted">{{ p.role.uz }}</span>
            <span class="mt-1 block text-xs text-subtle">{{ contact(p) }}</span>
          </button>
          <span class="chip shrink-0 text-[11px]!" :class="p.kind === 'rector' ? 'bg-brand-100 text-brand-800' : p.kind === 'press' ? 'bg-[#FEF3DC] text-[#8A5A00]' : 'bg-[#F1F0F5] text-muted'">{{ KINDS.find(k => k.value === p.kind)?.label.split(' /')[0] }}</span>
          <span class="flex shrink-0 flex-col">
            <button type="button" class="h-5 px-1 text-xs text-subtle" :aria-label="`${p.name} — yuqoriga`" :disabled="i === 0" @click="move(i, i - 1)">▲</button>
            <button type="button" class="h-5 px-1 text-xs text-subtle" :aria-label="`${p.name} — pastga`" :disabled="i === people.length - 1" @click="move(i, i + 1)">▼</button>
          </span>
        </li>
      </ol>

      <form v-if="sel !== null" class="card flex min-w-0 flex-[1_1_360px] flex-col gap-3 px-5 py-[18px]" @submit.prevent="save">
        <h2 class="text-base font-bold">{{ sel === 'new' ? 'Yangi rahbar' : 'Tahrirlaş' }}</h2>
        <div class="flex items-start gap-3.5">
          <div class="w-[96px] shrink-0"><ImageField v-model="form.photo" compact folder="staff" label="Rasm" /></div>
          <div class="flex min-w-0 flex-1 flex-col gap-2.5">
            <div><label for="ld-name" class="label">F.I.Ş. *</label><input id="ld-name" v-model="form.name" class="field" required></div>
            <div><label for="ld-kind" class="label">Turi</label><select id="ld-kind" v-model="form.kind" class="field"><option v-for="k in KINDS" :key="k.value" :value="k.value">{{ k.label }}</option></select></div>
          </div>
        </div>
        <div><label for="ld-staff" class="label">Xodim ID <span class="font-normal">(HEMIS · Staff sahifasiga havola, ixtiyoriy)</span></label><input id="ld-staff" v-model="form.staffId" class="field" inputmode="numeric" placeholder="Masalan: 9300"></div>
        <div>
          <div class="mb-1.5 flex items-center justify-between gap-2">
            <span class="label mb-0!">Lavozim va qabul vaqti</span>
            <div role="tablist" aria-label="Til" class="flex gap-1">
              <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
            </div>
          </div>
          <textarea v-model="form.role[lang]" rows="2" class="field h-auto! py-2.5 leading-normal" :aria-label="`Lavozim · ${lang}`" :required="lang === 'uz'" />
          <input v-model="form.hours[lang]" class="field mt-2" :aria-label="`Qabul kuni va vaqti · ${lang}`" placeholder="Qabul kuni va vaqti (24 soat): Duşanba, 15:00–17:00">
        </div>
        <div class="grid grid-cols-2 gap-2.5">
          <div><label for="ld-ph" class="label">Telefon</label><input id="ld-ph" v-model="form.phone" class="field" type="tel" placeholder="+998 71 230 12 91"></div>
          <div><label for="ld-ext" class="label">Içki raqam</label><input id="ld-ext" v-model="form.ext" class="field" inputmode="numeric"></div>
        </div>
        <div><label for="ld-mail" class="label">E-poçta</label><input id="ld-mail" v-model="form.email" class="field" type="email"></div>
        <label class="flex items-center gap-2.5 text-[13px] text-[#3D3958]"><input v-model="form.reception" type="checkbox" class="size-[18px] accent-brand-800"> “Virtual qabulxona” formasida körsatiş</label>
        <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <p v-else-if="saved" class="rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi — saytda yangilandi.</p>
        <div class="flex justify-end gap-2">
          <button v-if="current" type="button" class="btn-danger h-[42px]!" @click="remove">Olib taşlaş</button>
          <button type="submit" class="btn-primary h-[42px]!" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>
