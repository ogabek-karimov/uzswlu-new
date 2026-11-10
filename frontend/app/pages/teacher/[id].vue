<script setup lang="ts">
import type { StaffContactType, StaffProfile } from '#shared/types/api'

// Xodim profili (faqat ko'rish) — oldingi saytdagi /teacher/<id> ning yakuniy holati asosida.
// Ma'lumotlarni xodimning o'zi dashboard'da kiritadi; bo'sh bo'limlar umuman chiqmaydi.

const { t, locale } = useI18n()
const localePath = useLocalePath()
const route = useRoute()
const requestUrl = useRequestURL()

const id = computed(() => String(route.params.id))

const { data: person, error } = await useFetch<StaffProfile>(() => `/api/staff/${id.value}`, {
  key: `staff-${id.value}`,
  query: { lang: locale },
})
if (error.value) {
  throw createError({ statusCode: error.value.statusCode ?? 500, statusMessage: error.value.statusMessage, fatal: true })
}

// Pastdagi karusel — bosh sahifadagi bilan bir xil bannerlar
const { data: home } = await useHomeData()

// Ism HEMIS tartibida; sharif yo'q bo'lsa oxiriga qo'shiladi
const names = computed(() => staffName(person.value?.name ?? '', person.value?.patronymic))
// Lavozim va bo'limlar HEMIS ish joylaridan: avval boshqaruv lavozimi, keyin o'qituvchilik lavozimlari (kod 11–15)
const roles = computed(() => staffRoles(person.value?.employments ?? []))
const positionText = computed(() => roles.value.positions.join(', '))
const tiles = computed(() => (person.value ? staffTiles(person.value, t) : { contacts: [], socials: [], science: [] }))

// "Bog'lanish" oynasi: qo'ng'iroq, WhatsApp, Telegram, e-pochta (vCard/"kontaktni saqlash" yo'q)
const firstOf = (type: StaffContactType) => person.value?.contacts.find(c => c.type === type)
const connectOptions = computed(() => {
  const call = firstOf('mobile') ?? firstOf('phone')
  const out: { key: string; label: string; icon: string; tile: string; href: string; external?: boolean }[] = []
  if (call) out.push({ key: 'call', label: t('staff.profile.call'), icon: 'lucide:phone-call', tile: 'bg-[#2e7d32]', href: staffContacts[call.type].href(call.value) })
  const wa = firstOf('whatsapp')
  if (wa) out.push({ key: 'whatsapp', label: t('staff.profile.writeWhatsapp'), icon: 'simple-icons:whatsapp', tile: 'bg-[#25d366]', href: staffContacts.whatsapp.href(wa.value), external: true })
  const tg = firstOf('telegram')
  if (tg) out.push({ key: 'telegram', label: t('staff.profile.writeTelegram'), icon: 'simple-icons:telegram', tile: 'bg-[#229ed9]', href: staffContacts.telegram.href(tg.value), external: true })
  const mail = firstOf('email')
  if (mail) out.push({ key: 'email', label: t('staff.profile.sendEmail'), icon: 'lucide:mail', tile: 'bg-brand-900', href: staffContacts.email.href(mail.value) })
  return out
})

const optionClass = 'flex w-full items-center gap-3.5 rounded-2xl border border-line p-3 text-left font-semibold text-ink transition-colors hover:border-accent-500 hover:bg-paper'

// Oynalar: Bog'lanish, QR kod, Ulashish (oldingi uzswlu.uz/teacher sahifasidagi kabi)
const contactOpen = ref(false)
const qrOpen = ref(false)
const shareOpen = ref(false)
const bottomActions = [
  { key: 'qr', icon: 'lucide:qr-code', open: () => { qrOpen.value = true } },
  { key: 'share', icon: 'lucide:share-2', open: () => { shareOpen.value = true } },
]
const pageUrl = computed(() => `${requestUrl.origin}${route.path}`)

useSeo({
  title: () => names.value.full,
  description: () => (person.value ? `${positionText.value} — ${roles.value.departments.map(d => d.name).join(', ')}` : undefined),
  type: 'profile',
  image: () => person.value?.photo || person.value?.photoFallback,
})
</script>

<template>
  <div v-if="person">
    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
      <PageBreadcrumbs :items="[{ label: t('staff.university') }, { label: t('staff.title'), to: '/staff' }, { label: names.full }]" />
    </section>

    <section class="mx-auto flex max-w-7xl flex-col gap-7 px-4 pt-7 sm:px-6 lg:flex-row lg:items-start lg:px-8">
      <!-- Chap karta: kompyuterda scroll'da qotib turadi -->
      <StaffProfileCard :person="person" class="lg:sticky lg:top-36 lg:w-[380px] lg:shrink-0">
        <button
          v-if="connectOptions.length"
          type="button"
          aria-haspopup="dialog"
          class="mt-6 flex h-13 w-full items-center justify-center gap-2 rounded-2xl bg-accent-400 font-bold text-ink transition hover:-translate-y-0.5 hover:bg-accent-300 hover:shadow-[0_0_24px_rgba(0,252,180,0.45)]"
          @click="contactOpen = true"
        >
          <Icon name="lucide:message-square-text" class="size-[18px]" />
          {{ t('staff.profile.connect') }}
        </button>
      </StaffProfileCard>

      <!-- O'ng tomon -->
      <div class="flex min-w-0 flex-1 flex-col gap-5">
        <StaffSection :title="t('staff.profile.about')">
          <dl class="mt-5 grid gap-x-7 gap-y-5 sm:grid-cols-3">
            <div>
              <dt class="text-sm text-muted">{{ t('staff.profile.fullName') }}</dt>
              <dd class="mt-1 text-lg leading-snug font-bold break-words text-ink">{{ names.full }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted">{{ t('staff.profile.department') }}</dt>
              <dd class="mt-1 text-lg leading-snug font-bold">
                <template v-for="(d, i) in roles.departments" :key="d.id">
                  <NuxtLink
                    :to="{ path: localePath('/staff'), query: { department: d.id } }"
                    class="text-ink underline decoration-accent-500 underline-offset-4 transition-colors hover:text-accent-600"
                  >{{ d.name }}</NuxtLink><template v-if="i < roles.departments.length - 1">, </template>
                </template>
              </dd>
            </div>
            <div>
              <dt class="text-sm text-muted">{{ t('staff.profile.position') }}</dt>
              <dd class="mt-1 text-lg leading-snug font-bold text-ink">{{ positionText }}</dd>
            </div>
          </dl>
          <p v-if="person.about" class="mt-5 text-[17px] leading-relaxed text-ink">{{ person.about }}</p>
        </StaffSection>

        <StaffSection v-if="tiles.contacts.length" :title="t('staff.profile.contact')">
          <StaffTiles :tiles="tiles.contacts" class="mt-4.5" />
        </StaffSection>

        <StaffSection v-if="tiles.socials.length" :title="t('staff.profile.socials')">
          <StaffTiles :tiles="tiles.socials" class="mt-4.5" />
        </StaffSection>

        <StaffSection v-if="tiles.science.length" :title="t('staff.profile.science')">
          <StaffTiles :tiles="tiles.science" class="mt-4.5" />
        </StaffSection>

        <!-- Hujjatlar: CV, Kitoblar, Maqolalar — xodim yashirmagan va bo'sh bo'lmaganlari -->
        <StaffSection v-if="person.documents.length" :title="t('staff.profile.documents')">
          <div class="mt-4.5 grid gap-3">
            <details v-for="doc in person.documents" :key="doc.section" class="group/d rounded-[18px] border border-line bg-white transition hover:border-accent-500">
              <summary class="flex cursor-pointer list-none items-center gap-3.5 p-4 [&::-webkit-details-marker]:hidden">
                <span class="grid size-11 shrink-0 place-items-center rounded-xl text-white" :class="staffDocs[doc.section].tile"><Icon :name="staffDocs[doc.section].icon" class="size-5" /></span>
                <span class="flex-1 font-bold text-ink">{{ t(`staff.docs.${doc.section}`) }}</span>
                <span class="rounded-full bg-paper px-2.5 py-1 text-xs font-semibold text-muted">{{ t('staff.profile.count', { n: doc.items.length }) }}</span>
                <Icon name="lucide:chevron-down" class="size-5 text-muted transition-transform group-open/d:rotate-180" />
              </summary>
              <ul class="grid gap-1 border-t border-line px-4 py-3">
                <li v-for="(item, i) in doc.items" :key="i">
                  <a :href="item.url" target="_blank" rel="noopener" class="flex items-center gap-2.5 rounded-xl px-2 py-2 text-[15px] text-ink transition-colors hover:bg-paper">
                    <Icon name="lucide:file-text" class="size-4 shrink-0 text-muted" />
                    <span class="min-w-0 flex-1">{{ item.title }}</span>
                    <Icon name="lucide:arrow-up-right" class="size-4 shrink-0 text-muted" />
                  </a>
                </li>
              </ul>
            </details>
          </div>
        </StaffSection>
      </div>
    </section>

    <!-- QR kod va Ulashish — kartalar ostida, karuseldan yuqorida -->
    <div class="mx-auto flex max-w-7xl flex-wrap justify-center gap-3.5 px-4 pt-12 sm:px-6 lg:px-8">
      <button
        v-for="action in bottomActions"
        :key="action.key"
        type="button"
        aria-haspopup="dialog"
        class="flex h-14 min-w-44 items-center justify-center gap-2.5 rounded-[18px] border border-line bg-white px-7 font-bold text-ink shadow-[0_10px_30px_-22px_rgba(19,17,47,0.4)] transition duration-200 hover:-translate-y-0.5 hover:border-accent-500 sm:min-w-50"
        @click="action.open"
      >
        <Icon :name="action.icon" class="size-5" />
        {{ t(`staff.profile.${action.key}`) }}
      </button>
    </div>

    <div class="pt-6 pb-20 sm:pb-24">
      <StaffCarousel :slides="home?.slides ?? []" />
    </div>

    <!-- Bog'lanish -->
    <AppDialog v-model:open="contactOpen" :title="t('staff.profile.connect')" sheet class="max-w-[420px]">
      <div class="mt-4 grid gap-2">
        <a
          v-for="o in connectOptions"
          :key="o.key"
          :href="o.href"
          :target="o.external ? '_blank' : undefined"
          :rel="o.external ? 'noopener' : undefined"
          :class="optionClass"
        >
          <span class="grid size-10 shrink-0 place-items-center rounded-xl text-white" :class="o.tile"><Icon :name="o.icon" class="size-5" /></span>
          {{ o.label }}
        </a>
      </div>
      <button type="button" class="mt-3.5 flex h-12 w-full items-center justify-center rounded-[14px] bg-[#f2f0ea] text-[15px] font-semibold text-ink transition-colors hover:bg-line" @click="contactOpen = false">
        {{ t('staff.profile.close') }}
      </button>
    </AppDialog>

    <StaffQrShare v-model:qr="qrOpen" v-model:share="shareOpen" :person="person" :url="pageUrl" />
  </div>
</template>
