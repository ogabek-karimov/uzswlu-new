<script setup lang="ts">
import I18nFields from '@/components/I18nFields.vue'
import Icon from '@/components/Icon.vue'
import type { I18n } from '@/lib/api'

// Kartali bloklar (saytda matndagi [[kartalar-N]] joyida). Blok: kirish gapi, raqamlar («7 | nomi»),
// ustunlar (bandlar har qatorda; «Nom — izoh»; uslub: raqamli yoki ✓ belgili), xulosa gapi.
export type ShowcaseColumn = { title: I18n; icon: string; style: 'numbers' | 'checks'; items: I18n }
export type ShowcaseBlock = { intro: I18n; stats: I18n; columns: ShowcaseColumn[]; outro: I18n }
export type Showcase = { blocks?: ShowcaseBlock[]; intro?: I18n; columns?: ShowcaseColumn[] }
const model = defineModel<Showcase>({ required: true })

const ICONS = ['target', 'users-round', 'rocket', 'party-popper', 'trophy', 'star', 'heart-handshake', 'lightbulb', 'book-open-text', 'globe', 'palette', 'music', 'circle-check']
const emptyBlock = (): ShowcaseBlock => ({ intro: {}, stats: {}, columns: [], outro: {} })
// Eski shakl ({intro, columns}) — bitta blok
const blocks = (): ShowcaseBlock[] => model.value.blocks
  ?? (model.value.columns?.length ? [{ ...emptyBlock(), intro: model.value.intro ?? {}, columns: model.value.columns }] : [])

function save(list: ShowcaseBlock[]) { model.value = { blocks: list } }
function setBlock(i: number, patch: Partial<ShowcaseBlock>) { save(blocks().map((b, n) => (n === i ? { ...b, ...patch } : b))) }
function removeBlock(i: number) {
  if (!confirm(`${i + 1}-blok öçirilsinmi? Matndagi [[kartalar-${i + 1}]] belgisini ham olib taşlang.`)) return
  save(blocks().filter((_, n) => n !== i))
}
function setColumn(bi: number, ci: number, patch: Partial<ShowcaseColumn>) {
  setBlock(bi, { columns: blocks()[bi]!.columns.map((c, n) => (n === ci ? { ...c, ...patch } : c)) })
}
function addColumn(bi: number) {
  const cols = blocks()[bi]!.columns
  setBlock(bi, { columns: [...cols, { title: {}, icon: cols.length ? 'rocket' : 'users-round', style: 'numbers', items: {} }] })
}
function removeColumn(bi: number, ci: number) {
  if (!confirm('Ustun öçirilsinmi?')) return
  setBlock(bi, { columns: blocks()[bi]!.columns.filter((_, n) => n !== ci) })
}
async function copyMark(i: number) {
  try { await navigator.clipboard.writeText(`[[kartalar-${i + 1}]]`) } catch { /* nusxalab bo'lmasa — qo'lda yoziladi */ }
}
</script>

<template>
  <fieldset class="rounded-2xl border border-line bg-[#FAF9FD] px-4 py-3.5">
    <legend class="px-1 text-sm font-bold">Kartali bloklar <span class="font-normal text-muted">(raqamlar, ro‘yxatlar — chiroyli kartalarda)</span></legend>
    <p class="text-xs text-muted">Har blok saytda matndagi <code class="rounded bg-white px-1 font-bold text-brand-700">[[kartalar-N]]</code> qatori örnida çiqadi (N — blok raqami) — belgini matnda alohida qatorga yozing. Bandlar va raqamlar: har qatorda bittasi; izoh uçun <b>«Nom — izoh»</b>, raqam uçun <b>«7 | nomi»</b>.</p>

    <div v-for="(block, bi) in blocks()" :key="bi" class="mt-3.5 rounded-xl border border-[#ECEAF4] bg-white p-3.5">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <span class="flex items-center gap-2 text-sm font-bold">
          {{ bi + 1 }}-blok
          <button type="button" class="rounded-md bg-brand-50 px-2 py-0.5 font-mono text-xs text-brand-700 hover:bg-brand-100" title="Nusxalaş" @click="copyMark(bi)">[[kartalar-{{ bi + 1 }}]]</button>
        </span>
        <button type="button" class="inline-flex h-8 items-center gap-1 rounded-full px-3 text-xs font-semibold text-[#C5192D] hover:bg-red-50" @click="removeBlock(bi)"><Icon name="x" :size="14" /> Blokni öçiriş</button>
      </div>
      <div class="grid gap-3.5">
        <I18nFields :model-value="block.intro" label="Kirish gapi (yuqorida)" textarea :rows="2" @update:model-value="v => setBlock(bi, { intro: v })" />
        <I18nFields :model-value="block.stats" label="Raqamlar (har qatorda «son | nomi»)" textarea :rows="3" :placeholders="{ uz: '7 | Yönaliş koordinatorlari' }" @update:model-value="v => setBlock(bi, { stats: v })" />

        <div v-for="(col, ci) in block.columns" :key="ci" class="rounded-xl border border-dashed border-[#DAD6EA] p-3">
          <div class="mb-2.5 flex items-center justify-between gap-2">
            <span class="text-sm font-semibold">{{ ci + 1 }}-ustun</span>
            <button type="button" class="grid size-8 place-items-center rounded-full text-[#C5192D] hover:bg-red-50" :aria-label="`${ci + 1}-ustunni öçiriş`" @click="removeColumn(bi, ci)"><Icon name="x" :size="16" /></button>
          </div>
          <div class="grid gap-3 sm:grid-cols-[1fr_170px_170px]">
            <I18nFields :model-value="col.title" label="Ustun nomi" layout="rows" @update:model-value="v => setColumn(bi, ci, { title: v })" />
            <div>
              <label :for="`sc-icon-${bi}-${ci}`" class="label">Belgi</label>
              <input :id="`sc-icon-${bi}-${ci}`" :value="col.icon" class="field" list="sc-icons" placeholder="users-round" @input="setColumn(bi, ci, { icon: ($event.target as HTMLInputElement).value.trim() })">
            </div>
            <div>
              <label :for="`sc-style-${bi}-${ci}`" class="label">Bandlar körinişi</label>
              <select :id="`sc-style-${bi}-${ci}`" :value="col.style" class="field" @change="setColumn(bi, ci, { style: ($event.target as HTMLSelectElement).value as 'numbers' | 'checks' })">
                <option value="numbers">01, 02… raqamli</option>
                <option value="checks">✓ belgili</option>
              </select>
            </div>
          </div>
          <div class="mt-3">
            <I18nFields :model-value="col.items" label="Bandlar (har qatorda bittasi)" textarea :rows="5" @update:model-value="v => setColumn(bi, ci, { items: v })" />
          </div>
        </div>
        <button v-if="block.columns.length < 4" type="button" class="btn-ghost h-9! w-fit gap-2 text-sm" @click="addColumn(bi)"><Icon name="plus" :size="15" /> Ustun qöşiş</button>

        <I18nFields :model-value="block.outro" label="Xulosa gapi (pastda, ixtiyoriy)" textarea :rows="2" @update:model-value="v => setBlock(bi, { outro: v })" />
      </div>
    </div>
    <datalist id="sc-icons"><option v-for="ic in ICONS" :key="ic" :value="ic" /></datalist>
    <button v-if="blocks().length < 10" type="button" class="btn-ghost mt-3.5 h-10! gap-2" @click="save([...blocks(), emptyBlock()])"><Icon name="plus" :size="16" /> Blok qöşiş</button>
  </fieldset>
</template>
