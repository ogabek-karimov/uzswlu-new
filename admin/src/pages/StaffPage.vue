<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type Paginated } from '@/lib/api'
import { initials } from '@/lib/auth'
import { LANGS, type Lang, SITE_URL } from '@/lib/constants'
import { hemisBadge, useHemis } from '@/lib/hemis'

// Xodimlar: F.I.Sh., lavozim va bo'lim HEMIS'dan; bio (4 tilda), ilmiy profillar va saytda ko'rinishi — shu yerda
type Profile = { id: number; hemisId: string; name?: string | null; bio?: I18n; orcid?: string | null; scholar?: string | null; scopus?: string | null; researchgate?: string | null; hidden?: boolean }

const hemis = useHemis()
const badge = computed(() => hemisBadge(hemis.value))
const profiles = ref<Profile[]>([])
const q = ref('')
const dept = ref('all')
const state = ref<'all' | 'todo' | 'hidden'>('all')
const sel = ref<string | null>(null)
const lang = ref<Lang>('uz')
const saving = ref(false)
const saved = ref(false)
const error = ref('')
const page = ref(1)
const PER = 25
const COLORS = ['#382B85', '#2A2066', '#4C3FA0', '#0E7A5A', '#6D5FD3', '#1C1548', '#C5192D']

const form = reactive({ bio: {} as I18n, orcid: '', scholar: '', scopus: '', researchgate: '', visible: true })

async function load() {
  profiles.value = (await api.get<Paginated<Profile>>('/staff-profiles', { limit: 5000, depth: 0 })).docs
}
onMounted(load)

const profileOf = (id: string) => profiles.value.find(p => p.hemisId === id)
function score(id: string) {
  const p = profileOf(id)
  const missing: string[] = []
  const bio = p?.bio ?? {}
  if (!bio.uz?.trim()) missing.push('bio')
  const langs = LANGS.filter(l => l.code !== 'uz' && !bio[l.code]?.trim()).length
  if (langs) missing.push(`${langs} til tarjimasi`)
  if (!p?.orcid && !p?.scholar && !p?.scopus && !p?.researchgate) missing.push('ilmiy profil')
  const total = 5
  const have = (bio.uz?.trim() ? 1 : 0) + (3 - langs) + (missing.includes('ilmiy profil') ? 0 : 1)
  return { pct: Math.round((have / total) * 100), missing }
}

const staff = computed(() => hemis.value?.staff ?? [])
const fold = (s: string) => s.toLowerCase().replace(/[‘’'`ʻʼ]/g, '')
const filtered = computed(() => {
  const words = fold(q.value).split(/\s+/).filter(Boolean)
  return staff.value.filter(s =>
    (dept.value === 'all' || s.employments.some(e => e.department.id === dept.value))
    && words.every(w => fold(`${s.name} ${s.id}`).includes(w))
    && (state.value === 'all' || (state.value === 'hidden' ? !!profileOf(s.id)?.hidden : score(s.id).pct < 100)))
})
const shown = computed(() => filtered.value.slice(0, page.value * PER))
const kpis = computed(() => {
  const all = staff.value
  const full = all.filter(s => score(s.id).pct === 100).length
  return [
    { label: 'Jami xodimlar (HEMIS)', value: all.length, color: '#13112F' },
    { label: 'Profili töliq', value: full, color: '#0E7A5A' },
    { label: 'Töldiriş kerak', value: all.length - full, color: '#8A5A00' },
    { label: 'Saytda yaşirilgan', value: profiles.value.filter(p => p.hidden).length, color: '#B42318' },
  ]
})
const current = computed(() => staff.value.find(s => s.id === sel.value) ?? null)

function pick(id: string) {
  sel.value = id
  saved.value = false
  error.value = ''
  const p = profileOf(id)
  Object.assign(form, { bio: { ...(p?.bio ?? {}) }, orcid: p?.orcid ?? '', scholar: p?.scholar ?? '', scopus: p?.scopus ?? '', researchgate: p?.researchgate ?? '', visible: !p?.hidden })
}

async function save() {
  if (!current.value) return
  saving.value = true
  error.value = ''
  const data = {
    hemisId: current.value.id, name: current.value.name, bio: form.bio,
    orcid: form.orcid.trim() || null, scholar: form.scholar.trim() || null, scopus: form.scopus.trim() || null, researchgate: form.researchgate.trim() || null,
    hidden: !form.visible,
  }
  try {
    const existing = profileOf(current.value.id)
    if (existing) await api.patch(`/staff-profiles/${existing.id}`, data)
    else await api.post('/staff-profiles', data)
    await load()
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

const color = (id: string) => COLORS[Number(id) % COLORS.length]
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Xodimlar</h1>
        <p class="mt-1.5 max-w-[700px] text-[15px] leading-normal text-muted">F.I.Ş., rasm, lavozim va kafedra HEMIS’dan keladi — ularni HEMIS’da özgartiriladi. Bu yerda bio (4 tilda) va ilmiy profillar töldiriladi.</p>
      </div>
      <div class="flex items-center gap-2.5 rounded-[14px] border border-line bg-white py-2 pr-2 pl-3.5">
        <span class="text-[13px] leading-snug"><b class="block">HEMIS sinxronlaş</b><span :class="badge.ok ? 'text-subtle' : 'text-[#8A5A00]'">{{ badge.ok ? badge.text.replace('HEMIS: ', '') : 'Hali ulanmagan' }} · {{ staff.length.toLocaleString('ru-RU') }} xodim</span></span>
        <button type="button" class="btn-primary h-[38px]! px-3! text-[13px]!" disabled title="HEMIS API ulanganda (universitet serverida) işlaydi">Hozir yangilaş</button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div v-for="k in kpis" :key="k.label" class="card px-4 py-3.5"><p class="text-[13px] text-muted">{{ k.label }}</p><p class="mt-1.5 text-[26px] font-bold" :style="{ color: k.color }">{{ k.value.toLocaleString('ru-RU') }}</p></div>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <section class="card min-w-0 flex-[999_1_560px] overflow-hidden p-0!">
        <div class="flex flex-wrap items-center gap-2.5 px-[18px] py-3.5">
          <label class="flex h-10 min-w-[200px] flex-[1_1_220px] items-center gap-2 rounded-[10px] border border-field px-3 text-muted">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
            <input v-model="q" aria-label="Ism yoki HEMIS ID" placeholder="Ism yoki HEMIS ID…" class="min-w-0 flex-1 bg-transparent text-[13px] outline-none" @input="page = 1">
          </label>
          <select v-model="dept" class="field h-10! w-auto! max-w-[260px]" aria-label="Bölim" @change="page = 1">
            <option value="all">Barça bölimlar</option>
            <option v-for="d in hemis?.staffDepartments ?? []" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
          <select v-model="state" class="field h-10! w-auto!" aria-label="Profil holati" @change="page = 1">
            <option value="all">Barça profillar</option>
            <option value="todo">Töldiriş kerak</option>
            <option value="hidden">Saytda yaşirilgan</option>
          </select>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[860px] border-collapse text-sm">
            <thead>
              <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
                <th scope="col" class="px-[18px] py-3 font-semibold">Xodim</th>
                <th scope="col" class="px-3 py-3 font-semibold">Bölim va lavozim</th>
                <th scope="col" class="px-3 py-3 font-semibold">Profil</th>
                <th scope="col" class="py-3 pr-[18px] pl-3 font-semibold">Bio tillari</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!shown.length"><td colspan="4" class="px-5 py-10 text-center text-muted">Xodim topilmadi.</td></tr>
              <tr v-for="s in shown" :key="s.id" class="cursor-pointer border-t border-[#F0EEF6] hover:bg-[#FAF9FD]" :class="[sel === s.id && 'bg-brand-50', profileOf(s.id)?.hidden && 'opacity-60']" @click="pick(s.id)">
                <td class="px-[18px] py-3">
                  <span class="flex items-center gap-2.5">
                    <span aria-hidden="true" class="grid size-[38px] shrink-0 place-items-center rounded-full text-xs font-bold text-white" :style="{ background: color(s.id) }">{{ initials(s.name) }}</span>
                    <span class="leading-tight"><button type="button" class="text-left font-bold" :aria-pressed="sel === s.id" @click.stop="pick(s.id)">{{ s.name }}</button><span class="block text-xs text-subtle">HEMIS ID {{ s.id }}<template v-if="profileOf(s.id)?.hidden"> · yaşirilgan</template></span></span>
                  </span>
                </td>
                <td class="max-w-[260px] px-3 py-3 text-[13px] leading-snug text-muted">{{ s.employments[0]?.department.name }}<span class="block font-semibold text-ink">{{ s.employments.map(e => e.position).join(', ') }}</span></td>
                <td class="min-w-[150px] px-3 py-3">
                  <div class="flex items-center gap-2">
                    <div class="h-[7px] flex-1 overflow-hidden rounded-full bg-[#F0EEF6]"><div class="h-full rounded-full" :style="{ width: `${score(s.id).pct}%`, background: score(s.id).pct === 100 ? '#12B76A' : score(s.id).pct >= 40 ? '#382B85' : '#F79009' }" /></div>
                    <span class="w-9 text-right text-xs font-bold">{{ score(s.id).pct }}%</span>
                  </div>
                  <span class="mt-1 block text-[11px] text-subtle">{{ score(s.id).missing.length ? `Yöq: ${score(s.id).missing.join(', ')}` : 'Töliq' }}</span>
                </td>
                <td class="py-3 pr-[18px] pl-3 whitespace-nowrap">
                  <span class="flex gap-[3px]"><span v-for="l in LANGS" :key="l.code" class="rounded-md px-1.5 py-[3px] text-[11px] font-bold" :class="profileOf(s.id)?.bio?.[l.code]?.trim() ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-canvas text-[#B8B4C8]'">{{ l.short }}</span></span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="shown.length < filtered.length" class="border-t border-[#F0EEF6] p-3 text-center"><button type="button" class="btn-ghost h-9!" @click="page++">Yana körsatiş ({{ filtered.length - shown.length }})</button></div>
      </section>

      <form v-if="current" class="card flex min-w-0 flex-[1_1_360px] flex-col gap-3 px-5 py-[18px]" @submit.prevent="save">
        <div class="flex items-center gap-3">
          <span aria-hidden="true" class="grid size-14 shrink-0 place-items-center rounded-full font-bold text-white" :style="{ background: color(current.id) }">{{ initials(current.name) }}</span>
          <span class="leading-snug"><b class="block text-base">{{ current.name }}</b><span class="text-[13px] text-muted">{{ current.employments.map(e => e.position).join(', ') }}</span></span>
        </div>
        <div>
          <span class="label">HEMIS’dan <span class="font-normal">— faqat öqiş</span></span>
          <div class="flex flex-col gap-1.5">
            <p class="rounded-[10px] bg-canvas px-3 py-2 text-[13px] text-[#3D3958]">🔒 F.I.Ş.: {{ current.name }}</p>
            <p v-for="(e, i) in current.employments" :key="i" class="rounded-[10px] bg-canvas px-3 py-2 text-[13px] text-[#3D3958]">🔒 {{ e.department.name }} · {{ e.position }}</p>
          </div>
        </div>
        <div>
          <div class="mb-1.5 flex items-center justify-between gap-2">
            <span class="label mb-0!">Bio</span>
            <div role="tablist" aria-label="Til" class="flex gap-1">
              <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
            </div>
          </div>
          <textarea v-model="form.bio[lang]" rows="4" class="field h-auto! py-2.5 leading-relaxed" :aria-label="`Bio · ${lang}`" />
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div><label for="sf-orcid" class="label">ORCID</label><input id="sf-orcid" v-model="form.orcid" class="field" placeholder="0000-0000-0000-0000"></div>
          <div><label for="sf-scholar" class="label">Google Scholar</label><input id="sf-scholar" v-model="form.scholar" class="field" type="url" placeholder="havola"></div>
          <div><label for="sf-scopus" class="label">Scopus ID</label><input id="sf-scopus" v-model="form.scopus" class="field"></div>
          <div><label for="sf-rg" class="label">ResearchGate</label><input id="sf-rg" v-model="form.researchgate" class="field" type="url" placeholder="havola"></div>
        </div>
        <label class="flex items-center gap-2.5 text-[13px] text-[#3D3958]"><input v-model="form.visible" type="checkbox" class="size-[18px] accent-brand-800"> Saytda körsatiş</label>
        <p class="rounded-[10px] bg-brand-50 px-3 py-2.5 text-xs leading-normal text-brand-800">Xodim bularni öz kabinetidan ham töldiriši mumkin.</p>
        <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <p v-else-if="saved" class="rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi — saytda yangilandi.</p>
        <div class="flex gap-2">
          <a :href="`${SITE_URL}/teacher/${current.id}`" target="_blank" rel="noopener" class="btn-ghost h-[42px]! flex-1">Saytda köriş ↗</a>
          <button type="submit" class="btn-primary h-[42px]! flex-1" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>
