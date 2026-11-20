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

const tel = (phone: string) => `tel:${phone.startsWith('+') ? '' : '+998'}${phone.replace(/[^\d+]/g, '')}`

useSeo({ title: () => t('contact.title'), description: () => t('contact.lead') })
</script>

<template>
  <div v-if="data">
    <PageIntro :crumbs="[{ label: t('nav.contact') }]" :title="t('contact.title')" :lead="t('contact.lead')" />

    <section class="mx-auto max-w-7xl px-4 pt-9 sm:px-6 lg:px-8">
      <div v-reveal class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <a :href="tel(data.hotline.phone)" data-reveal-item class="rounded-3xl bg-brand-900 p-6 text-white transition-colors hover:bg-brand-800">
          <span class="block text-[13px] text-white/60">{{ t('contact.hotline') }}</span>
          <span class="mt-1.5 block font-display text-[28px] font-semibold">{{ data.hotline.phone }}</span>
          <span v-if="data.hotline.ext" class="mt-1 block text-[13px] text-accent-400">{{ t('contact.ext', { ext: data.hotline.ext }) }}</span>
        </a>
        <div v-for="e in data.emails" :key="e.value" data-reveal-item class="rounded-3xl border border-line bg-white p-6">
          <span class="block text-[13px] text-muted">{{ e.title }}</span>
          <a :href="`mailto:${e.value}`" class="mt-1.5 block text-lg font-semibold break-all hover:text-brand-700">{{ e.value }}</a>
          <span v-if="e.extra.length" class="mt-1 block text-[13px] break-all text-muted">{{ e.extra.join(' · ') }}</span>
        </div>
        <a href="https://t.me/UzSWLU" target="_blank" rel="noopener" data-reveal-item class="rounded-3xl border border-line bg-white p-6 text-ink transition-colors hover:border-accent-500">
          <span class="block text-[13px] text-muted">Telegram</span>
          <span class="mt-1.5 block text-lg font-semibold">t.me/UzSWLU</span>
          <span class="mt-1 block text-[13px] text-brand-700">{{ t('contact.channel') }} →</span>
        </a>
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
