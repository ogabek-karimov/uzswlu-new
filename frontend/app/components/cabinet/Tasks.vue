<script setup lang="ts">
import type { CabinetTask, CabinetTasks } from '#shared/types/api'

// Xodim vazifalari: menga berilgan / men bergan. Dekan kafedra mudirlariga, kafedra mudiri xodimlariga topshiriq beradi
// (kimga — backend HEMIS lavozimidan aniqlaydi); hamma o'ziga ham vazifa yozishi mumkin.
const { t } = useI18n()
const { data, refresh } = await useFetch<CabinetTasks>('/api/me/tasks', { key: 'cabinet-tasks', default: () => ({ mine: [], given: [], assignees: [] }) })

const tab = ref<'mine' | 'given'>('mine')
const adding = ref(false)
const busy = ref(false)
const failed = ref(false)
const form = reactive({ title: '', note: '', due: '', assigneeId: '' })

const canGive = computed(() => (data.value?.assignees.length ?? 0) > 0)
const list = computed(() => data.value?.[tab.value] ?? [])
const openCount = computed(() => (data.value?.mine ?? []).filter(x => x.status === 'open').length)

function reset() {
  Object.assign(form, { title: '', note: '', due: '', assigneeId: '' })
  adding.value = false
  failed.value = false
}

async function run(fn: () => Promise<unknown>) {
  busy.value = true
  failed.value = false
  try {
    await fn()
    await refresh()
    return true
  }
  catch {
    failed.value = true
    return false
  }
  finally {
    busy.value = false
  }
}

async function create() {
  if (!form.title.trim()) return
  const ok = await run(() => $fetch('/api/me/tasks', { method: 'POST', body: { ...form, assigneeId: form.assigneeId || null, due: form.due || null } }))
  if (ok) reset()
}

const toggle = (x: CabinetTask) => run(() => $fetch(`/api/me/tasks/${x.id}`, { method: 'PATCH', body: { status: x.status === 'done' ? 'open' : 'done' } }))
const remove = (x: CabinetTask) => confirm(t('cabinet.tasks.confirm')) && run(() => $fetch(`/api/me/tasks/${x.id}`, { method: 'DELETE' }))
const fmt = (d: string) => new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })
</script>

<template>
  <section class="rounded-[28px] border border-line bg-white p-5 sm:p-6" :aria-label="t('cabinet.tasks.title')">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="flex items-center gap-2.5 font-display text-[28px] font-semibold text-ink">
          {{ t('cabinet.tasks.title') }}
          <span v-if="openCount" class="rounded-full bg-accent-100 px-2.5 py-0.5 font-sans text-sm font-semibold text-accent-600">{{ openCount }}</span>
        </h2>
        <p class="mt-1 text-[15px] text-muted">{{ t('cabinet.tasks.desc') }}</p>
      </div>
      <button v-if="!adding" type="button" class="inline-flex items-center gap-1.5 rounded-full bg-brand-700 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-900" @click="adding = true">
        <Icon name="lucide:plus" class="size-4" />{{ t('cabinet.tasks.add') }}
      </button>
    </div>

    <form v-if="adding" class="mt-4 grid gap-3 rounded-2xl bg-brand-50 p-4" @submit.prevent="create">
      <div class="grid gap-3 sm:grid-cols-2">
        <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.tasks.name') }}
          <input v-model="form.title" required maxlength="200" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
        </label>
        <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.tasks.who') }}
          <select v-model="form.assigneeId" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
            <option value="">{{ t('cabinet.tasks.me') }}</option>
            <option v-for="a in data?.assignees" :key="a.id" :value="a.id">{{ a.name }}<template v-if="a.position"> — {{ a.position }}</template></option>
          </select>
        </label>
      </div>
      <div class="grid gap-3 sm:grid-cols-[1fr_200px]">
        <label class="grid gap-1 text-sm font-medium text-ink">{{ t('cabinet.tasks.note') }}
          <textarea v-model="form.note" rows="2" maxlength="2000" class="rounded-xl border border-line bg-white px-3 py-2 font-normal" />
        </label>
        <label class="grid gap-1 self-start text-sm font-medium text-ink">{{ t('cabinet.tasks.due') }}
          <input v-model="form.due" type="date" class="h-11 rounded-xl border border-line bg-white px-3 font-normal">
        </label>
      </div>
      <div class="flex justify-end gap-2">
        <button type="button" class="rounded-full px-4 py-2 text-sm font-semibold text-muted hover:bg-white" @click="reset">{{ t('cabinet.tasks.cancel') }}</button>
        <button type="submit" :disabled="busy" class="rounded-full bg-brand-700 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-900 disabled:opacity-60">{{ t('cabinet.tasks.save') }}</button>
      </div>
    </form>

    <p v-if="failed" role="alert" class="mt-3 rounded-xl bg-[#fdecec] px-4 py-2.5 text-sm text-[#8e1b1b]">{{ t('cabinet.tasks.error') }}</p>

    <div v-if="canGive" role="tablist" class="mt-4 inline-flex rounded-full bg-brand-50 p-1">
      <button v-for="k in (['mine', 'given'] as const)" :key="k" type="button" role="tab" :aria-selected="tab === k"
              class="rounded-full px-4 py-1.5 text-sm font-semibold transition-colors" :class="tab === k ? 'bg-white text-brand-900 shadow-sm' : 'text-muted'" @click="tab = k">
        {{ t(`cabinet.tasks.${k}`) }}
      </button>
    </div>

    <ul v-if="list.length" class="mt-4 grid gap-2">
      <li v-for="x in list" :key="x.id" class="flex items-start gap-3 rounded-2xl border border-line px-4 py-3" :class="x.status === 'done' ? 'bg-brand-50/60' : ''">
        <button v-if="tab === 'mine'" type="button" :aria-label="x.status === 'done' ? t('cabinet.tasks.reopen') : t('cabinet.tasks.done')" :disabled="busy"
                class="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full border-2 transition-colors" :class="x.status === 'done' ? 'border-brand-700 bg-brand-700 text-white' : 'border-line hover:border-brand-700'" @click="toggle(x)">
          <Icon v-if="x.status === 'done'" name="lucide:check" class="size-3.5" />
        </button>
        <Icon v-else :name="x.status === 'done' ? 'lucide:circle-check' : 'lucide:circle-dashed'" class="mt-0.5 size-6 shrink-0 text-brand-600" />
        <div class="min-w-0 flex-1">
          <p class="font-medium text-ink" :class="x.status === 'done' ? 'text-muted line-through' : ''">{{ x.title }}</p>
          <p v-if="x.note" class="mt-0.5 text-sm text-muted">{{ x.note }}</p>
          <p class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted">
            <span v-if="tab === 'mine' && !x.self">{{ t('cabinet.tasks.from') }}: {{ x.authorName }}</span>
            <span v-if="tab === 'given'">{{ t('cabinet.tasks.to') }}: {{ x.assigneeName }}</span>
            <span v-if="x.due" :class="x.overdue ? 'font-semibold text-[#b42318]' : ''">{{ t('cabinet.tasks.until') }}: {{ fmt(x.due) }}<template v-if="x.overdue"> · {{ t('cabinet.tasks.overdue') }}</template></span>
          </p>
        </div>
        <button v-if="tab === 'given' || x.self" type="button" :aria-label="t('cabinet.tasks.remove')" :disabled="busy"
                class="grid size-8 shrink-0 place-items-center rounded-full text-muted transition-colors hover:bg-brand-50 hover:text-[#b42318]" @click="remove(x)">
          <Icon name="lucide:trash-2" class="size-4" />
        </button>
      </li>
    </ul>
    <p v-else class="mt-4 text-sm text-muted">{{ t(tab === 'mine' ? 'cabinet.tasks.empty' : 'cabinet.tasks.emptyGiven') }}</p>
  </section>
</template>
