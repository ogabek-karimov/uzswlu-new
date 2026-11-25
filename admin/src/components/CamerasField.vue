<script setup lang="ts">
// Onlayn kameralar (Online translatsiya): qöşiş, öçiriş, ko'z belgisi bilan yaşiriş/körsatiş. Sahifalar va «Onlayn kameralar» sahifasida.
import { ref } from 'vue'
import Icon from '@/components/Icon.vue'
import { type Camera, cameraUrl, parseCameraFile } from '@/lib/cameras'

const list = defineModel<Camera[]>({ required: true })
defineProps<{ bare?: boolean }>()
const hidingCam = ref<number | null>(null)
function toggleCam(i: number, sure = false) {
  const c = list.value[i]!
  if (!c.hidden && !sure) { hidingCam.value = i; return }
  hidingCam.value = null
  c.hidden = !c.hidden
}
const fileInput = ref<HTMLInputElement | null>(null)
const note = ref('')
async function onFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  const found = parseCameraFile(await file.text())
  if (!found.length) { note.value = 'Faylda rtsp.ru kamera havolasi topilmadi.'; return }
  let added = 0
  let updated = 0
  for (const f of found) {
    const old = list.value.find(c => c.name.trim().toLowerCase() === f.name.toLowerCase())
    if (old) { if (cameraUrl(old.url) !== f.url) { old.url = f.url; updated++ } }
    else { list.value.push({ name: f.name, url: f.url, hidden: false }); added++ }
  }
  note.value = `Fayldan ${found.length} ta kamera ökildi: ${added} ta yangi qöşildi, ${updated} ta havolasi yangilandi${added + updated ? '. Saqlaşni unutmang.' : ' — özgariş yöq.'}`
}
const removing = ref<number | null>(null)
function removeCam(i: number, sure = false) {
  const c = list.value[i]
  if (!c) return
  // Böş (hali kiritilmagan) qator sörovsiz olib taşlanadi
  if (!sure && (c.name.trim() || c.url.trim())) { removing.value = i; return }
  removing.value = null
  list.value.splice(i, 1)
}
</script>

<template>
<div :class="bare ? '' : 'rounded-xl border border-field p-3.5'">
  <div class="flex flex-wrap items-center justify-between gap-2">
    <span class="label mb-0!">{{ bare ? `Kameralar · ${list.length}` : 'Onlayn kameralar' }} <span class="font-normal">— saytda 2–3 ustunli setka, barça tillarda bir xil</span></span>
    <span class="flex flex-wrap gap-2">
      <button type="button" class="btn-ghost h-9! text-xs!" title="rtsp.ru bergan .txt fayl: nom va iframe kodlari — nechta bölsa, şunça kamera qöşiladi" @click="fileInput?.click()">Fayldan yuklaş (.txt)</button>
      <button type="button" class="btn-ghost h-9! text-xs!" @click="list.push({ name: '', url: '', hidden: false })">+ Kamera qöşiş</button>
    </span>
    <input ref="fileInput" type="file" accept=".txt,.html,.htm,text/plain,text/html" class="hidden" @change="onFile">
  </div>
  <p v-if="note" role="status" class="mt-2 rounded-lg bg-brand-50 px-3 py-2 text-xs text-brand-800">{{ note }}</p>
  <p v-if="!list.length" class="mt-2 text-sm text-muted">Kamera yöq.</p>
  <ul class="mt-2.5 flex flex-col gap-2">
    <li v-for="(c, i) in list" :key="i" class="flex flex-wrap items-center gap-2 rounded-lg border border-line p-2" :class="c.hidden && 'bg-canvas'">
      <button type="button" class="grid size-8 shrink-0 place-items-center rounded-lg" :class="c.hidden ? 'text-orange-600' : 'text-brand-700'" :aria-pressed="c.hidden" :title="c.hidden ? 'Yaşirin — körsatiş' : 'Saytda körinadi — yaşiriş'" :aria-label="`${c.name || 'Kamera'}: ${c.hidden ? 'körsatiş' : 'yaşiriş'}`" @click="toggleCam(i)"><Icon :name="c.hidden ? 'eye-off' : 'eye'" :size="16" /></button>
      <input v-model="c.name" class="field w-28! shrink-0" aria-label="Kamera nomi" placeholder="A-411">
      <input :value="c.url" class="field min-w-0 flex-1" aria-label="Havola yoki iframe kodi" placeholder="https://rtsp.ru/embed/… yoki <iframe …> kodi" @change="e => (c.url = cameraUrl((e.target as HTMLInputElement).value) || (e.target as HTMLInputElement).value)">
      <span v-if="c.url && !cameraUrl(c.url)" class="w-full text-xs text-red-700">Havola rtsp.ru/embed/… bölişi kerak — bu kamera saqlanmaydi.</span>
      <button type="button" class="grid size-8 shrink-0 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" :aria-label="`${c.name || 'Kamera'}ni öçiriş`" @click="removeCam(i)"><Icon name="trash" :size="14" /></button>
    </li>
  </ul>
</div>
  <div v-if="hidingCam !== null" class="fixed inset-0 z-[90] grid place-items-center bg-night/55 p-4" @click.self="hidingCam = null" @keydown.esc="hidingCam = null">
    <section role="alertdialog" aria-modal="true" aria-labelledby="cam-hide-title" aria-describedby="cam-hide-text" class="w-full max-w-[440px] rounded-[22px] bg-white p-6 shadow-2xl">
      <span class="grid size-11 place-items-center rounded-2xl bg-[#FEF3DC] text-[#B54708]"><Icon name="eye-off" :size="20" /></span>
      <h2 id="cam-hide-title" class="mt-4 text-xl font-bold tracking-tight">Kamera yaşirilsinmi?</h2>
      <p id="cam-hide-text" class="mt-2 text-[15px] leading-relaxed text-muted">«{{ list[hidingCam]?.name }}» saqlagandan keyin saytda körinmay qoladi. Uni istalgan payt ko'z belgisi orqali qayta körsatiş mumkin.</p>
      <div class="mt-5 flex flex-wrap justify-end gap-3">
        <button type="button" class="btn-ghost" @click="hidingCam = null">Bekor qiliş</button>
        <button type="button" class="btn-primary" @click="toggleCam(hidingCam!, true)">Ha, yaşiriş</button>
      </div>
    </section>
  </div>
  <div v-if="removing !== null" class="fixed inset-0 z-[90] grid place-items-center bg-night/55 p-4" @click.self="removing = null" @keydown.esc="removing = null">
    <section role="alertdialog" aria-modal="true" aria-labelledby="cam-del-title" aria-describedby="cam-del-text" class="w-full max-w-[440px] rounded-[22px] bg-white p-6 shadow-2xl">
      <span class="grid size-11 place-items-center rounded-2xl bg-red-50 text-red-700"><Icon name="trash" :size="20" /></span>
      <h2 id="cam-del-title" class="mt-4 text-xl font-bold tracking-tight">Kamera öçirilsinmi?</h2>
      <p id="cam-del-text" class="mt-2 text-[15px] leading-relaxed text-muted">«{{ list[removing]?.name || 'Nomsiz kamera' }}» röyxatdan olib taşlanadi va saqlagandan keyin saytda körinmaydi. Vaqtinça berkitiş kerak bölsa — ko'z belgisidan foydalaning.</p>
      <div class="mt-5 flex flex-wrap justify-end gap-3">
        <button type="button" class="btn-ghost" autofocus @click="removing = null">Orqaga</button>
        <button type="button" class="inline-flex h-11 items-center gap-2 rounded-xl bg-red-600 px-5 font-semibold text-white hover:bg-red-700" @click="removeCam(removing!, true)"><Icon name="trash" :size="16" />Öçiriş</button>
      </div>
    </section>
  </div>
</template>
