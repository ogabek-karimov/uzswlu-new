<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, type Paginated } from '@/lib/api'
import Icon from '@/components/Icon.vue'

// Murojaatlarda (virtual qabulxona) taqiqlangan haqoratli so'zlar: qo'shish, tahrirlash, vaqtincha o'chirish, o'chirish
type Word = { id: number; word: string; lang: Lang; active: boolean }
type Lang = 'uz' | 'ru' | 'en' | 'zh'
const LANGS: { key: Lang; label: string }[] = [
  { key: 'uz', label: 'Özbekça' }, { key: 'ru', label: 'Rusça' }, { key: 'en', label: 'Inglizça' }, { key: 'zh', label: 'Xitoyça' },
]
const langLabel = (l: Lang) => LANGS.find(x => x.key === l)?.label ?? l

const items = ref<Word[]>([])
const loaded = ref(false)
const query = ref('')
const filter = ref<Lang | 'all'>('all')
const word = ref('')
const lang = ref<Lang>('uz')
const editing = ref<number | null>(null)
const saving = ref(false)
const error = ref('')
const notice = ref('')

async function load() {
  const r = await api.get<Paginated<Word>>('/rude-words', { sort: 'word', limit: 2000 })
  items.value = r.docs
  loaded.value = true
}
onMounted(load)

const counts = computed(() => Object.fromEntries(LANGS.map(l => [l.key, items.value.filter(w => w.lang === l.key).length])) as Record<Lang, number>)
const shown = computed(() => {
  const q = query.value.trim().toLowerCase()
  return items.value.filter(w => (filter.value === 'all' || w.lang === filter.value) && (!q || w.word.includes(q)))
})

function edit(w: Word | null) {
  editing.value = w?.id ?? null
  word.value = w?.word ?? ''
  lang.value = w?.lang ?? (filter.value === 'all' ? 'uz' : filter.value)
  error.value = ''
}

async function save() {
  const value = word.value.trim().toLowerCase()
  if (value.replace(/\*/g, '').length < 2 || /\s/.test(value)) { error.value = 'Söz kamida 2 harf, böş joysiz bölsin'; return }
  saving.value = true
  error.value = ''
  try {
    if (editing.value) await api.patch(`/rude-words/${editing.value}`, { word: value, lang: lang.value })
    else await api.post('/rude-words', { word: value, lang: lang.value, active: true })
    notice.value = editing.value ? `«${value}» saqlandi` : `«${value}» qöşildi`
    await load()
    edit(null)
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

async function toggle(w: Word) {
  await api.patch(`/rude-words/${w.id}`, { active: !w.active })
  w.active = !w.active
}

async function remove(w: Word) {
  if (!confirm(`«${w.word}» röyxatdan öçirilsinmi?`)) return
  await api.del(`/rude-words/${w.id}`)
  if (editing.value === w.id) edit(null)
  await load()
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Haqoratli sözlar</h1>
      <p class="mt-1.5 max-w-3xl text-[15px] text-muted">
        Virtual qabulxona murojaatida bu sözlar yozilsa, söz qizil bilan belgilanadi va murojaat yuborilmaydi. Özgarişlar saytda bir necha soniyada kuçga kiradi.
      </p>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <form class="card min-w-0 flex-[1_1_340px] px-5 py-[18px] lg:sticky lg:top-4" @submit.prevent="save">
        <h2 class="text-lg font-bold">{{ editing ? 'Sözni tahrirlaş' : 'Yangi söz qöşiş' }}</h2>
        <div class="mt-3.5 grid gap-3.5">
          <div>
            <label for="rw-word" class="label">Söz</label>
            <input id="rw-word" v-model="word" class="field text-[16px]" placeholder="masalan: ahmoq*" autocomplete="off">
          </div>
          <div>
            <p class="label">Til</p>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="l in LANGS"
                :key="l.key"
                type="button"
                class="h-11 rounded-[12px] border-2 text-sm font-semibold transition"
                :class="lang === l.key ? 'border-brand-700 bg-brand-50 text-brand-800' : 'border-[#ECEAF3] text-muted'"
                @click="lang = l.key"
              >{{ l.label }}</button>
            </div>
          </div>
        </div>
        <div class="mt-4 rounded-[12px] bg-[#F5F3FE] px-3.5 py-3 text-[13px] leading-relaxed text-ink/80">
          <b>Qanday yoziladi:</b>
          <ul class="mt-1 list-disc pl-4">
            <li><b>ahmoq</b> — faqat aynan şu söz.</li>
            <li><b>ahmoq*</b> — şu bilan boşlanuvçi hamma sözlar (ahmoqsan, ahmoqlik).</li>
            <li>Ruscha sözni kirillda yozing — lotincha yozilişi (masalan «blyad», «nahuy») ham avtomatik uşlanadi.</li>
            <li>Katta-kiçik harf, «0/1/@» bilan yaşiriş ham hisobga olinadi.</li>
          </ul>
        </div>
        <p v-if="error" class="mt-3 text-sm font-semibold text-[#C5192D]" role="alert">{{ error }}</p>
        <p v-else-if="notice" class="mt-3 text-sm font-semibold text-[#0B5A43]" role="status">{{ notice }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button class="btn-primary h-[46px] gap-2" :disabled="saving"><Icon :name="editing ? 'check' : 'plus'" :size="18" /> {{ saving ? 'Saqlanmoqda…' : editing ? 'Saqlaş' : 'Qöşiş' }}</button>
          <button v-if="editing" type="button" class="btn-ghost h-[46px]" @click="edit(null)">Bekor qiliş</button>
        </div>
      </form>

      <section class="card min-w-0 flex-[2_1_520px] px-5 py-[18px]">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-lg font-bold">Röyxat ({{ items.length }})</h2>
          <input v-model="query" type="search" class="field h-10 w-full sm:w-64" placeholder="Qidiriş">
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <button type="button" class="h-9 rounded-full px-4 text-sm font-semibold transition" :class="filter === 'all' ? 'bg-brand-800 text-white' : 'bg-[#F1F0F5] text-muted'" @click="filter = 'all'">Hammasi · {{ items.length }}</button>
          <button
            v-for="l in LANGS"
            :key="l.key"
            type="button"
            class="h-9 rounded-full px-4 text-sm font-semibold transition"
            :class="filter === l.key ? 'bg-brand-800 text-white' : 'bg-[#F1F0F5] text-muted'"
            @click="filter = l.key"
          >{{ l.label }} · {{ counts[l.key] }}</button>
        </div>
        <p v-if="loaded && !shown.length" class="mt-4 text-sm text-muted">Heç narsa topilmadi.</p>
        <ul class="mt-3 grid gap-1.5 sm:grid-cols-2">
          <li
            v-for="w in shown"
            :key="w.id"
            class="flex items-center gap-2 rounded-[12px] border px-3 py-2 transition"
            :class="[editing === w.id ? 'border-2 border-brand-700' : 'border-[#F0EEF6]', !w.active && 'opacity-55']"
          >
            <button type="button" class="min-w-0 flex-1 text-left" title="Tahrirlaş" @click="edit(w)">
              <span class="block truncate text-[15px] font-semibold" :class="!w.active && 'line-through'">{{ w.word }}</span>
              <span class="block text-xs text-muted">{{ langLabel(w.lang) }}{{ w.active ? '' : ' · öçirib qöyilgan' }}</span>
            </button>
            <button
              type="button"
              class="grid size-9 shrink-0 place-items-center rounded-full transition-colors"
              :class="w.active ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#F1F0F5] text-muted'"
              :aria-pressed="w.active"
              :title="w.active ? 'Faol — vaqtinça öçiriş uçun bosing' : 'Öçirib qöyilgan — yoqiş uçun bosing'"
              @click="toggle(w)"
            >
              <Icon :name="w.active ? 'eye' : 'eyeOff'" :size="17" />
            </button>
            <button type="button" class="grid size-9 shrink-0 place-items-center rounded-full text-[#C5192D] transition-colors hover:bg-[#FDECEE]" title="Öçiriş" @click="remove(w)">
              <Icon name="trash" :size="17" />
            </button>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
