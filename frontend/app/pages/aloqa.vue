<script setup lang="ts">
import type { ContactPage } from '#shared/types/api'

// Aloqa va Virtual qabulxona (canvas: "Aloqa va Virtual qabulxona")
const { t, locale } = useI18n()

const { data } = await useFetch<ContactPage>('/api/contact', { key: 'contact', query: { lang: locale } })

// Telefonlar ma'lumotnomasi: qidiruv (F.I.Sh., lavozim, ichki raqam, telefon); bo'lim sarlavhasi shu bo'limda topilgan qator bo'lsa ko'rinadi
const phoneQuery = ref('')
const fold = (v: string) => v.toLowerCase().replace(/[‘’ʻʼ`']/g, '')
const phoneRows = computed(() => {
  const rows = data.value?.phones ?? []
  const q = fold(phoneQuery.value.trim())
  let n = 0
  const numbered = rows.map(r => ({ ...r, n: r.section ? 0 : ++n }))
  if (!q) return numbered
  const out: typeof numbered = []
  let header: (typeof numbered)[number] | null = null
  for (const r of numbered) {
    if (r.section) { header = r; continue }
    if (fold(`${r.name ?? ''} ${r.position} ${r.ext ?? ''} ${r.phone ?? ''}`).includes(q)) {
      if (header) { out.push(header); header = null }
      out.push(r)
    }
  }
  return out
})

// Sahifalarga bo'lish: ~5 sahifa, bo'lim o'rtadan bo'linmaydi; faqat jadval almashadi
const phonePage = ref(0)
const phonePages = computed(() => {
  const rows = phoneRows.value
  const size = Math.max(12, Math.ceil(rows.length / 5))
  const pages: (typeof rows)[] = []
  let cur: typeof rows = []
  for (const r of rows) {
    if (r.section && cur.length >= size) { pages.push(cur); cur = [] }
    cur.push(r)
  }
  if (cur.length) pages.push(cur)
  return pages
})
const phoneTable = ref<HTMLElement>()
function goPhonePage(i: number) {
  phonePage.value = i
  if ((phoneTable.value?.getBoundingClientRect().top ?? 0) < 80) phoneTable.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
watch(phoneQuery, () => { phonePage.value = 0 })

// E-poçta kartalari: asosiy manzil + qöşimça qatorlar (admin → Aloqa → E-poçtalar, «har qatorda bittadan»).
// Qator «Izoh: manzil@domen» körinişida bölsa izoh manzil ustida yoziladi; har bir manzil — alohida mailto havola.
const EMAIL = /[\w.+-]+@[\w-]+(?:\.[\w-]+)+/
const emailCards = computed(() => (data.value?.emails ?? []).map(e => ({
  title: e.title,
  items: [
    { email: e.value, label: null as string | null, main: true },
    ...e.extra.flatMap((line) => {
      const m = EMAIL.exec(line)
      if (!m) return []
      const label = line.slice(0, m.index).replace(/[\s:：—–-]+$/, '').trim()
      return [{ email: m[0], label: label || null, main: false }]
    }),
  ],
})))

const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`

useSeo({ title: () => t('contact.title'), description: () => t('contact.lead') })
</script>

<template>
  <div v-if="data">
    <PageIntro :crumbs="[{ label: t('nav.contact') }]" :title="t('contact.title')" :lead="t('contact.lead')" />

    <section class="mx-auto max-w-7xl px-4 pt-9 sm:px-6 lg:px-8">
      <!-- Çapda: işonç telefoni va Telegram ustma-ust, ong tomonda — e-poçta kartalari (manzillar uzun, keng joy kerak) -->
      <div v-reveal class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div class="grid gap-4 sm:col-span-2 sm:grid-cols-2 lg:col-span-1 lg:grid-cols-1">
          <!-- Işonç telefoni: och mint fon, ingiçka tölqin çiziqlar (sahifa boşidagi kabi), orqada katta telefon belgisi -->
          <a :href="tel(data.hotline.phone)" data-reveal-item class="group/hot relative isolate overflow-hidden rounded-3xl border border-[#9fead3] bg-[linear-gradient(120deg,#e9fdf6,#bff3e2)] p-6 text-ink transition duration-300 hover:-translate-y-1 hover:border-accent-500 hover:shadow-[0_30px_60px_-28px_rgb(15_185_143/0.55)] motion-reduce:hover:transform-none">
            <svg class="pointer-events-none absolute inset-0 -z-10 size-full" viewBox="0 0 300 130" preserveAspectRatio="none" aria-hidden="true">
              <path d="M90 112C150 72 205 132 300 82" fill="none" stroke="rgb(15 185 143 / 0.6)" stroke-width="1.6" vector-effect="non-scaling-stroke" />
              <path d="M110 126C170 92 225 142 300 102" fill="none" stroke="rgb(75 58 168 / 0.22)" stroke-width="1.2" vector-effect="non-scaling-stroke" />
              <path d="M140 40C190 10 240 60 300 30" fill="none" stroke="rgb(15 185 143 / 0.25)" stroke-width="1.2" vector-effect="non-scaling-stroke" />
            </svg>
            <Icon name="lucide:phone-call" class="pointer-events-none absolute -right-3 -bottom-4 -z-10 size-28 -rotate-12 text-[#0fb98f]/[0.14] transition-transform duration-500 group-hover/hot:rotate-0" aria-hidden="true" />
            <span class="flex items-center gap-2 text-[13px] font-medium text-[#0b5a43]"><span class="relative flex size-2"><span class="absolute inline-flex size-full animate-ping rounded-full bg-[#0fb98f] opacity-75 motion-reduce:animate-none" /><span class="relative inline-flex size-2 rounded-full bg-[#0fb98f]" /></span>{{ t('contact.hotline') }}</span>
            <span class="mt-2 block font-display text-[28px] font-semibold text-brand-950 tabular-nums">{{ data.hotline.phone }}</span>
            <span v-if="data.hotline.ext" class="mt-1 block text-[13px] font-semibold text-brand-800">{{ t('contact.ext', { ext: data.hotline.ext }) }}</span>
          </a>
          <!-- Telegram: hover'da kanal rangidagi gradient -->
          <a href="https://t.me/UzSWLU" target="_blank" rel="noopener" data-reveal-item class="group/tg relative isolate flex items-center gap-4 overflow-hidden rounded-3xl border border-line bg-white p-6 text-ink transition duration-300 hover:-translate-y-1 hover:border-[#2AABEE]/50 hover:shadow-[0_30px_60px_-30px_rgb(42_171_238/0.6)] motion-reduce:hover:transform-none">
            <span class="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(120deg,rgb(42_171_238/0.10),transparent_60%)] opacity-0 transition-opacity duration-500 group-hover/tg:opacity-100" aria-hidden="true" />
            <span class="grid size-12 shrink-0 place-items-center rounded-2xl bg-[linear-gradient(135deg,#37BBFE,#007DBB)] text-white shadow-[0_10px_24px_-10px_rgb(42_171_238/0.9)] transition-transform duration-300 group-hover/tg:-rotate-6 group-hover/tg:scale-105" aria-hidden="true">
              <Icon name="lucide:send" class="size-5 -translate-x-px translate-y-px" />
            </span>
            <span class="min-w-0">
              <span class="block text-[13px] text-muted">Telegram · {{ t('contact.channel') }}</span>
              <span class="mt-0.5 block text-lg font-semibold">t.me/UzSWLU</span>
            </span>
            <Icon name="lucide:arrow-up-right" class="ml-auto size-5 shrink-0 text-muted transition duration-300 group-hover/tg:translate-x-0.5 group-hover/tg:-translate-y-0.5 group-hover/tg:text-[#2AABEE]" aria-hidden="true" />
          </a>
        </div>
        <!-- E-poçta: har bir manzil bosiladigan havola (poçta ilovasi oçiladi) + nusxa oliş tugmasi.
             Bezak: qaymoq fon, orqada mint, lavanda va şaftoli rangli yumşoq şarlar; ustida yarim şaffof «şişa» panel (hover'da şarlar siljiydi) -->
        <div v-for="(e, i) in emailCards" :key="e.items[0]!.email" data-reveal-item class="group/card relative isolate flex flex-col overflow-hidden rounded-3xl border border-[#ecdfc0] bg-[#f8eed8] p-2.5 transition duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_-28px_rgb(120_95_40/0.45)] motion-reduce:hover:transform-none">
          <span class="pointer-events-none absolute -top-10 -right-10 -z-10 size-44 rounded-full bg-[radial-gradient(circle,#00fcb4,rgb(0_252_180/0)_70%)] transition-transform duration-700 group-hover/card:-translate-x-6 group-hover/card:translate-y-4" aria-hidden="true" />
          <span class="pointer-events-none absolute -bottom-14 -left-10 -z-10 size-48 rounded-full bg-[radial-gradient(circle,#a99cec,rgb(169_156_236/0)_70%)] transition-transform duration-700 group-hover/card:translate-x-6 group-hover/card:-translate-y-3" aria-hidden="true" />
          <span class="pointer-events-none absolute top-1/3 left-1/2 -z-10 size-28 rounded-full bg-[radial-gradient(circle,#ffcf9e,rgb(255_207_158/0)_70%)] transition-transform duration-700 group-hover/card:scale-125" aria-hidden="true" />
          <div class="flex flex-1 flex-col rounded-[20px] border border-white/85 bg-[rgb(255_250_240/0.62)] px-0.5 pb-1 backdrop-blur-xl backdrop-saturate-150">
          <div class="flex items-center gap-3 px-3 pt-4 pb-3">
            <span class="grid size-11 shrink-0 place-items-center rounded-2xl bg-[linear-gradient(135deg,#5b4bb7,#211a5c)] text-accent-400 shadow-[0_10px_24px_-10px_rgb(56_43_133/0.9)] transition-transform duration-300 group-hover/card:-rotate-6" aria-hidden="true">
              <Icon :name="i === 0 ? 'lucide:mail' : 'lucide:globe'" class="size-5" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block font-semibold leading-tight">{{ e.title }}</span>
              <span class="mt-0.5 block text-xs text-muted tabular-nums">{{ t('contact.mail.count', { n: e.items.length }) }}</span>
            </span>
          </div>
          <ul class="grid gap-0.5 border-t border-[#e3d6b5] pt-2">
            <li v-for="m in e.items" :key="m.email">
              <MailLink :email="m.email" :label="m.label" :strong="m.main" />
            </li>
          </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- Binolar -->
    <section class="mx-auto max-w-7xl px-4 pt-16 sm:px-6 lg:px-8">
      <h2 class="font-display text-4xl font-semibold sm:text-[40px]">{{ t('contact.campuses') }}</h2>
      <CampusCards :campuses="data.campuses" />
    </section>

    <!-- Rahbariyat telefonlari + Virtual qabulxona -->
    <!-- Telefonlar ma'lumotnomasi (admin → Telefonlar); bo'sh bo'lsa — pastda rahbariyat jadvali -->
    <section v-if="data.phones?.length" class="mx-auto max-w-7xl px-4 pt-16 sm:px-6 lg:px-8">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <h2 class="font-display text-[34px] font-semibold">{{ t('contact.phones') }}</h2>
        <label class="flex h-12 w-full items-center gap-2 rounded-full border border-line bg-white px-4 focus-within:border-brand-300 focus-within:ring-4 focus-within:ring-brand-100 sm:w-[340px]">
          <Icon name="lucide:search" class="text-lg text-muted" />
          <span class="sr-only">{{ t('contact.phonesSearch') }}</span>
          <input v-model="phoneQuery" type="search" autocomplete="off" :placeholder="t('contact.phonesSearch')" class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-muted">
        </label>
      </div>
      <div ref="phoneTable" class="mt-5 scroll-mt-28 overflow-x-auto rounded-[22px] border border-line bg-white shadow-[0_24px_48px_-36px_rgb(56_43_133/0.4)]">
        <table class="w-full min-w-[640px] border-collapse text-[17px]">
          <thead>
            <tr class="bg-brand-50 text-left text-[15px] text-brand-800">
              <th scope="col" class="w-16 border-b border-line px-[18px] py-4 font-bold">{{ t('contact.table.no') }}</th>
              <th scope="col" class="border-b border-line px-[18px] py-4 font-bold">{{ t('contact.table.name') }}</th>
              <th scope="col" class="border-b border-line px-[18px] py-4 font-bold">{{ t('contact.table.ext') }}</th>
              <th scope="col" class="border-b border-line px-[18px] py-4 font-bold">{{ t('contact.table.phone') }}</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(r, i) in phonePages[phonePage] ?? []" :key="`${phonePage}-${i}`">
              <tr v-if="r.section">
                <th scope="colgroup" colspan="4" class="border-b border-line bg-[linear-gradient(90deg,var(--color-brand-50),#fff)] px-[18px] pt-5 pb-2.5 text-left text-[15px] font-semibold tracking-wide text-brand-700">{{ r.position }}</th>
              </tr>
              <tr v-else class="border-b border-line/60 transition-colors last:border-0 hover:bg-brand-50/40">
                <td class="px-[18px] py-3 text-muted tabular-nums">{{ r.n }}</td>
                <td class="px-[18px] py-3"><span v-if="r.name" class="block font-semibold">{{ r.name }}</span><span class="block" :class="r.name ? 'mt-0.5 text-[15px] text-muted' : 'font-medium'">{{ r.position }}</span></td>
                <td class="px-[18px] py-3 text-lg font-semibold tabular-nums">{{ r.ext }}</td>
                <td class="px-[18px] py-3 text-lg whitespace-nowrap tabular-nums"><a v-if="r.phone" :href="tel(r.phone)" class="hover:text-brand-700">{{ r.phone }}</a></td>
              </tr>
            </template>
            <tr v-if="!phoneRows.length"><td colspan="4" class="px-[18px] py-8 text-center text-muted">{{ t('contact.phonesEmpty') }}</td></tr>
          </tbody>
        </table>
      </div>
      <nav v-if="phonePages.length > 1" class="mt-4 flex flex-wrap items-center justify-center gap-2" :aria-label="t('contact.phones')">
        <button type="button" class="grid size-11 place-items-center rounded-full border border-line bg-white text-lg transition hover:border-brand-300 disabled:opacity-40" :disabled="phonePage === 0" :aria-label="t('contact.prev')" @click="goPhonePage(phonePage - 1)"><Icon name="lucide:chevron-left" /></button>
        <button
          v-for="(_, i) in phonePages"
          :key="i"
          type="button"
          class="size-11 rounded-full border text-base font-semibold tabular-nums transition"
          :class="i === phonePage ? 'border-brand-800 bg-brand-800 text-white' : 'border-line bg-white hover:border-brand-300'"
          :aria-current="i === phonePage ? 'page' : undefined"
          @click="goPhonePage(i)"
        >{{ i + 1 }}</button>
        <button type="button" class="grid size-11 place-items-center rounded-full border border-line bg-white text-lg transition hover:border-brand-300 disabled:opacity-40" :disabled="phonePage === phonePages.length - 1" :aria-label="t('contact.next')" @click="goPhonePage(phonePage + 1)"><Icon name="lucide:chevron-right" /></button>
      </nav>
    </section>

    <section v-reveal class="mx-auto grid max-w-7xl items-start gap-7 px-4 pt-16 pb-24 sm:px-6 lg:px-8" :class="!data.phones?.length && 'lg:grid-cols-[1.1fr_1fr]'">
      <div v-if="!data.phones?.length" data-reveal-item class="min-w-0">
        <h2 class="font-display text-[34px] font-semibold">{{ t('contact.leaders') }}</h2>
        <div class="mt-5 overflow-x-auto rounded-[22px] border border-line bg-white">
          <table class="w-full min-w-[520px] border-collapse text-sm">
            <thead>
              <tr class="text-left text-xs text-muted">
                <th scope="col" class="border-b border-line px-[18px] py-4 font-bold">{{ t('contact.table.name') }}</th>
                <th scope="col" class="border-b border-line px-[18px] py-4 font-bold">{{ t('contact.table.ext') }}</th>
                <th scope="col" class="border-b border-line px-[18px] py-4 font-bold">{{ t('contact.table.phone') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in data.leaders" :key="l.name" class="border-b border-line/60 last:border-0">
                <td class="px-[18px] py-3.5"><span class="block font-semibold">{{ l.name }}</span><span class="mt-0.5 block text-muted">{{ l.role }}</span></td>
                <td class="px-[18px] py-3.5 font-semibold">{{ l.ext }}</td>
                <td class="px-[18px] py-3.5 whitespace-nowrap"><a :href="tel(l.phone)" class="hover:text-brand-700">{{ l.phone }}</a></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 text-[13px] text-muted">{{ t('contact.reception', { phone: data.reception }) }}</p>
      </div>

      <AppealForm data-reveal-item :recipients="data.recipients" :rude-words="data.rudeWords" />
    </section>
    <SectionNav />
  </div>
</template>
