<script setup lang="ts">
import type { StaffProfile } from '#shared/types/api'

// Aloqa / Ijtimoiy tarmoqlar / Ilmiy profillar: ko'rish (Staff'dagi plitalar) va "Tahrirlash" —
// har bir maydon uchun kichik oyna va o'z "Saqlash" tugmasi; e-pochta bir nechta bo'lishi mumkin (oldingi saytdagidek)
type Kind = 'contacts' | 'socials' | 'science'
type Entry = { type: string; value: string }

const props = defineProps<{ kind: Kind; title: string; person: StaffProfile }>()
const emit = defineEmits<{ save: [entries: Entry[]] }>()

const { t } = useI18n()

// Maydonlar va namunalar (oldingi saytdagi dashboard maydonlari)
const FIELDS: Record<Kind, { type: string; label: string; placeholder: string; hint?: string; url?: boolean }[]> = {
  contacts: [
    { type: 'email', label: 'staff.contact.email', placeholder: 'name@uzswlu.uz' },
    { type: 'telegram', label: 'staff.contact.telegram', placeholder: '@username — https://t.me/…' },
    { type: 'whatsapp', label: 'staff.contact.whatsapp', placeholder: '+998 90 123 45 67' },
    { type: 'mobile', label: 'staff.contact.mobile', placeholder: '+998 90 123 45 67' },
    { type: 'phone', label: 'staff.contact.phone', placeholder: '+998 71 230 13 73' },
    { type: 'office', label: 'staff.contact.office', placeholder: 'Toşkent ş., …', hint: 'cabinet.links.officeHint' },
  ],
  socials: (['instagram', 'threads', 'facebook', 'linkedin', 'x', 'youtube'] as const).map(n => ({
    type: n, label: staffNetworks[n].label, placeholder: { instagram: 'https://instagram.com/…', threads: 'https://threads.net/@…', facebook: 'https://facebook.com/…', linkedin: 'https://linkedin.com/in/…', x: 'https://x.com/…', youtube: 'https://youtube.com/@…' }[n], url: true,
  })),
  science: (['orcid', 'scholar', 'scopus', 'researchgate'] as const).map(n => ({
    type: n, label: staffScience[n].label, placeholder: { orcid: 'https://orcid.org/0000-0000-0000-0000', scholar: 'https://scholar.google.com/…', scopus: 'https://www.scopus.com/…', researchgate: 'https://www.researchgate.net/profile/…' }[n], url: true,
  })),
}

/** Profil ma'lumoti → yozuvlar ro'yxati (turi + qiymati) */
const current = computed<Entry[]>(() => {
  if (props.kind === 'contacts') return props.person.contacts.map(c => ({ type: c.type, value: c.value }))
  const list = props.kind === 'socials' ? props.person.socials : props.person.science
  return list.map(s => ({ type: s.network, value: s.url }))
})
const tiles = computed(() => staffTiles(props.person, t)[props.kind])

// Tahrirlash: har bir qator alohida (e-pochtalar bir nechta qator)
const editing = ref(false)
const rows = ref<{ id: number; type: string; value: string; saved: boolean; error: boolean }[]>([])
let seq = 0
function start() {
  rows.value = FIELDS[props.kind].flatMap((f) => {
    const values = current.value.filter(e => e.type === f.type).map(e => e.value)
    return (values.length ? values : ['']).map(value => ({ id: seq++, type: f.type, value, saved: false, error: false }))
  })
  editing.value = true
}
const fieldOf = (type: string) => FIELDS[props.kind].find(f => f.type === type)!
const labelOf = (type: string) => {
  const f = fieldOf(type)
  return f.label.includes('.') ? t(f.label) : f.label
}

function addEmail() {
  const lastEmail = rows.value.map(r => r.type).lastIndexOf('email')
  rows.value.splice(lastEmail + 1, 0, { id: seq++, type: 'email', value: '', saved: false, error: false })
}

function valid(type: string, value: string) {
  if (!value) return true
  if (fieldOf(type).url) return /^https:\/\/\S+$/i.test(value)
  if (type === 'email') return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
  return true
}

/** "Saqlash" (bitta maydon): butun ro'yxat yuboriladi — bo'sh maydonlar chiqarib tashlanadi */
function saveRow(id: number) {
  const row = rows.value.find(r => r.id === id)!
  row.value = row.value.trim()
  row.error = !valid(row.type, row.value)
  if (row.error) return
  emit('save', rows.value.filter(r => r.value && valid(r.type, r.value)).map(r => ({ type: r.type, value: r.value })))
  row.saved = true
  setTimeout(() => { row.saved = false }, 2000)
}
</script>

<template>
  <StaffSection :title="title" :active="editing">
    <template #action>
      <button
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-sm font-semibold transition-colors"
        :class="editing ? 'bg-[#fdecec] text-[#c62828] hover:bg-[#fbd5d5]' : 'text-brand-700 hover:bg-brand-50'"
        @click="editing ? (editing = false) : start()"
      >
        <Icon :name="editing ? 'lucide:x' : 'lucide:square-pen'" class="size-4" />
        {{ editing ? t('cabinet.close') : t('cabinet.edit') }}
      </button>
    </template>

    <template v-if="!editing">
      <StaffTiles v-if="tiles.length" :tiles="tiles" class="mt-4.5" />
      <p v-else class="mt-3.5 text-muted">{{ t('cabinet.links.empty') }}</p>
    </template>

    <div v-else class="mt-4">
      <label v-for="row in rows" :key="row.id" class="mt-3.5 block text-[13px] text-muted first:mt-0">
        {{ labelOf(row.type) }}
        <span class="mt-1.5 flex gap-2.5">
          <input
            v-model="row.value"
            :type="row.type === 'email' ? 'email' : fieldOf(row.type).url ? 'url' : 'text'"
            :placeholder="fieldOf(row.type).placeholder"
            maxlength="300"
            class="h-12 min-w-0 flex-1 rounded-[14px] border bg-white px-3.5 text-[15px] text-ink outline-none focus:ring-4"
            :class="row.error ? 'border-[#c62828] focus:ring-[#c62828]/15' : 'border-line focus:border-accent-600 focus:ring-accent-600/15'"
            @input="row.error = false"
            @keydown.enter.prevent="saveRow(row.id)"
          >
          <button
            type="button"
            class="flex h-12 shrink-0 items-center gap-1.5 rounded-[14px] px-4 text-sm font-bold transition-colors"
            :class="row.saved ? 'bg-accent-100 text-accent-700' : 'bg-brand-900 text-white hover:bg-brand-800'"
            @click="saveRow(row.id)"
          >
            <Icon v-if="row.saved" name="lucide:check" class="size-4" />
            {{ row.saved ? t('cabinet.saved') : t('cabinet.save') }}
          </button>
        </span>
        <span v-if="row.error" class="mt-1.5 block text-xs text-[#c62828]">{{ t('cabinet.links.invalid') }}</span>
        <span v-else-if="fieldOf(row.type).hint" class="mt-1.5 block text-xs text-muted">{{ t(fieldOf(row.type).hint!) }}</span>
      </label>

      <div class="mt-4 flex flex-wrap gap-2.5">
        <button
          v-if="kind === 'contacts'"
          type="button"
          class="flex h-11 items-center gap-1.5 rounded-[14px] border border-dashed border-accent-600 bg-white px-4 text-sm font-semibold text-accent-600 transition-colors hover:bg-accent-100"
          @click="addEmail"
        >
          <Icon name="lucide:plus" class="size-4" />
          {{ t('cabinet.links.addEmail') }}
        </button>
        <button type="button" class="h-11 rounded-[14px] border border-line bg-white px-5 text-sm font-semibold text-ink transition-colors hover:border-accent-500" @click="editing = false">
          {{ t('cabinet.close') }}
        </button>
      </div>
    </div>
  </StaffSection>
</template>
