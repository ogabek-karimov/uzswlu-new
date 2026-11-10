<script setup lang="ts">
import Image from '@tiptap/extension-image'
import Subscript from '@tiptap/extension-subscript'
import Superscript from '@tiptap/extension-superscript'
import { TableKit } from '@tiptap/extension-table'
import TextAlign from '@tiptap/extension-text-align'
import { TextStyleKit } from '@tiptap/extension-text-style'
import Youtube from '@tiptap/extension-youtube'
import { Placeholder } from '@tiptap/extensions'
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import type { MediaDoc } from '@/lib/api'
import Icon from './Icon.vue'
import MediaPicker from './MediaPicker.vue'

// Matn muharriri (eski CKEditor imkoniyatlari): format, rang, shrift, jadval, rasm, havola,
// "Serverdan tanlash" (media kutubxona), topish/almashtirish, HTML manba, to'liq ekran.
// Natija — HTML; server tomonda yana tozalanadi (XSS'dan himoya).
// modelValue: API bo'sh tilni null qilib bersa ham (Vue prop ogohlantirishisiz) bo'sh matn deb qabul qilinadi
const props = defineProps<{ modelValue?: string | null; placeholder?: string }>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()

const editor = useEditor({
  content: props.modelValue || '',
  extensions: [
    StarterKit.configure({ heading: { levels: [2, 3, 4] }, link: { openOnClick: false, HTMLAttributes: { rel: 'noopener noreferrer' } } }),
    Subscript,
    Superscript,
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
    TextStyleKit,
    Image,
    TableKit.configure({ table: { resizable: false } }),
    Youtube.configure({ nocookie: true, width: 640, height: 360 }),
    Placeholder.configure({ placeholder: () => props.placeholder ?? '' }),
  ],
  editorProps: {
    attributes: { class: 'prose-editor' },
    // Word'dan nusxa olinganda ortiqcha uslublar tozalanadi
    transformPastedHTML: html => html.replace(/ class="[^"]*"/g, '').replace(/<\/?(font|o:p)[^>]*>/g, '').replace(/ style="[^"]*mso-[^"]*"/g, ''),
  },
  onUpdate: ({ editor: e }) => emit('update:modelValue', e.isEmpty ? '' : e.getHTML()),
})

// Til almashtirilganda matnni yangilash (o'zgarish hodisasi chiqarmasdan)
watch(() => props.modelValue, (value) => {
  const e = editor.value
  if (!e || source.value) return
  const current = e.isEmpty ? '' : e.getHTML()
  if (current !== (value || '')) e.commands.setContent(value || '', { emitUpdate: false })
})
onBeforeUnmount(() => editor.value?.destroy())

const chain = () => editor.value!.chain().focus()
const active = (name: string, attrs?: Record<string, unknown>) => !!editor.value?.isActive(name, attrs)

// ── HTML manba, to'liq ekran, bloklar ──
const source = ref(false)
const sourceText = ref('')
const fullscreen = ref(false)
const showBlocks = ref(false)
function toggleSource() {
  const e = editor.value
  if (!e) return
  if (!source.value) { sourceText.value = e.isEmpty ? '' : e.getHTML(); source.value = true; return }
  e.commands.setContent(sourceText.value, { emitUpdate: true })
  source.value = false
}

// ── Format, shrift, o'lcham, rang ──
const FORMATS = [['p', 'Oddiy matn'], ['2', 'Sarlavha 2'], ['3', 'Sarlavha 3'], ['4', 'Sarlavha 4']] as const
const FONTS = [['', 'Onest (sayt)'], ['Playfair Display', 'Playfair Display'], ['Arial', 'Arial'], ['Times New Roman', 'Times New Roman'], ['Georgia', 'Georgia'], ['Courier New', 'Courier New']] as const
const SIZES = ['', '12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px']
const COLORS = ['#13112F', '#2A2066', '#382B85', '#0E7A5A', '#C0362C', '#B45309', '#0A6BB5', '#5E5A72']
const BG_COLORS = ['#FCE68A', '#DDFBF0', '#E9F6FD', '#FDECEA', '#ECEBFB', '#F1F0F5']
const format = computed(() => (active('heading', { level: 2 }) ? '2' : active('heading', { level: 3 }) ? '3' : active('heading', { level: 4 }) ? '4' : 'p'))
function setFormat(v: string) {
  if (v === 'p') chain().setParagraph().run()
  else chain().setHeading({ level: Number(v) as 2 | 3 | 4 }).run()
}
const font = computed(() => (editor.value?.getAttributes('textStyle').fontFamily as string) ?? '')
const size = computed(() => (editor.value?.getAttributes('textStyle').fontSize as string) ?? '')
function setFont(v: string) { v ? chain().setFontFamily(v).run() : chain().unsetFontFamily().run() }
function setSize(v: string) { v ? chain().setFontSize(v).run() : chain().unsetFontSize().run() }
const palette = ref<'' | 'color' | 'bg' | 'chars' | 'table'>('')
function setColor(c: string | null) { c ? chain().setColor(c).run() : chain().unsetColor().run(); palette.value = '' }
function setBg(c: string | null) { c ? chain().setBackgroundColor(c).run() : chain().unsetBackgroundColor().run(); palette.value = '' }

// ── Maxsus belgilar ──
const CHARS = ['–', '—', '«', '»', '“', '”', '‘', '’', 'ʻ', 'ʼ', '№', '§', '©', '®', '™', '°', '±', '×', '÷', '…', '€', '$', '£', '¥', '½', '¼', '→', '←', '•', '✓']
function insertChar(c: string) { chain().insertContent(c).run(); palette.value = '' }

// ── Oddiy matn sifatida qo'yish ──
async function pastePlain() {
  try {
    const text = await navigator.clipboard.readText()
    const paragraphs = text.split(/\r?\n\s*\r?\n/).map(p => ({ type: 'paragraph', content: p.trim() ? [{ type: 'text', text: p.replace(/\r?\n/g, ' ').trim() }] : [] }))
    chain().insertContent(paragraphs).run()
  }
  catch {
    window.alert('Brauzer nusxa olingan matnni öqişga ruxsat bermadi. Ctrl+Shift+V bilan qöying.')
  }
}

// ── Havola (va "Serverdan tanlash") ──
const link = reactive({ open: false, url: '', text: '', newTab: true, editing: false, hasSelection: false })
function openLink() {
  const e = editor.value
  if (!e) return
  const { from, to } = e.state.selection
  link.hasSelection = from !== to
  link.text = e.state.doc.textBetween(from, to, ' ')
  const attrs = e.getAttributes('link')
  link.url = (attrs.href as string) ?? ''
  link.newTab = attrs.target ? attrs.target === '_blank' : true
  link.editing = !!attrs.href
  link.open = true
}
function applyLink() {
  const url = link.url.trim()
  if (!url) return
  const attrs = { href: url, target: link.newTab ? '_blank' : null }
  if (link.hasSelection || link.editing) chain().extendMarkRange('link').setLink(attrs).run()
  else chain().insertContent({ type: 'text', text: link.text.trim() || url, marks: [{ type: 'link', attrs }] }).run()
  link.open = false
}
function removeLink() { chain().extendMarkRange('link').unsetLink().run(); link.open = false }

// ── Media tanlash: havola yoki rasm uchun ──
const picker = reactive<{ open: boolean; kind: 'pdf' | 'image' | 'all'; for: 'link' | 'image' }>({ open: false, kind: 'all', for: 'link' })
function onPick(m: MediaDoc) {
  picker.open = false
  if (picker.for === 'link') {
    link.url = m.url ?? ''
    if (!link.hasSelection && !link.text) link.text = m.filename ?? ''
  }
  else {
    chain().setImage({ src: m.sizes?.hero?.url ?? m.url ?? '', alt: m.alt?.uz ?? '' }).run()
  }
}

// ── Video (YouTube) ──
const video = reactive({ open: false, url: '' })
function applyVideo() {
  if (video.url.trim()) chain().setYoutubeVideo({ src: video.url.trim() }).run()
  video.open = false
  video.url = ''
}

// ── Topish va almashtirish ──
const find = reactive({ open: false, q: '', replace: '', info: '' })
function matches() {
  const e = editor.value
  const term = find.q.toLocaleLowerCase()
  const out: { from: number; to: number }[] = []
  if (!e || !term) return out
  e.state.doc.descendants((node, pos) => {
    if (!node.isText) return
    const text = node.text!.toLocaleLowerCase()
    let i = text.indexOf(term)
    while (i !== -1) { out.push({ from: pos + i, to: pos + i + term.length }); i = text.indexOf(term, i + term.length) }
  })
  return out
}
function findNext() {
  const all = matches()
  if (!all.length) { find.info = 'Topilmadi'; return }
  const after = editor.value?.state.selection.to ?? 0
  const m = all.find(x => x.from >= after) ?? all[0]!
  chain().setTextSelection(m).scrollIntoView().run()
  find.info = `${all.indexOf(m) + 1} / ${all.length}`
}
function replaceOne() {
  const e = editor.value
  if (!e) return
  const { from, to } = e.state.selection
  if (e.state.doc.textBetween(from, to).toLocaleLowerCase() === find.q.toLocaleLowerCase() && find.q) chain().insertContentAt({ from, to }, find.replace).run()
  findNext()
}
function replaceAll() {
  const e = editor.value
  if (!e) return
  const all = matches().reverse()
  if (!all.length) { find.info = 'Topilmadi'; return }
  let tr = e.state.tr
  for (const m of all) tr = tr.insertText(find.replace, m.from, m.to)
  e.view.dispatch(tr)
  find.info = `${all.length} ta almaştirildi`
}

const words = computed(() => {
  const text = editor.value?.getText() ?? ''
  return text.trim() ? text.trim().split(/\s+/).length : 0
})
const inTable = computed(() => active('table'))
</script>

<template>
  <div :class="fullscreen ? 'fixed inset-0 z-[60] flex flex-col bg-white p-4' : ''">
    <div class="flex flex-col overflow-hidden rounded-[14px] border border-field" :class="fullscreen && 'min-h-0 flex-1'">
      <div v-if="editor" role="toolbar" aria-label="Matn formatlaş" class="relative flex flex-col gap-0.5 border-b border-line bg-[#FAF9FD] px-2 py-1.5">
        <!-- 1-qator: manba, tarix, topish, havola, qo'shish, ko'rinish -->
        <div class="flex flex-wrap items-center gap-0.5">
          <button type="button" class="tool" :class="source && 'on'" title="HTML manba (Source)" aria-label="HTML manba" @click="toggleSource">&lt;/&gt;</button>
          <span class="sep" />
          <button type="button" class="tool" title="Orqaga (Ctrl+Z)" aria-label="Orqaga" :disabled="source" @click="chain().undo().run()">↶</button>
          <button type="button" class="tool" title="Oldinga (Ctrl+Y)" aria-label="Oldinga" :disabled="source" @click="chain().redo().run()">↷</button>
          <span class="sep" />
          <button type="button" class="tool" :class="find.open && 'on'" title="Topiş va almaştiriş" aria-label="Topiş va almaştiriş" :disabled="source" @click="find.open = !find.open"><Icon name="search" :size="16" /></button>
          <button type="button" class="tool" title="Oddiy matn sifatida qöyiş" aria-label="Oddiy matn sifatida qöyiş" :disabled="source" @click="pastePlain">T</button>
          <button type="button" class="tool" title="Formatni tozalaş" aria-label="Formatni tozalaş" :disabled="source" @click="chain().unsetAllMarks().clearNodes().run()">T<sub>x</sub></button>
          <span class="sep" />
          <button type="button" class="tool" :class="active('link') && 'on'" title="Havola (serverdagi fayl yoki manzil)" aria-label="Havola" :disabled="source" @click="openLink"><Icon name="link" :size="16" /></button>
          <button type="button" class="tool" title="Havolani olib taşlaş" aria-label="Havolani olib taşlaş" :disabled="source || !active('link')" @click="removeLink"><span class="line-through">⛓</span></button>
          <span class="sep" />
          <button type="button" class="tool" title="Rasm (serverdan yoki yangi)" aria-label="Rasm" :disabled="source" @click="Object.assign(picker, { open: true, kind: 'image', for: 'image' })"><Icon name="image" :size="16" /></button>
          <button type="button" class="tool" :class="(palette === 'table' || inTable) && 'on'" title="Jadval" aria-label="Jadval" :disabled="source" @click="palette = palette === 'table' ? '' : 'table'">▦</button>
          <button type="button" class="tool" title="Gorizontal çiziq" aria-label="Gorizontal çiziq" :disabled="source" @click="chain().setHorizontalRule().run()">―</button>
          <button type="button" class="tool" :class="palette === 'chars' && 'on'" title="Maxsus belgilar" aria-label="Maxsus belgilar" :disabled="source" @click="palette = palette === 'chars' ? '' : 'chars'">Ω</button>
          <button type="button" class="tool" title="Video (YouTube)" aria-label="Video (YouTube)" :disabled="source" @click="video.open = true">▶</button>
          <span class="sep" />
          <button type="button" class="tool" :class="fullscreen && 'on'" :title="fullscreen ? 'Kiçraytiriş' : 'Töliq ekran'" aria-label="Töliq ekran" @click="fullscreen = !fullscreen">⤢</button>
          <button type="button" class="tool" :class="showBlocks && 'on'" title="Bloklarni körsatiş" aria-label="Bloklarni körsatiş" @click="showBlocks = !showBlocks">¶</button>
        </div>
        <!-- 2-qator: belgilar, ro'yxatlar, tekislash -->
        <div class="flex flex-wrap items-center gap-0.5">
          <button type="button" class="tool" :class="active('bold') && 'on'" title="Qalin (Ctrl+B)" aria-label="Qalin" :disabled="source" @click="chain().toggleBold().run()"><b>B</b></button>
          <button type="button" class="tool italic" :class="active('italic') && 'on'" title="Kursiv (Ctrl+I)" aria-label="Kursiv" :disabled="source" @click="chain().toggleItalic().run()">I</button>
          <button type="button" class="tool underline" :class="active('underline') && 'on'" title="Tagiga çiziş (Ctrl+U)" aria-label="Tagiga çiziş" :disabled="source" @click="chain().toggleUnderline().run()">U</button>
          <button type="button" class="tool line-through" :class="active('strike') && 'on'" title="Ustidan çiziş" aria-label="Ustidan çiziş" :disabled="source" @click="chain().toggleStrike().run()">S</button>
          <button type="button" class="tool" :class="active('subscript') && 'on'" title="Pastki indeks" aria-label="Pastki indeks" :disabled="source" @click="chain().toggleSubscript().run()">x<sub>2</sub></button>
          <button type="button" class="tool" :class="active('superscript') && 'on'" title="Yuqori indeks" aria-label="Yuqori indeks" :disabled="source" @click="chain().toggleSuperscript().run()">x<sup>2</sup></button>
          <span class="sep" />
          <button type="button" class="tool" :class="active('orderedList') && 'on'" title="Raqamli röyxat" aria-label="Raqamli röyxat" :disabled="source" @click="chain().toggleOrderedList().run()">1.</button>
          <button type="button" class="tool" :class="active('bulletList') && 'on'" title="Röyxat" aria-label="Röyxat" :disabled="source" @click="chain().toggleBulletList().run()">•</button>
          <button type="button" class="tool" title="Tashqariga" aria-label="Tashqariga" :disabled="source" @click="chain().liftListItem('listItem').run()">⇤</button>
          <button type="button" class="tool" title="Içkariga" aria-label="Içkariga" :disabled="source" @click="chain().sinkListItem('listItem').run()">⇥</button>
          <button type="button" class="tool" :class="active('blockquote') && 'on'" title="Iqtibos" aria-label="Iqtibos" :disabled="source" @click="chain().toggleBlockquote().run()">❝</button>
          <span class="sep" />
          <button v-for="a in ([['left', 'Çapga', '⯇'], ['center', 'Markazga', '≡'], ['right', 'Öngga', '⯈'], ['justify', 'Ikki tomonga', '☰']] as const)" :key="a[0]" type="button" class="tool" :class="editor.isActive({ textAlign: a[0] }) && 'on'" :title="a[1]" :aria-label="a[1]" :disabled="source" @click="chain().setTextAlign(a[0]).run()">{{ a[2] }}</button>
        </div>
        <!-- 3-qator: format, shrift, o'lcham, ranglar -->
        <div class="flex flex-wrap items-center gap-1 py-0.5">
          <select :value="format" aria-label="Format" class="sel" :disabled="source" @change="setFormat(($event.target as HTMLSelectElement).value)">
            <option v-for="f in FORMATS" :key="f[0]" :value="f[0]">{{ f[1] }}</option>
          </select>
          <select :value="font" aria-label="Şrift" class="sel" :disabled="source" @change="setFont(($event.target as HTMLSelectElement).value)">
            <option v-for="f in FONTS" :key="f[0]" :value="f[0]">{{ f[1] }}</option>
          </select>
          <select :value="size" aria-label="Ölçam" class="sel w-[84px]" :disabled="source" @change="setSize(($event.target as HTMLSelectElement).value)">
            <option v-for="s in SIZES" :key="s" :value="s">{{ s ? s.replace('px', '') : 'Ölçam' }}</option>
          </select>
          <span class="sep" />
          <button type="button" class="tool" :class="palette === 'color' && 'on'" title="Matn rangi" aria-label="Matn rangi" :disabled="source" @click="palette = palette === 'color' ? '' : 'color'"><span class="border-b-[3px] border-[#C0362C] leading-none">A</span></button>
          <button type="button" class="tool" :class="palette === 'bg' && 'on'" title="Fon rangi" aria-label="Fon rangi" :disabled="source" @click="palette = palette === 'bg' ? '' : 'bg'"><span class="bg-[#FCE68A] px-[3px] leading-tight">A</span></button>
        </div>

        <!-- Ochiladigan panellar -->
        <div v-if="palette === 'color' || palette === 'bg'" class="absolute top-full left-2 z-10 mt-1 flex flex-wrap items-center gap-1.5 rounded-xl border border-line bg-white p-2.5 shadow-xl">
          <button v-for="c in (palette === 'color' ? COLORS : BG_COLORS)" :key="c" type="button" class="size-7 rounded-md border border-black/10" :style="{ background: c }" :aria-label="c" @click="palette === 'color' ? setColor(c) : setBg(c)" />
          <label class="flex items-center gap-1 text-xs text-muted">Boşqa: <input type="color" class="size-7 cursor-pointer" @change="palette === 'color' ? setColor(($event.target as HTMLInputElement).value) : setBg(($event.target as HTMLInputElement).value)"></label>
          <button type="button" class="h-7 rounded-md border border-field px-2 text-xs" @click="palette === 'color' ? setColor(null) : setBg(null)">Olib taşlaş</button>
        </div>
        <div v-if="palette === 'chars'" class="absolute top-full left-2 z-10 mt-1 grid grid-cols-10 gap-1 rounded-xl border border-line bg-white p-2.5 shadow-xl">
          <button v-for="c in CHARS" :key="c" type="button" class="grid size-8 place-items-center rounded-md text-base hover:bg-canvas" @click="insertChar(c)">{{ c }}</button>
        </div>
        <div v-if="palette === 'table'" class="absolute top-full left-2 z-10 mt-1 flex flex-wrap gap-1.5 rounded-xl border border-line bg-white p-2.5 text-xs font-semibold shadow-xl" @click="palette = ''">
          <button type="button" class="tbl" @click="chain().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()">+ Jadval 3×3</button>
          <template v-if="inTable">
            <button type="button" class="tbl" @click="chain().addRowAfter().run()">+ Qator</button>
            <button type="button" class="tbl" @click="chain().addColumnAfter().run()">+ Ustun</button>
            <button type="button" class="tbl" @click="chain().deleteRow().run()">− Qator</button>
            <button type="button" class="tbl" @click="chain().deleteColumn().run()">− Ustun</button>
            <button type="button" class="tbl" @click="chain().toggleHeaderRow().run()">Sarlavha qatori</button>
            <button type="button" class="tbl text-red-700" @click="chain().deleteTable().run()">Jadvalni öçiriş</button>
          </template>
        </div>
      </div>

      <!-- Topish va almashtirish -->
      <div v-if="find.open && !source" class="flex flex-wrap items-center gap-2 border-b border-line bg-white px-3 py-2 text-[13px]">
        <input v-model="find.q" aria-label="Topiladigan matn" placeholder="Topiş…" class="field h-9! w-48!" @keydown.enter.prevent="findNext">
        <input v-model="find.replace" aria-label="Almaştiriladigan matn" placeholder="Nima bilan almaştiriş" class="field h-9! w-48!">
        <button type="button" class="btn-ghost h-9! px-3! text-xs!" @click="findNext">Keyingisi</button>
        <button type="button" class="btn-ghost h-9! px-3! text-xs!" @click="replaceOne">Almaştiriş</button>
        <button type="button" class="btn-ghost h-9! px-3! text-xs!" @click="replaceAll">Hammasini</button>
        <span class="text-subtle">{{ find.info }}</span>
      </div>

      <textarea v-if="source" v-model="sourceText" aria-label="HTML manba" class="min-h-[300px] w-full flex-1 resize-y bg-[#13112F] p-4 font-mono text-[13px] leading-relaxed text-[#E6E3F5] outline-none" spellcheck="false" />
      <EditorContent v-else :editor="editor" class="min-h-0 flex-1 overflow-y-auto" :class="showBlocks && 'show-blocks'" />

      <div class="flex flex-wrap justify-between gap-2 border-t border-line bg-[#FAF9FD] px-3.5 py-2 text-xs text-subtle">
        <span>Word’dan nusxa olinsa, ortiqça format öz-özidan tozalanadi</span>
        <span>{{ words }} söz</span>
      </div>
    </div>

    <!-- Havola oynasi -->
    <Teleport to="body">
      <div v-if="link.open" class="fixed inset-0 z-[65] grid place-items-center bg-night/45 p-4" @click.self="link.open = false">
        <section role="dialog" aria-modal="true" aria-label="Havola" class="w-full max-w-[560px] rounded-[20px] bg-white p-5 shadow-2xl">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-base font-bold">{{ link.editing ? 'Havolani tahrirlaş' : 'Havola qöşiş' }}</h2>
            <span v-if="link.hasSelection" class="max-w-[60%] truncate text-xs text-subtle">Belgilangan matn: <b class="text-ink">{{ link.text }}</b></span>
          </div>
          <div v-if="!link.hasSelection && !link.editing" class="mt-3"><label for="ln-text" class="label">Havola matni</label><input id="ln-text" v-model="link.text" class="field" placeholder="Masalan: AVTOREFERAT"></div>
          <label for="ln-url" class="label mt-3">Manzil (URL)</label>
          <div class="flex flex-wrap gap-2">
            <input id="ln-url" v-model="link.url" class="field min-w-[240px] flex-1" placeholder="https://… yoki serverdan tanlang" @keydown.enter.prevent="applyLink">
            <button type="button" class="btn-primary" @click="Object.assign(picker, { open: true, kind: 'pdf', for: 'link' })">Serverdan tanlaş</button>
          </div>
          <label class="mt-3 flex items-center gap-2 text-[13px]"><input v-model="link.newTab" type="checkbox" class="size-4 accent-brand-800"> Yangi oynada oçilsin</label>
          <div class="mt-4 flex flex-wrap justify-between gap-2">
            <button v-if="link.editing" type="button" class="btn-danger h-10!" @click="removeLink">Havolani olib taşlaş</button>
            <span v-else />
            <span class="flex gap-2">
              <button type="button" class="btn-ghost h-10!" @click="link.open = false">Bekor qiliş</button>
              <button type="button" class="btn-primary h-10!" :disabled="!link.url.trim()" @click="applyLink">Havolani qöyiş</button>
            </span>
          </div>
        </section>
      </div>

      <!-- Video oynasi -->
      <div v-if="video.open" class="fixed inset-0 z-[65] grid place-items-center bg-night/45 p-4" @click.self="video.open = false">
        <section role="dialog" aria-modal="true" aria-label="Video" class="w-full max-w-[520px] rounded-[20px] bg-white p-5 shadow-2xl">
          <h2 class="text-base font-bold">YouTube video qöşiş</h2>
          <label for="yt-url" class="label mt-3">Video havolasi</label>
          <input id="yt-url" v-model="video.url" class="field" placeholder="https://youtu.be/…" @keydown.enter.prevent="applyVideo">
          <div class="mt-4 flex justify-end gap-2">
            <button type="button" class="btn-ghost h-10!" @click="video.open = false">Bekor qiliş</button>
            <button type="button" class="btn-primary h-10!" :disabled="!video.url.trim()" @click="applyVideo">Qöşiş</button>
          </div>
        </section>
      </div>
    </Teleport>

    <MediaPicker :open="picker.open" :kind="picker.kind" @pick="onPick" @close="picker.open = false" />
  </div>
</template>

<style scoped>
.tool { height: 32px; min-width: 32px; padding: 0 7px; border-radius: 8px; font-size: 13px; font-weight: 700; color: #3d3958; display: inline-grid; place-items: center; }
.tool:hover:not(:disabled) { background: #f0eef6; }
.tool.on { background: #ecebfb; color: #2a2066; }
.tool:disabled { opacity: 0.35; cursor: not-allowed; }
.sep { width: 1px; height: 20px; margin: 0 4px; background: #e1deec; }
.sel { height: 32px; padding: 0 8px; border: 1px solid #e1deec; border-radius: 8px; background: #fff; font-size: 12px; font-weight: 600; color: #3d3958; }
.tbl { height: 30px; padding: 0 10px; border: 1px solid #e1deec; border-radius: 8px; background: #fff; }
.tbl:hover { border-color: #382b85; }
</style>
