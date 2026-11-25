<script setup lang="ts">
import { computed, ref } from 'vue'
import Collapsible from '@/components/Collapsible.vue'
import Icon from '@/components/Icon.vue'
import ImageField from '@/components/ImageField.vue'
import LangTabs from '@/components/LangTabs.vue'
import type { I18n, MediaDoc } from '@/lib/api'
import { LANGS, type Lang } from '@/lib/constants'
import { mediaUrl } from '@/lib/posts'

// Kartali bloklar (saytda matndagi [[kartalar-N]] joyida). Soddalaştirilgan tahrir:
// bitta til tanlanadi; bloklar va ro'yxatlar yig'ilgan holda, bosilsa oçiladi; böş qismlar «+ …» tugmasi bilan qöşiladi.
// Ma'lumot şakli özgarmagan: raqamlar va bandlar har tilda qatorlar («son | nomi», «Nom — izoh»).
export type ShowcaseColumn = { title: I18n; icon: string; style: 'numbers' | 'checks'; items: I18n }
export type ShowcaseCard = { title: I18n; url: string; photo?: MediaDoc | null }
export type ShowcaseBlock = { intro: I18n; stats: I18n; columns: ShowcaseColumn[]; outro: I18n; photos?: MediaDoc[]; slider?: boolean; cards?: ShowcaseCard[] }
export type Showcase = { blocks?: ShowcaseBlock[]; intro?: I18n; columns?: ShowcaseColumn[] }
const model = defineModel<Showcase>({ required: true })

const lang = ref<Lang>('uz')
const langLabel = computed(() => LANGS.find(l => l.code === lang.value)?.label ?? '')
const openBlock = ref<number | null>(null)
const openColumn = ref<string | null>(null) // `${blok}-${ustun}`
// «+ Kirish gapi» kabi tugma bosilgan, lekin hali böş qism ham körinib tursin
const shown = ref<Record<string, boolean>>({})

const ICONS: [string, string][] = [
  ['users-round', 'Odamlar'], ['rocket', 'Raketa'], ['target', 'Nişon'], ['trophy', 'Kubok'], ['star', 'Yulduz'],
  ['lightbulb', 'Çiroq'], ['book-open-text', 'Kitob'], ['graduation-cap', 'Qalpoq'], ['globe', 'Globus'], ['handshake', 'Qöl berişiş'],
  ['heart-handshake', 'Yordam'], ['shield-check', 'Himoya'], ['calendar-days', 'Taqvim'], ['party-popper', 'Bayram'], ['landmark', 'Bino'],
  ['palette', 'San’at'], ['music', 'Musiqa'], ['circle-check', 'Belgi'],
]

const emptyBlock = (): ShowcaseBlock => ({ intro: {}, stats: {}, columns: [], outro: {}, photos: [] })
// Eski şakl ({intro, columns}) — bitta blok
const blocks = (): ShowcaseBlock[] => model.value.blocks
  ?? (model.value.columns?.length ? [{ ...emptyBlock(), intro: model.value.intro ?? {}, columns: model.value.columns }] : [])
function save(list: ShowcaseBlock[]) { model.value = { blocks: list } }
function setBlock(i: number, patch: Partial<ShowcaseBlock>) { save(blocks().map((b, n) => (n === i ? { ...b, ...patch } : b))) }

const tr = (v: I18n | undefined) => (v?.[lang.value] ?? '').trim()
const setTr = (v: I18n | undefined, text: string): I18n => ({ ...(v ?? {}), [lang.value]: text })
const lines = (v: I18n | undefined) => tr(v).split('\n').map(x => x.trim()).filter(Boolean)
const has = (v: I18n | undefined) => Object.values(v ?? {}).some(x => (x ?? '').trim())
const isOn = (bi: number, part: string, filled: boolean) => filled || !!shown.value[`${bi}-${part}`]
const turnOn = (bi: number, part: string) => { shown.value = { ...shown.value, [`${bi}-${part}`]: true } }

// Yig'ilgan blok sarlavhasi: nimalar bor
function summary(b: ShowcaseBlock) {
  const title = b.columns.map(c => tr(c.title)).filter(Boolean).slice(0, 3).join(', ') || tr(b.intro).slice(0, 60) || (b.photos?.length ? 'Suratlar' : 'Böş blok')
  const parts = [
    b.photos?.length && `${b.photos.length} surat`,
    lines(b.stats).length && `${lines(b.stats).length} raqam`,
    b.columns.length && `${b.columns.length} röyxat`,
    b.cards?.length && `${b.cards.length} karta`,
  ].filter(Boolean)
  return { title, parts }
}

// ── Bloklar ────────────────────────────────────────────────
function addBlock() {
  save([...blocks(), emptyBlock()])
  openBlock.value = blocks().length - 1
}
function removeBlock(i: number) {
  if (!confirm(`${i + 1}-blok öçirilsinmi? Matndagi [[kartalar-${i + 1}]] qatorini ham olib taşlang.`)) return
  save(blocks().filter((_, n) => n !== i))
  openBlock.value = null
}
const copied = ref<number | null>(null)
async function copyMark(i: number) {
  try {
    await navigator.clipboard.writeText(`[[kartalar-${i + 1}]]`)
    copied.value = i
    setTimeout(() => (copied.value = null), 1500)
  }
  catch { /* nusxalab bo'lmasa — qo'lda yoziladi */ }
}

// ── Raqamlar: «son | nomi» qatorlari → ikki katakli qatorlar ──
function statRows(b: ShowcaseBlock) {
  return lines(b.stats).map((ln) => {
    const [value = '', ...rest] = ln.split('|')
    return { value: value.trim(), label: rest.join('|').trim() }
  })
}
function setStats(bi: number, rows: { value: string; label: string }[]) {
  setBlock(bi, { stats: setTr(blocks()[bi]!.stats, rows.map(r => `${r.value} | ${r.label}`).join('\n')) })
}
function editStat(bi: number, si: number, key: 'value' | 'label', text: string) {
  const rows = statRows(blocks()[bi]!)
  rows[si] = { ...rows[si]!, [key]: text.replace(/\|/g, '/') }
  setStats(bi, rows)
}
function addStat(bi: number) { setStats(bi, [...statRows(blocks()[bi]!), { value: '0', label: '' }]) }
function removeStat(bi: number, si: number) { setStats(bi, statRows(blocks()[bi]!).filter((_, n) => n !== si)) }

// ── Röyxatlar (ustunlar) ──────────────────────────────────
function setColumn(bi: number, ci: number, patch: Partial<ShowcaseColumn>) {
  setBlock(bi, { columns: blocks()[bi]!.columns.map((c, n) => (n === ci ? { ...c, ...patch } : c)) })
}
function addColumn(bi: number) {
  const cols = blocks()[bi]!.columns
  setBlock(bi, { columns: [...cols, { title: {}, icon: 'circle-check', style: 'numbers', items: {} }] })
  openColumn.value = `${bi}-${cols.length}`
}
function removeColumn(bi: number, ci: number) {
  if (!confirm('Röyxat öçirilsinmi?')) return
  setBlock(bi, { columns: blocks()[bi]!.columns.filter((_, n) => n !== ci) })
  openColumn.value = null
}
function moveColumn(bi: number, ci: number, d: -1 | 1) {
  const cols = [...blocks()[bi]!.columns]
  const j = ci + d
  if (j < 0 || j >= cols.length) return
  ;[cols[ci], cols[j]] = [cols[j]!, cols[ci]!]
  setBlock(bi, { columns: cols })
  openColumn.value = `${bi}-${j}`
}

function setCard(bi: number, ci: number, patch: Partial<ShowcaseCard>) {
  setBlock(bi, { cards: (blocks()[bi]!.cards ?? []).map((c, n) => (n === ci ? { ...c, ...patch } : c)) })
}

// ── Suratlar ──────────────────────────────────────────────
function addPhoto(bi: number, m: MediaDoc | null) {
  if (!m) return
  const list = blocks()[bi]!.photos ?? []
  if (!list.some(x => x.id === m.id)) setBlock(bi, { photos: [...list, m] })
}
function removePhoto(bi: number, pi: number) { setBlock(bi, { photos: (blocks()[bi]!.photos ?? []).filter((_, n) => n !== pi) }) }
function movePhoto(bi: number, pi: number, d: -1 | 1) {
  const list = [...(blocks()[bi]!.photos ?? [])]
  const j = pi + d
  if (j < 0 || j >= list.length) return
  ;[list[pi], list[j]] = [list[j]!, list[pi]!]
  setBlock(bi, { photos: list })
}
</script>

<template>
  <Collapsible id="page-showcase" variant="inner" title="Kartali bloklar" hint="Raqamlar, röyxatlar va suratlar chiroyli kartalarda" :default-open="!!(model.blocks?.length || model.columns?.length)" body-class="">

    <details class="rounded-xl bg-white px-3.5 py-2.5 text-[13px] leading-relaxed text-muted">
      <summary class="cursor-pointer font-semibold text-brand-700">Qanday işlaydi?</summary>
      <ol class="mt-2 list-decimal space-y-1 pl-5">
        <li>Quyida blok qöşing va uni töldiring (surat, raqamlar, röyxatlar…).</li>
        <li>Blok sarlavhasidagi <b>[[kartalar-1]]</b> tugmasini bosing — belgi nusxalanadi.</li>
        <li>Yuqoridagi «Matn» maydonida blok çiqişi kerak bölgan joyga belgini alohida qatorga qöying.</li>
      </ol>
    </details>

    <div class="mt-3 flex flex-wrap items-center gap-2.5">
      <span class="text-[13px] font-semibold text-muted">Tahrirlaş tili:</span>
      <LangTabs v-model="lang" compact />
    </div>

    <ul class="mt-3 flex flex-col gap-2.5">
      <li v-for="(block, bi) in blocks()" :key="bi" class="overflow-hidden rounded-xl border bg-white" :class="openBlock === bi ? 'border-brand-700' : 'border-[#ECEAF4]'">
        <!-- Yig'ilgan sarlavha -->
        <div class="flex items-center gap-2.5 px-3 py-2.5">
          <button type="button" class="flex min-w-0 flex-1 items-center gap-2.5 text-left" :aria-expanded="openBlock === bi" @click="openBlock = openBlock === bi ? null : bi">
            <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-brand-50 text-sm font-bold text-brand-700">{{ bi + 1 }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-semibold">{{ summary(block).title }}</span>
              <span class="block truncate text-xs text-muted">{{ summary(block).parts.join(' · ') || 'hali böş' }}</span>
            </span>
            <Icon name="chevronDown" :size="18" class="shrink-0 text-muted transition-transform" :class="openBlock === bi && 'rotate-180'" />
          </button>
          <button type="button" class="shrink-0 rounded-md bg-brand-50 px-2 py-1 font-mono text-xs text-brand-700 hover:bg-brand-100" title="Belgini nusxalaş — matnga qöyiş uçun" @click="copyMark(bi)">
            {{ copied === bi ? 'Nusxalandi ✓' : `[[kartalar-${bi + 1}]]` }}
          </button>
        </div>

        <!-- Oçilgan blok -->
        <div v-if="openBlock === bi" class="flex flex-col gap-4 border-t border-[#F0EEF6] px-3.5 py-3.5">
          <!-- Suratlar -->
          <section v-if="isOn(bi, 'photos', !!block.photos?.length)">
            <div class="mb-1.5 flex flex-wrap items-center justify-between gap-2">
              <h4 class="text-[13px] font-bold">Suratlar <span class="font-normal text-muted">— {{ block.slider ? 'slayderda bittadan, ostida 1 2 3 …' : 'birinçisi katta körinadi' }}</span></h4>
              <label class="flex cursor-pointer items-center gap-2 text-xs font-semibold"><input type="checkbox" :checked="!!block.slider" class="size-4 accent-[var(--color-brand-700)]" @change="setBlock(bi, { slider: ($event.target as HTMLInputElement).checked })">Slayder körinişida</label>
            </div>
            <ul class="flex flex-wrap gap-2">
              <li v-for="(ph, pi) in block.photos ?? []" :key="ph.id" class="group relative size-[88px] overflow-hidden rounded-xl border border-[#ECEAF4] bg-[#F1F0F5]">
                <img v-if="mediaUrl(ph)" :src="mediaUrl(ph)!" alt="" class="size-full object-cover">
                <span class="absolute inset-x-1 bottom-1 flex justify-between opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
                  <button type="button" class="grid size-6 place-items-center rounded bg-night/70 text-xs text-white disabled:opacity-40" :disabled="pi === 0" aria-label="Çapga" @click="movePhoto(bi, pi, -1)">←</button>
                  <button type="button" class="grid size-6 place-items-center rounded bg-[#C5192D] text-white" aria-label="Suratni olib taşlaş" @click="removePhoto(bi, pi)"><Icon name="x" :size="12" /></button>
                  <button type="button" class="grid size-6 place-items-center rounded bg-night/70 text-xs text-white disabled:opacity-40" :disabled="pi === (block.photos ?? []).length - 1" aria-label="Öngga" @click="movePhoto(bi, pi, 1)">→</button>
                </span>
              </li>
              <li v-if="(block.photos ?? []).length < 40" class="w-[88px]"><ImageField :model-value="null" compact folder="posts" label="Surat" @update:model-value="m => addPhoto(bi, m)" /></li>
            </ul>
          </section>

          <!-- Havolali kartalar -->
          <section v-if="isOn(bi, 'cards', !!block.cards?.length)">
            <h4 class="mb-1.5 text-[13px] font-bold">Havolali kartalar <span class="font-normal text-muted">· {{ langLabel }} — rasm, nom, bosilganda oçiladigan sahifa</span></h4>
            <ul class="flex flex-col gap-2">
              <li v-for="(c, ci) in block.cards ?? []" :key="ci" class="flex items-start gap-2.5 rounded-lg border border-[#ECEAF4] p-2.5">
                <div class="w-[72px] shrink-0"><ImageField :model-value="c.photo ?? null" compact folder="posts" label="Rasm" @update:model-value="m => setCard(bi, ci, { photo: m })" /></div>
                <div class="grid min-w-0 flex-1 gap-1.5">
                  <input :value="c.title?.[lang] ?? ''" class="field h-9!" :aria-label="`${ci + 1}-karta nomi`" placeholder="Nomi (masalan, Viza rasmiylaştiriş)" @input="setCard(bi, ci, { title: setTr(c.title, ($event.target as HTMLInputElement).value) })">
                  <input :value="c.url" class="field h-9!" :aria-label="`${ci + 1}-karta havolasi`" placeholder="/sahifa-manzili yoki https://…" @input="setCard(bi, ci, { url: ($event.target as HTMLInputElement).value.trim() })">
                </div>
                <button type="button" class="grid size-8 shrink-0 place-items-center rounded-full text-[#C5192D] hover:bg-red-50" :aria-label="`${ci + 1}-kartani öçiriş`" @click="setBlock(bi, { cards: (block.cards ?? []).filter((_, n) => n !== ci) })"><Icon name="x" :size="15" /></button>
              </li>
            </ul>
            <button type="button" class="mt-1.5 text-[13px] font-semibold text-brand-700 hover:underline" @click="setBlock(bi, { cards: [...(block.cards ?? []), { title: {}, url: '', photo: null }] })">+ Karta qöşiş</button>
          </section>

          <!-- Kirish gapi -->
          <section v-if="isOn(bi, 'intro', has(block.intro))">
            <label :for="`sc-intro-${bi}`" class="mb-1.5 block text-[13px] font-bold">Kirish gapi <span class="font-normal text-muted">· {{ langLabel }}</span></label>
            <textarea :id="`sc-intro-${bi}`" :value="tr(block.intro)" rows="2" class="field h-auto! py-2.5 leading-normal" placeholder="Blok tepasidagi qisqa gap (ixtiyoriy)" @input="setBlock(bi, { intro: setTr(block.intro, ($event.target as HTMLTextAreaElement).value) })" />
          </section>

          <!-- Raqamlar -->
          <section v-if="isOn(bi, 'stats', has(block.stats))">
            <h4 class="mb-1.5 text-[13px] font-bold">Raqamlar <span class="font-normal text-muted">· {{ langLabel }} — katta son va uning ostidagi yozuv</span></h4>
            <ul class="flex flex-col gap-1.5">
              <li v-for="(row, si) in statRows(block)" :key="si" class="flex items-center gap-2">
                <input :value="row.value" class="field h-10! w-[120px] shrink-0 font-bold" :aria-label="`${si + 1}-raqam`" placeholder="152" @input="editStat(bi, si, 'value', ($event.target as HTMLInputElement).value)">
                <input :value="row.label" class="field h-10! min-w-0 flex-1" :aria-label="`${si + 1}-raqam yozuvi`" placeholder="hamkor universitet" @input="editStat(bi, si, 'label', ($event.target as HTMLInputElement).value)">
                <button type="button" class="grid size-9 shrink-0 place-items-center rounded-full text-[#C5192D] hover:bg-red-50" aria-label="Raqamni öçiriş" @click="removeStat(bi, si)"><Icon name="x" :size="15" /></button>
              </li>
            </ul>
            <button type="button" class="mt-1.5 text-[13px] font-semibold text-brand-700 hover:underline" @click="addStat(bi)">+ Raqam qöşiş</button>
          </section>

          <!-- Röyxatlar -->
          <section v-if="block.columns.length">
            <h4 class="mb-1.5 text-[13px] font-bold">Röyxatlar <span class="font-normal text-muted">· {{ langLabel }}</span></h4>
            <ul class="flex flex-col gap-1.5">
              <li v-for="(col, ci) in block.columns" :key="ci" class="rounded-lg border border-[#ECEAF4]">
                <div class="flex items-center gap-2 px-2.5 py-2">
                  <button type="button" class="flex min-w-0 flex-1 items-center gap-2 text-left" :aria-expanded="openColumn === `${bi}-${ci}`" @click="openColumn = openColumn === `${bi}-${ci}` ? null : `${bi}-${ci}`">
                    <span class="min-w-0 flex-1 truncate text-sm font-semibold">{{ tr(col.title) || `${ci + 1}-röyxat (nomsiz)` }}</span>
                    <span class="shrink-0 text-xs text-muted">{{ lines(col.items).length }} band</span>
                    <Icon name="chevronDown" :size="16" class="shrink-0 text-muted transition-transform" :class="openColumn === `${bi}-${ci}` && 'rotate-180'" />
                  </button>
                </div>
                <div v-if="openColumn === `${bi}-${ci}`" class="flex flex-col gap-2.5 border-t border-[#F0EEF6] p-2.5">
                  <div class="grid gap-2.5 sm:grid-cols-[1fr_180px]">
                    <div>
                      <label :for="`sc-ct-${bi}-${ci}`" class="label">Röyxat nomi</label>
                      <input :id="`sc-ct-${bi}-${ci}`" :value="tr(col.title)" class="field h-10!" placeholder="Masalan: Klublar" @input="setColumn(bi, ci, { title: setTr(col.title, ($event.target as HTMLInputElement).value) })">
                    </div>
                    <div>
                      <label :for="`sc-ci-${bi}-${ci}`" class="label">Belgi</label>
                      <select :id="`sc-ci-${bi}-${ci}`" :value="col.icon" class="field h-10!" @change="setColumn(bi, ci, { icon: ($event.target as HTMLSelectElement).value })">
                        <option v-for="[v, l] in ICONS" :key="v" :value="v">{{ l }}</option>
                        <option v-if="col.icon && !ICONS.some(([v]) => v === col.icon)" :value="col.icon">{{ col.icon }}</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <span class="label">Bandlar körinişi</span>
                    <div class="inline-flex rounded-lg border border-field p-0.5">
                      <button type="button" class="h-8 rounded-md px-3 text-xs font-bold" :class="col.style !== 'checks' ? 'bg-brand-700 text-white' : 'text-muted'" @click="setColumn(bi, ci, { style: 'numbers' })">01 02 03</button>
                      <button type="button" class="h-8 rounded-md px-3 text-xs font-bold" :class="col.style === 'checks' ? 'bg-brand-700 text-white' : 'text-muted'" @click="setColumn(bi, ci, { style: 'checks' })">✓ ✓ ✓</button>
                    </div>
                  </div>
                  <div>
                    <label :for="`sc-items-${bi}-${ci}`" class="label">Bandlar — har qatorda bittasi</label>
                    <textarea :id="`sc-items-${bi}-${ci}`" :value="tr(col.items)" rows="5" class="field h-auto! py-2.5 leading-normal" placeholder="Zakovat — intellektual klub&#10;Yoş kitobxon" @input="setColumn(bi, ci, { items: setTr(col.items, ($event.target as HTMLTextAreaElement).value) })" />
                    <p class="mt-1 text-xs text-muted">Izoh kerak bölsa: <b>Nom — izoh</b> (izoh kartada mayda yozuvda çiqadi).</p>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <button type="button" class="btn-ghost h-8! px-3! text-xs!" :disabled="ci === 0" @click="moveColumn(bi, ci, -1)">↑ Yuqoriga</button>
                    <button type="button" class="btn-ghost h-8! px-3! text-xs!" :disabled="ci === block.columns.length - 1" @click="moveColumn(bi, ci, 1)">↓ Pastga</button>
                    <button type="button" class="ml-auto h-8 rounded-full px-3 text-xs font-semibold text-[#C5192D] hover:bg-red-50" @click="removeColumn(bi, ci)">Röyxatni öçiriş</button>
                  </div>
                </div>
              </li>
            </ul>
          </section>

          <!-- Xulosa -->
          <section v-if="isOn(bi, 'outro', has(block.outro))">
            <label :for="`sc-outro-${bi}`" class="mb-1.5 block text-[13px] font-bold">Xulosa gapi <span class="font-normal text-muted">· {{ langLabel }} — blok pastida</span></label>
            <textarea :id="`sc-outro-${bi}`" :value="tr(block.outro)" rows="2" class="field h-auto! py-2.5 leading-normal" @input="setBlock(bi, { outro: setTr(block.outro, ($event.target as HTMLTextAreaElement).value) })" />
          </section>

          <!-- Qöşiş tugmalari: faqat hali yöq qismlar -->
          <div class="flex flex-wrap gap-1.5">
            <button v-if="!isOn(bi, 'photos', !!block.photos?.length)" type="button" class="chip-add" @click="turnOn(bi, 'photos')">+ Suratlar</button>
            <button v-if="!isOn(bi, 'cards', !!block.cards?.length)" type="button" class="chip-add" @click="turnOn(bi, 'cards')">+ Havolali kartalar</button>
            <button v-if="!isOn(bi, 'intro', has(block.intro))" type="button" class="chip-add" @click="turnOn(bi, 'intro')">+ Kirish gapi</button>
            <button v-if="!isOn(bi, 'stats', has(block.stats))" type="button" class="chip-add" @click="turnOn(bi, 'stats'); addStat(bi)">+ Raqamlar</button>
            <button v-if="block.columns.length < 20" type="button" class="chip-add" @click="addColumn(bi)">+ Röyxat</button>
            <button v-if="!isOn(bi, 'outro', has(block.outro))" type="button" class="chip-add" @click="turnOn(bi, 'outro')">+ Xulosa gapi</button>
            <button type="button" class="ml-auto h-8 rounded-full px-3 text-xs font-semibold text-[#C5192D] hover:bg-red-50" @click="removeBlock(bi)">Blokni öçiriş</button>
          </div>
        </div>
      </li>
    </ul>

    <button v-if="blocks().length < 10" type="button" class="btn-ghost mt-3 h-10! gap-2" @click="addBlock"><Icon name="plus" :size="16" /> Yangi blok</button>
  </Collapsible>
</template>

<style scoped>
.chip-add {
  height: 2rem;
  border-radius: 9999px;
  border: 1px dashed #cfcae3;
  padding: 0 0.85rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-brand-700);
  background: #fff;
}
.chip-add:hover { border-style: solid; border-color: var(--color-brand-700); }
</style>
