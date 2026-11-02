<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import { api } from '@/lib/api'
import { auth } from '@/lib/auth'
import { POST_TYPES, SDG_COLORS, SDG_NAMES } from '@/lib/constants'
import { dateTime, relative } from '@/lib/format'
import { postState, STATE_BADGE } from '@/lib/posts'

type Overview = {
  posts: { month: { news: number; announcements: number; events: number }; drafts: number; scheduled: number; hidden: number; total: number }
  recent: { id: number; type: 'news' | 'announcements' | 'events'; title: string; sdg: number; status: 'draft' | 'published'; hidden: boolean; publishedAt: string | null; author: string | null }[]
  logins?: { today: number; failed24h: number }
  activity?: { id: number; who: string; action: string; label: string; at: string }[]
}

const data = ref<Overview | null>(null)
const error = ref('')
const typeLabel = (t: string) => POST_TYPES.find(p => p.value === t)?.label ?? t
const ACTIONS: Record<string, string> = { create: 'yaratdi', edit: 'tahrirladi', publish: 'naşr qildi', hide: 'yaşirdi', show: 'qayta körsatdi', delete: 'savatga taşladi', restore: 'qaytardi', role: 'rol berdi', settings: 'sozlamalarni saqladi' }

const hour = new Date().getHours()
const greeting = hour < 11 ? 'Xayrli tong' : hour < 18 ? 'Xayrli kun' : 'Xayrli keç'

onMounted(async () => {
  try { data.value = await api.get<Overview>('/panel/overview') }
  catch { error.value = 'Ma’lumotlarni yuklab bölmadi.' }
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[30px] font-bold tracking-tight">{{ greeting }}, {{ auth.user.value?.name }}</h1>
        <p class="mt-1.5 flex items-center gap-2 text-[15px] text-muted"><span class="size-2 rounded-full bg-[#12B76A] shadow-[0_0_0_4px_rgba(18,183,106,0.15)]" />Sayt barqaror işlayapti</p>
      </div>
      <div class="flex flex-wrap gap-2.5">
        <RouterLink v-for="t in POST_TYPES" :key="t.value" :to="`/postlar/${t.value}/yangi`" class="btn-ghost h-11">
          <span class="grid size-6 place-items-center rounded-lg bg-brand-100 font-bold text-brand-700">+</span>{{ t.label }}
        </RouterLink>
      </div>
    </div>

    <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{{ error }}</p>

    <div v-if="data" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div class="card border-night! bg-night! p-5 text-white">
        <p class="text-[13px] text-white/60">Şu oy naşr qilingan</p>
        <p class="mt-2.5 text-4xl leading-none font-bold">{{ data.posts.month.news + data.posts.month.announcements + data.posts.month.events }}</p>
        <p class="mt-2 text-[13px] text-white/60">{{ data.posts.month.news }} yangilik · {{ data.posts.month.announcements }} e’lon · {{ data.posts.month.events }} tadbir</p>
      </div>
      <div class="card p-5">
        <p class="text-[13px] text-muted">Qoralama va rejada</p>
        <p class="mt-2.5 text-4xl leading-none font-bold">{{ data.posts.drafts + data.posts.scheduled }}</p>
        <p class="mt-2 text-[13px] text-muted">{{ data.posts.drafts }} qoralama · {{ data.posts.scheduled }} rejalaştirilgan</p>
      </div>
      <div class="card p-5">
        <p class="text-[13px] text-muted">Saytdan yaşirilgan</p>
        <p class="mt-2.5 text-4xl leading-none font-bold">{{ data.posts.hidden }}</p>
        <p class="mt-2 text-[13px] text-muted">jami {{ data.posts.total }} ta post</p>
      </div>
      <div v-if="data.logins" class="card p-5">
        <p class="text-[13px] text-muted">Bugungi kirişlar</p>
        <p class="mt-2.5 flex items-baseline gap-2.5"><span class="text-4xl leading-none font-bold">{{ data.logins.today }}</span>
          <span v-if="data.logins.failed24h" class="chip bg-red-50 text-red-700">{{ data.logins.failed24h }} xato uriniş</span></p>
        <RouterLink to="/kirish-tarixi" class="mt-2 inline-block text-[13px] font-semibold text-brand-700">Kiriş tarixi →</RouterLink>
      </div>
    </div>

    <section v-if="data" class="card overflow-hidden">
      <div class="flex flex-wrap items-center justify-between gap-3 px-5 py-5">
        <div>
          <h2 class="text-[17px] font-bold">Sönggi postlar</h2>
          <p class="mt-1 text-[13px] text-muted">Yangiliklar, e’lonlar va tadbirlar — kim, qaçon joylagani bilan</p>
        </div>
        <RouterLink to="/postlar/news" class="text-sm font-semibold text-brand-700">Hammasi →</RouterLink>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[860px] border-collapse text-sm">
          <thead>
            <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
              <th class="px-5 py-3 font-semibold">Sarlavha</th>
              <th class="px-3.5 py-3 font-semibold">Turi</th>
              <th class="px-3.5 py-3 font-semibold">BRM</th>
              <th class="px-3.5 py-3 font-semibold">Muallif</th>
              <th class="px-3.5 py-3 font-semibold">Holati</th>
              <th class="px-5 py-3 font-semibold">Vaqti</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in data.recent" :key="p.id" class="border-t border-[#F0EEF6] hover:bg-[#FAF9FD]">
              <td class="max-w-[420px] px-5 py-3.5"><RouterLink :to="`/postlar/${p.type}/${p.id}`" class="line-clamp-2 font-semibold">{{ p.title }}</RouterLink></td>
              <td class="px-3.5 py-3.5 whitespace-nowrap text-muted">{{ typeLabel(p.type) }}</td>
              <td class="px-3.5 py-3.5">
                <span v-if="p.sdg" :title="`BRM ${p.sdg} — ${SDG_NAMES[p.sdg - 1]}`" class="grid size-7 place-items-center rounded-lg text-xs font-bold text-white" :style="{ background: SDG_COLORS[p.sdg - 1] }">{{ p.sdg }}</span>
                <span v-else class="text-subtle">—</span>
              </td>
              <td class="px-3.5 py-3.5 whitespace-nowrap">{{ p.author ?? '—' }}</td>
              <td class="px-3.5 py-3.5 whitespace-nowrap">
                <span class="chip" :class="STATE_BADGE[postState(p)].cls">{{ STATE_BADGE[postState(p)].label }}</span>
                <span v-if="p.hidden" class="chip ml-1 bg-[#EEF0F6] text-[#3D4466]">yaşirilgan</span>
              </td>
              <td class="px-5 py-3.5 whitespace-nowrap text-muted tabular-nums">{{ dateTime(p.publishedAt) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="data?.activity" class="card p-5">
      <div class="flex items-baseline justify-between gap-3">
        <h2 class="text-[17px] font-bold">Faollik jurnali</h2>
        <RouterLink to="/faollik" class="text-sm font-semibold text-brand-700">Hammasi →</RouterLink>
      </div>
      <p v-if="!data.activity.length" class="mt-3 text-sm text-muted">Hali heç qanday özgariş yöq.</p>
      <ul class="mt-3.5 flex flex-col gap-3">
        <li v-for="a in data.activity" :key="a.id" class="flex gap-3 text-sm leading-relaxed">
          <span class="grid size-8 shrink-0 place-items-center rounded-full bg-brand-100 text-brand-700"><Icon name="activity" :size="15" /></span>
          <span><b>{{ a.who }}</b> {{ ACTIONS[a.action] ?? a.action }}: {{ a.label }}<span class="block text-xs text-subtle">{{ relative(a.at) }}</span></span>
        </li>
      </ul>
    </section>
  </div>
</template>
