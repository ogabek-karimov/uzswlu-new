<script setup lang="ts">
import type { CabinetAdminLink, CabinetTasks, CabinetDocSection, CabinetPatch, StaffCabinet, StaffContactType, StaffDocSection, StaffNetwork, StaffScienceNetwork } from '#shared/types/api'

// Xodim kabineti (oldingi saytdagi /site/dashboard ning yakuniy holati asosida).
// HEMIS (my.gov) orqali kirgan xodim o'z Staff sahifasidagi ma'lumotlarni shu yerda qo'shadi va o'zgartiradi;
// Staff sahifasida tahrirlash yo'q. Ism, lavozim, bo'lim va asl rasm — HEMIS'dan.

const { t, locale } = useI18n()
const localePath = useLocalePath()
const requestUrl = useRequestURL()

const { data: cabinet, error, refresh } = await useFetch<StaffCabinet>('/api/me', {
  key: 'cabinet',
  query: { lang: locale },
})

useSeo({ title: () => t('cabinet.title'), noindex: true })

const person = computed(() => cabinet.value?.profile)
const staffUrl = computed(() => (person.value ? `${requestUrl.origin}${localePath(`/teacher/${person.value.id}`)}` : ''))

// Kabinet bo'limlari: har biri alohida ko'rinadi (hammasi bir sahifaga tiqilib qolmasligi uchun). Manzilda `?bolim=...`
// «Yangiliklar» bo'limi faqat admin paneldagi roli yangilik/e'lon/tadbirga YOZISH ruxsati bergan xodimda chiqadi (backend rolni HEMIS lavozimidan biladi)
const POST_TYPES = ['news', 'announcements', 'events'] as const
const BASE_SECTIONS = [
  { key: 'overview', icon: 'lucide:layout-grid', label: 'dashboard' },
  { key: 'tasks', icon: 'lucide:list-checks', label: 'tasks' },
  { key: 'profile', icon: 'lucide:user-pen', label: 'profile' },
  { key: 'documents', icon: 'lucide:folder-open', label: 'documents' },
] as const
const NEWS_SECTION = { key: 'news', icon: 'lucide:newspaper', label: 'news' } as const
type SectionKey = typeof BASE_SECTIONS[number]['key'] | typeof NEWS_SECTION['key']
const route = useRoute()
const { data: tasks } = await useFetch<CabinetTasks>('/api/me/tasks', { key: 'cabinet-tasks', default: () => ({ mine: [], given: [], assignees: [] }) })
const openTasks = computed(() => tasks.value.mine.filter(x => x.status === 'open').length)

// «Admin panel»: xodimning admin hisobi bo'lsa (yoki lavozimi rolga bog'langan bo'lsa) tugma chiqadi; havola 60 soniyalik, bir martalik (bosilganda olinadi)
const { data: adminLink } = await useFetch<CabinetAdminLink>('/api/me/admin-link', { query: { list: 1 }, key: 'cabinet-admin-link', default: () => ({ available: false, url: null, role: null, sections: [] }) })
const postTypes = computed(() => POST_TYPES.filter(k => adminLink.value.sections.some(s => s.key === k && s.level === 'write')))
const SECTIONS = computed(() => (postTypes.value.length ? [...BASE_SECTIONS, NEWS_SECTION] : [...BASE_SECTIONS]))
const view = computed<SectionKey>(() => SECTIONS.value.find(s => s.key === route.query.bolim)?.key ?? 'overview')
const openingAdmin = ref(false)
async function openAdmin() {
  openingAdmin.value = true
  try {
    const link = await $fetch<CabinetAdminLink>('/api/me/admin-link')
    if (link.url) window.location.assign(link.url)
  }
  finally {
    openingAdmin.value = false
  }
}

const bannerOpen = ref(true)
const qrOpen = ref(false)
const shareOpen = ref(false)
const uploadSection = ref<CabinetDocSection | null>(null)

// Saqlash: o'zgargan qism yuboriladi, javobda yangilangan kabinet keladi
const saving = ref(false)
const failed = ref(false)
async function patch(body: CabinetPatch) {
  saving.value = true
  failed.value = false
  try {
    cabinet.value = await $fetch<StaffCabinet>('/api/me', { method: 'PATCH', query: { lang: locale.value }, body })
  }
  catch {
    failed.value = true
  }
  finally {
    saving.value = false
  }
}

function saveLinks(kind: 'contacts' | 'socials' | 'science', entries: { type: string; value: string }[]) {
  if (kind === 'contacts') patch({ contacts: entries.map(e => ({ type: e.type as StaffContactType, value: e.value })) })
  else if (kind === 'socials') patch({ socials: entries.map(e => ({ network: e.type as StaffNetwork, url: e.value })) })
  else patch({ science: entries.map(e => ({ network: e.type as StaffScienceNetwork, url: e.value })) })
}

function toggleDoc(section: StaffDocSection, visible: boolean) {
  patch({ visibility: { [section]: visible } })
}

// Rasm: o'z rasmi (JPG, PNG, WEBP, 10 MB gacha) yoki HEMIS rasmiga qaytish
const photoBusy = ref(false)
const photoError = ref('')
const removePhotoOpen = ref(false)
async function uploadPhoto(file: File) {
  photoError.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024) {
    photoError.value = t('cabinet.photo.bad')
    return
  }
  const form = new FormData()
  form.append('file', file)
  photoBusy.value = true
  try {
    await $fetch('/api/me/avatar', { method: 'POST', body: form })
    await refresh()
  }
  catch {
    photoError.value = t('cabinet.error')
  }
  finally {
    photoBusy.value = false
  }
}
async function removePhoto() {
  photoBusy.value = true
  try {
    await $fetch('/api/me/avatar', { method: 'DELETE' })
    await refresh()
  }
  finally {
    photoBusy.value = false
  }
}

const menuClass = 'flex items-center gap-3 rounded-[14px] px-3.5 py-3 font-medium text-ink transition-colors hover:bg-paper'
</script>

<template>
  <div>
    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
      <PageBreadcrumbs :items="[{ label: t('cabinet.title') }]" />
    </section>

    <!-- Kirilmagan (backend 401) -->
    <section v-if="error || !cabinet || !person" class="mx-auto max-w-3xl px-4 py-24 text-center sm:px-6">
      <span class="mx-auto grid size-16 place-items-center rounded-2xl bg-brand-50 text-brand-700"><Icon name="lucide:lock" class="size-7" /></span>
      <p class="mt-6 text-lg text-muted">{{ t('cabinet.error') }}</p>
    </section>

    <section v-else class="mx-auto flex max-w-7xl flex-col gap-7 px-4 pt-7 pb-24 sm:px-6 lg:flex-row lg:items-start lg:px-8">
      <!-- ===== Chap ustun ===== -->
      <div class="flex flex-col gap-5 lg:w-[380px] lg:shrink-0">
        <StaffProfileCard
          :person="person"
          editable-photo
          :has-own-photo="cabinet.hasOwnPhoto"
          :busy="photoBusy"
          @photo="uploadPhoto"
          @remove-photo="removePhotoOpen = true"
        >
          <p v-if="photoError" role="alert" class="mt-4 rounded-xl bg-white/10 px-3 py-2 text-sm text-white">{{ photoError }}</p>
          <NuxtLink
            :to="localePath(`/teacher/${person.id}`)"
            class="mt-6 flex h-13 w-full items-center justify-center gap-2 rounded-2xl bg-accent-400 font-bold text-ink transition hover:bg-accent-300 hover:shadow-[0_0_24px_rgba(0,252,180,0.45)]"
          >
            <Icon name="lucide:circle-user-round" class="size-[18px]" />
            {{ t('cabinet.myPage') }}
          </NuxtLink>
          <div class="mt-2.5 grid grid-cols-2 gap-2.5">
            <button
              v-for="a in [{ key: 'qr', icon: 'lucide:qr-code' }, { key: 'share', icon: 'lucide:share-2' }]"
              :key="a.key"
              type="button"
              aria-haspopup="dialog"
              class="flex h-11.5 items-center justify-center gap-2 rounded-[14px] border border-white/22 bg-white/6 text-sm font-semibold text-white transition hover:border-white/50 hover:bg-white/12"
              @click="a.key === 'qr' ? (qrOpen = true) : (shareOpen = true)"
            >
              <Icon :name="a.icon" class="size-[17px]" />
              {{ t(`staff.profile.${a.key}`) }}
            </button>
          </div>
        </StaffProfileCard>

        <!-- Menyu ("Ma'lumotlar qo'shish" olib tashlangan — oldingi saytdagidek) -->
        <nav :aria-label="t('cabinet.menu.label')" class="rounded-3xl border border-line bg-white p-5">
          <p class="mb-3 ml-2 text-xs font-bold tracking-[0.18em] text-muted uppercase">{{ t('cabinet.menu.label') }}</p>
          <NuxtLink
            v-for="s in SECTIONS"
            :key="s.key"
            :to="{ query: s.key === 'overview' ? {} : { bolim: s.key } }"
            :aria-current="view === s.key ? 'page' : undefined"
            :class="[view === s.key ? 'flex items-center gap-3 rounded-[14px] bg-accent-100 px-3.5 py-3 font-bold text-accent-700' : menuClass, 'mt-1 first:mt-0']"
          >
            <Icon :name="s.icon" class="size-5" />
            {{ t(`cabinet.menu.${s.label}`) }}
            <span v-if="s.key === 'tasks' && openTasks" class="ml-auto rounded-full bg-accent-400 px-2 py-0.5 text-xs font-bold text-ink">{{ openTasks }}</span>
          </NuxtLink>
          <button v-if="adminLink.available" type="button" :disabled="openingAdmin" :class="[menuClass, 'mt-1 w-full text-left']" @click="openAdmin">
            <Icon name="lucide:shield-check" class="size-5" />
            {{ t('cabinet.menu.admin') }}
          </button>
          <NuxtLink :to="localePath(`/teacher/${person.id}`)" :class="[menuClass, 'mt-1']">
            <Icon name="lucide:id-card" class="size-5" />
            {{ t('cabinet.menu.staffPage') }}
          </NuxtLink>
          <!-- Chiqish: backend sessiyasini yopadi (manzilni backend beradi) -->
          <a href="/logout" :class="[menuClass, 'mt-1']">
            <Icon name="lucide:log-out" class="size-5" />
            {{ t('cabinet.menu.logout') }}
          </a>
        </nav>

        <!-- Texnik yordam -->
        <div class="flex gap-4 rounded-3xl bg-[linear-gradient(135deg,var(--color-brand-50),var(--color-accent-100))] p-5">
          <span class="grid size-12 shrink-0 place-items-center rounded-2xl bg-brand-900 text-accent-400"><Icon name="lucide:headset" class="size-[22px]" /></span>
          <span>
            <b class="block text-ink">{{ t('cabinet.support.title') }}</b>
            <span class="mt-1 block text-sm leading-relaxed text-muted">{{ t('cabinet.support.text') }}</span>
            <NuxtLink :to="localePath('/aloqa')" class="mt-2 inline-flex items-center gap-1.5 font-bold text-accent-600 hover:underline">
              {{ t('cabinet.support.link') }}
              <Icon name="lucide:arrow-up-right" class="size-4" />
            </NuxtLink>
          </span>
        </div>
      </div>

      <!-- ===== O'ng ustun ===== -->
      <div class="flex min-w-0 flex-1 flex-col gap-5">
        <div v-if="bannerOpen && view === 'overview'" class="relative rounded-[20px] border border-[#f3dfa2] bg-[#fff6db] py-4 pr-14 pl-5 text-[#5a4300]">
          <b>{{ t('cabinet.banner.title') }}</b> {{ t('cabinet.banner.text') }}
          <button type="button" :aria-label="t('cabinet.close')" class="absolute top-3 right-3 grid size-8 place-items-center rounded-full transition-colors hover:bg-[#f3dfa2]" @click="bannerOpen = false">
            <Icon name="lucide:x" class="size-[18px]" />
          </button>
        </div>

        <p v-if="failed" role="alert" class="rounded-2xl bg-[#fdecec] px-5 py-3 text-[#8e1b1b]">{{ t('cabinet.error') }}</p>

        <template v-if="view === 'overview'">
          <CabinetRolePanel v-if="cabinet.panel" :role="cabinet.role" :panel="cabinet.panel" :person-id="person.id" />
          <CabinetHemisCard :cabinet="cabinet" />
        </template>
        <CabinetTasks v-else-if="view === 'tasks'" />
        <CabinetPosts v-else-if="view === 'news'" :types="[...postTypes]" />
        <template v-else-if="view === 'profile'">
        <CabinetAboutCard :about="cabinet.about" :text="person.about" :saving="saving" @save="about => patch({ about })" />
        <CabinetLinksCard kind="contacts" :title="t('staff.profile.contact')" :person="person" @save="e => saveLinks('contacts', e)" />
        <CabinetLinksCard kind="socials" :title="t('staff.profile.socials')" :person="person" @save="e => saveLinks('socials', e)" />
        <CabinetLinksCard kind="science" :title="t('staff.profile.science')" :person="person" @save="e => saveLinks('science', e)" />
        </template>
        <CabinetDocuments v-else :documents="cabinet.documents" @toggle="toggleDoc" @open="s => (uploadSection = s)" />
      </div>
    </section>

    <template v-if="person">
      <StaffQrShare v-model:qr="qrOpen" v-model:share="shareOpen" :person="person" :url="staffUrl" />
      <CabinetUploadDialog v-model:section="uploadSection" @changed="refresh()" />
      <AppConfirm
        v-model:open="removePhotoOpen"
        :title="t('cabinet.photo.removeTitle')"
        :text="t('cabinet.photo.removeText')"
        :confirm-label="t('cabinet.photo.removeYes')"
        :cancel-label="t('cabinet.cancel')"
        @confirm="removePhoto"
      />
    </template>
  </div>
</template>
