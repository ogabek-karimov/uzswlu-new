<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import ProfileSecurity from '@/components/profile/ProfileSecurity.vue'
import { api, ApiError, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { auth, initials, roleLabel } from '@/lib/auth'
import { POST_TYPES } from '@/lib/constants'
import { dateTime, relative } from '@/lib/format'
import { mediaUrl, type Post, postState, STATE_BADGE } from '@/lib/posts'
import { SECTION_PATHS, SECTIONS } from '@/lib/roles'

// Mening profilim: kim ekanim (rol, ruxsatlar), saytdagi muallif ko'rinishi, so'nggi postlarim va xavfsizlik (parol, 2FA)
const route = useRoute()
const router = useRouter()
const me = auth.user
const tab = computed(() => (route.query.tab === 'xavfsizlik' ? 'security' : 'general'))
const setTab = (t: 'general' | 'security') => router.replace({ query: t === 'security' ? { tab: 'xavfsizlik' } : {} })

const info = reactive({ name: '', position: '', department: '' })
const fill = () => Object.assign(info, { name: me.value?.name ?? '', position: me.value?.position ?? '', department: me.value?.department ?? '' })
fill()
watch(me, fill)
const dirty = computed(() => info.name !== (me.value?.name ?? '') || info.position !== (me.value?.position ?? '') || info.department !== (me.value?.department ?? ''))
const saving = ref(false)
const error = ref('')
const message = ref('')

const avatar = computed(() => (me.value?.avatar && typeof me.value.avatar === 'object' ? mediaUrl(me.value.avatar as MediaDoc, 'card') : null))
const canUpload = computed(() => auth.can('media', 'write'))
const uploading = ref(false)
const fileInput = ref<HTMLInputElement>()

const isSuper = computed(() => me.value?.role === 'superadmin')
const sections = computed(() => {
  const perms = me.value?.permissions ?? {}
  const groups = [...new Set(SECTIONS.map(s => s.group))]
  return groups
    .map(g => ({ group: g, items: SECTIONS.filter(s => s.group === g && s.key !== 'dashboard' && (isSuper.value || perms[s.key])).map(s => ({ ...s, level: isSuper.value ? 'write' : perms[s.key]! })) }))
    .filter(g => g.items.length)
})
const writeCount = computed(() => sections.value.flatMap(g => g.items).filter(s => s.level === 'write').length)

// Profil to'liqligi: saytda muallif sifatida chiqadigan ma'lumot + himoya
const steps = computed(() => [
  { ok: !!me.value?.name?.trim(), label: 'F.I.Ş.' },
  { ok: !!me.value?.position?.trim(), label: 'Lavozim' },
  { ok: !!me.value?.department?.trim(), label: 'Bölim' },
  { ok: !!avatar.value, label: 'Rasm' },
  { ok: !!me.value?.twoFactorEnabled, label: '2FA' },
])
const percent = computed(() => Math.round(steps.value.filter(s => s.ok).length / steps.value.length * 100))

const postTypes = computed(() => POST_TYPES.filter(t => auth.can(t.value)).map(t => t.value))
const myPosts = ref<Post[] | null>(null)
const myTotal = ref(0)
async function loadPosts() {
  if (!postTypes.value.length || !me.value) return
  const res = await api.get<Paginated<Post>>('/posts', { where: { and: [{ author: { equals: me.value.id } }, { type: { in: postTypes.value.join(',') } }] }, sort: '-updatedAt', limit: 5, depth: 1 })
  myPosts.value = res.docs
  myTotal.value = res.totalDocs
}
onMounted(() => loadPosts().catch(() => { myPosts.value = [] }))

async function saveInfo() {
  error.value = ''
  saving.value = true
  try {
    await api.patch(`/users/${me.value!.id}`, info)
    await auth.me()
    flash('Ma’lumotlar saqlandi')
  }
  catch (e) { error.value = e instanceof ApiError ? e.message : 'Saqlab bölmadi' }
  finally { saving.value = false }
}

async function onAvatar(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  error.value = ''
  try {
    const m = await uploadMedia(file, { folder: 'staff' })
    await api.patch(`/users/${me.value!.id}`, { avatar: m.id })
    await auth.me()
    flash('Rasm yangilandi')
  }
  catch (err) { error.value = (err as Error).message || 'Rasmni yuklab bölmadi' }
  finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function removeAvatar() {
  await api.patch(`/users/${me.value!.id}`, { avatar: null })
  await auth.me()
  flash('Rasm olib taşlandi')
}

function flash(text: string) {
  message.value = text
  setTimeout(() => { if (message.value === text) message.value = '' }, 3000)
}
const typeLabel = (t: string) => POST_TYPES.find(p => p.value === t)?.label ?? t
</script>

<template>
  <div class="flex flex-col gap-5">
    <!-- Bosh qism: rasm, ism, rol, asosiy belgilar -->
    <section class="card overflow-hidden">
      <div class="relative h-[132px] overflow-hidden bg-gradient-to-br from-night via-brand-900 to-brand-700">
        <span aria-hidden="true" class="absolute -top-40 -right-16 size-[380px] rounded-full border-[46px] border-mint/10" />
        <span aria-hidden="true" class="absolute -bottom-24 left-1/3 size-[220px] rounded-full border-[30px] border-white/5" />
      </div>
      <div class="relative -mt-14 flex flex-wrap items-start gap-x-6 gap-y-4 px-6 pb-6">
        <div class="relative shrink-0">
          <img v-if="avatar" :src="avatar" alt="" class="size-28 rounded-[28px] object-cover shadow-[0_0_0_5px_#fff]">
          <span v-else class="grid size-28 place-items-center rounded-[28px] bg-gradient-to-br from-brand-700 to-night text-[38px] font-bold text-mint shadow-[0_0_0_5px_#fff]">{{ initials(me?.name) }}</span>
          <template v-if="canUpload">
            <button type="button" class="absolute -right-1.5 -bottom-1.5 grid size-9 place-items-center rounded-full bg-white text-brand-700 shadow-md ring-1 ring-line hover:bg-brand-50" :aria-label="avatar ? 'Rasmni almaştiriş' : 'Rasm yuklaş'" :disabled="uploading" @click="fileInput?.click()">
              <Icon :name="uploading ? 'upload' : 'image'" :size="16" />
            </button>
            <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" @change="onAvatar">
          </template>
        </div>
        <div class="min-w-0 flex-[1_1_280px] sm:pt-[68px]">
          <h1 class="text-[28px] leading-tight font-bold tracking-tight [overflow-wrap:anywhere]">{{ me?.name }}</h1>
          <p class="mt-1 text-sm text-muted">{{ [me?.position, me?.department].filter(Boolean).join(' · ') || 'Lavozim kiritilmagan' }}</p>
          <div class="mt-3 flex flex-wrap items-center gap-2">
            <span class="chip bg-brand-50 text-brand-800">{{ roleLabel(me) }}</span>
            <span class="chip bg-[#F1F0F5] text-muted">login: {{ me?.username }}</span>
            <span class="chip" :class="me?.twoFactorEnabled ? 'bg-[#E3F6EE] text-[#0B5A43]' : 'bg-[#FEF3DC] text-[#8A5A00]'">2FA {{ me?.twoFactorEnabled ? 'yoqilgan' : 'öçiq' }}</span>
            <button v-if="avatar && canUpload" type="button" class="text-xs font-semibold text-muted hover:text-red-700" @click="removeAvatar">Rasmni olib taşlaş</button>
          </div>
        </div>
        <dl class="grid w-full grid-cols-3 gap-3 sm:w-auto sm:min-w-[420px] sm:pt-[68px]">
          <div class="rounded-2xl bg-canvas px-4 py-3"><dt class="text-xs text-muted">Oxirgi kiriş</dt><dd class="mt-1 text-sm font-semibold">{{ me?.lastLogin ? relative(me.lastLogin) : '—' }}</dd></div>
          <div class="rounded-2xl bg-canvas px-4 py-3"><dt class="text-xs text-muted">Postlarim</dt><dd class="mt-1 text-sm font-semibold">{{ postTypes.length ? myTotal : '—' }}</dd></div>
          <div class="rounded-2xl bg-canvas px-4 py-3"><dt class="text-xs text-muted">Hisob oçilgan</dt><dd class="mt-1 text-sm font-semibold">{{ me?.createdAt ? dateTime(me.createdAt).split(' · ')[0] : '—' }}</dd></div>
        </dl>
      </div>
    </section>

    <div role="tablist" aria-label="Profil bölimlari" class="flex gap-1 self-start rounded-2xl bg-white p-1 ring-1 ring-line">
      <button type="button" role="tab" :aria-selected="tab === 'general'" class="h-10 rounded-xl px-4 text-sm font-semibold" :class="tab === 'general' ? 'bg-night text-white' : 'text-muted hover:text-ink'" @click="setTab('general')">Umumiy</button>
      <button type="button" role="tab" :aria-selected="tab === 'security'" class="flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-semibold" :class="tab === 'security' ? 'bg-night text-white' : 'text-muted hover:text-ink'" @click="setTab('security')">
        Xavfsizlik<span v-if="!me?.twoFactorEnabled" class="size-2 rounded-full bg-[#F79009]" aria-label="2FA öçiq" />
      </button>
    </div>

    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{{ error }}</p>

    <ProfileSecurity v-if="tab === 'security'" @done="flash" />

    <div v-else class="grid items-start gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
      <div class="flex min-w-0 flex-col gap-5">
        <section class="card flex flex-col gap-3.5 p-[22px]">
          <div><h2 class="text-base font-bold">Ma’lumotlarim</h2><p class="mt-1 text-[13px] text-muted">Yangilik muallifi sifatida saytda şu ism va lavozim çiqadi.</p></div>
          <div><label for="pr-name" class="label">F.I.Ş.</label><input id="pr-name" v-model="info.name" class="field"></div>
          <div class="grid gap-3.5 sm:grid-cols-2">
            <div><label for="pr-pos" class="label">Lavozim</label><input id="pr-pos" v-model="info.position" class="field" placeholder="Masalan: Matbuot xizmati"></div>
            <div><label for="pr-dep" class="label">Bölim</label><input id="pr-dep" v-model="info.department" class="field"></div>
          </div>
          <div class="rounded-2xl border border-dashed border-line bg-[#FBFAFE] p-4">
            <p class="text-[11px] font-bold tracking-[0.14em] text-muted uppercase">Saytda şunday körinadi</p>
            <div class="mt-2.5 flex items-center gap-3">
              <img v-if="avatar" :src="avatar" alt="" class="size-10 rounded-full object-cover">
              <span v-else class="grid size-10 place-items-center rounded-full bg-night text-sm font-bold text-mint">{{ initials(info.name) }}</span>
              <span class="leading-tight"><b class="block text-sm">{{ info.name || '—' }}</b><span class="text-xs text-muted">{{ info.position || 'lavozim' }}</span></span>
            </div>
          </div>
          <div class="flex items-center justify-end gap-3">
            <span v-if="dirty" class="text-[13px] text-[#8A5A00]">Saqlanmagan özgarişlar bor</span>
            <button type="button" class="btn-primary" :disabled="saving || !dirty" @click="saveInfo">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
          </div>
        </section>

        <section v-if="postTypes.length" class="card overflow-hidden">
          <div class="flex items-center justify-between gap-3 px-[22px] pt-[22px] pb-3">
            <h2 class="text-base font-bold">So‘nggi postlarim</h2>
            <RouterLink :to="`/postlar/${postTypes[0]}`" class="text-[13px] font-semibold text-brand-700">Hammasi →</RouterLink>
          </div>
          <p v-if="myPosts === null" class="px-[22px] pb-5 text-sm text-muted">Yuklanmoqda…</p>
          <p v-else-if="!myPosts.length" class="px-[22px] pb-5 text-sm text-muted">Hali post yozmagansiz.</p>
          <ul v-else class="divide-y divide-line">
            <li v-for="p in myPosts" :key="p.id">
              <RouterLink :to="`/postlar/${p.type}/${p.id}`" class="flex items-center gap-3 px-[22px] py-3 hover:bg-canvas">
                <Icon :name="p.type" :size="18" class="shrink-0 text-subtle" />
                <span class="min-w-0 flex-1"><b class="block truncate text-sm">{{ p.title?.uz || '—' }}</b><span class="text-xs text-muted">{{ typeLabel(p.type) }} · {{ relative(p.updatedAt) }}</span></span>
                <span class="chip shrink-0" :class="STATE_BADGE[postState(p)].cls">{{ STATE_BADGE[postState(p)].label }}</span>
              </RouterLink>
            </li>
          </ul>
        </section>
      </div>

      <div class="flex min-w-0 flex-col gap-5">
        <section class="card p-[22px]">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-base font-bold">Profil töliqligi</h2>
            <b class="text-sm" :class="percent === 100 ? 'text-[#0B5A43]' : 'text-brand-700'">{{ percent }}%</b>
          </div>
          <div class="mt-3 h-2 overflow-hidden rounded-full bg-[#ECEAF3]"><div class="h-full rounded-full bg-gradient-to-r from-brand-700 to-mint transition-all" :style="{ width: `${percent}%` }" /></div>
          <ul class="mt-3.5 flex flex-wrap gap-2">
            <li v-for="s in steps" :key="s.label" class="chip" :class="s.ok ? 'bg-[#E3F6EE] text-[#0B5A43]' : 'bg-[#F1F0F5] text-muted'">{{ s.ok ? '✓' : '○' }} {{ s.label }}</li>
          </ul>
          <button v-if="!me?.twoFactorEnabled" type="button" class="mt-3.5 text-[13px] font-semibold text-brand-700" @click="setTab('security')">2FA ni yoqiş →</button>
        </section>

        <section class="card p-[22px]">
          <h2 class="text-base font-bold">Rolim va ruxsatlarim</h2>
          <div class="mt-3 rounded-2xl bg-night p-4 text-white">
            <p class="text-lg font-bold">{{ roleLabel(me) }}</p>
            <p class="mt-1 text-[13px] leading-snug text-white/65">{{ isSuper ? 'Hamma bölim, foydalanuvçilar, rollar va sozlamalar.' : (me?.roleDescription || `${writeCount} ta bölimda yozish, qolganida körish`) }}</p>
            <p v-if="me?.scoped" class="mt-2 text-xs text-mint">Faqat öz fakulteti doirasida{{ me?.scope ? `: ${me.scope}` : '' }}</p>
          </div>
          <div v-for="g in sections" :key="g.group" class="mt-4">
            <p class="mb-1.5 text-[11px] font-bold tracking-[0.14em] text-muted uppercase">{{ g.group }}</p>
            <ul class="grid gap-1.5">
              <li v-for="s in g.items" :key="s.key">
                <RouterLink :to="SECTION_PATHS[s.key] ?? '/'" class="flex items-center justify-between gap-3 rounded-xl border border-line px-3 py-2 text-sm hover:border-brand-700">
                  <span class="font-medium">{{ s.label }}</span>
                  <span class="chip" :class="s.level === 'write' ? 'bg-brand-50 text-brand-800' : 'bg-[#F1F0F5] text-muted'">{{ s.level === 'write' ? 'yozish' : 'körish' }}</span>
                </RouterLink>
              </li>
            </ul>
          </div>
          <p class="mt-4 text-xs leading-snug text-subtle">Ruxsatni superadmin «Rollar» sahifasida özgartiradi. Har bir amalingiz faollik jurnalida saqlanadi.</p>
        </section>
      </div>
    </div>

    <div v-if="message" role="status" class="fixed right-6 bottom-6 z-50 rounded-2xl bg-night px-4 py-3 text-sm font-semibold text-white shadow-xl">{{ message }}</div>
  </div>
</template>
