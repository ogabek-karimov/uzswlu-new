<script setup lang="ts">
import { computed } from 'vue'
import type { Action } from '@/lib/api'
import { ACTIONS, SECTIONS } from '@/lib/roles'

// Ruxsatlar jadvali: har bo'lim × amal (ko'rish / qo'shish / tahrirlash / o'chirish). Yozish amali belgilansa — ko'rish ham avtomatik;
// ko'rish olib tashlansa — bo'lim butunlay yopiladi. Qator boshidagi belgi — shu bo'limning hammasi, ustun sarlavhasi — shu amal hamma bo'limda.
// `inherited` — rolga to'plamlardan kelgan amallar (kulrang, o'chirib bo'lmaydi: to'plamni olib tashlash kerak).
const model = defineModel<Record<string, Action[]>>({ required: true })
const props = defineProps<{ disabled?: boolean; inherited?: Record<string, Action[]> }>()
const groups = computed(() => [...new Set(SECTIONS.map(s => s.group))]) // bo'limlar serverdan keladi

const has = (k: string, a: Action) => (model.value[k] ?? []).includes(a)
const fromSet = (k: string, a: Action) => !has(k, a) && (props.inherited?.[k] ?? []).includes(a)
function set(k: string, acts: Action[]) {
  const next = { ...model.value }
  const clean = ACTIONS.map(x => x.key).filter(x => acts.includes(x))
  if (clean.some(x => x !== 'read') && !clean.includes('read')) clean.unshift('read')
  if (clean.length) next[k] = clean
  else delete next[k]
  model.value = next
}
function toggle(k: string, a: Action) {
  if (props.disabled) return
  const cur = model.value[k] ?? []
  if (has(k, a)) set(k, a === 'read' ? [] : cur.filter(x => x !== a)) // ko'rishsiz qolgan bo'lim — yopiladi
  else set(k, [...cur, a])
}
const allRow = (k: string) => ACTIONS.every(a => has(k, a.key))
function toggleRow(k: string) {
  if (!props.disabled) set(k, allRow(k) ? [] : ACTIONS.map(a => a.key))
}
const allCol = (a: Action) => SECTIONS.every(s => has(s.key, a))
function toggleCol(a: Action) {
  if (props.disabled) return
  const on = !allCol(a)
  for (const s of SECTIONS) {
    const cur = model.value[s.key] ?? []
    set(s.key, on ? [...cur, a] : (a === 'read' ? [] : cur.filter(x => x !== a)))
  }
}
const total = computed(() => Object.keys(model.value).length)
</script>

<template>
  <div class="overflow-x-auto rounded-2xl border border-line">
    <table class="w-full min-w-[560px] border-collapse text-sm">
      <thead>
        <tr class="bg-[#FAF9FD] text-xs text-muted">
          <th class="px-3.5 py-2.5 text-left font-semibold">Bölim <span class="font-normal text-subtle">· {{ total }} ta</span></th>
          <th v-for="a in ACTIONS" :key="a.key" class="w-[92px] px-1 py-2.5 text-center font-semibold">
            <button type="button" class="rounded-lg px-2 py-1 hover:bg-brand-50 hover:text-brand-700 disabled:hover:bg-transparent" :disabled="disabled" :title="`${a.label}: hamma bölimda yoqiş/öçiriş`" @click="toggleCol(a.key)">{{ a.label }}</button>
          </th>
        </tr>
      </thead>
      <tbody>
        <template v-for="g in groups" :key="g">
          <tr><td :colspan="ACTIONS.length + 1" class="bg-white px-3.5 pt-3 pb-1 text-[11px] font-bold tracking-[0.14em] text-muted uppercase">{{ g }}</td></tr>
          <tr v-for="s in SECTIONS.filter(x => x.group === g)" :key="s.key" class="border-t border-[#F0EEF6] hover:bg-[#FBFAFE]">
            <td class="px-3.5 py-2">
              <label class="flex cursor-pointer items-center gap-2.5 font-medium" :class="disabled && 'cursor-default'">
                <input type="checkbox" class="size-4 accent-brand-800" :checked="allRow(s.key)" :disabled="disabled" :aria-label="`${s.label}: hammasi`" @change="toggleRow(s.key)">
                {{ s.label }}
              </label>
            </td>
            <td v-for="a in ACTIONS" :key="a.key" class="px-1 py-2 text-center">
              <button
                type="button" role="checkbox" :aria-checked="has(s.key, a.key)" :aria-label="`${s.label} — ${a.label}`" :disabled="disabled"
                class="mx-auto grid size-8 place-items-center rounded-lg border text-[13px] font-bold transition-colors"
                :class="has(s.key, a.key) ? 'border-brand-700 bg-brand-700 text-white' : fromSet(s.key, a.key) ? 'border-dashed border-brand-300 bg-brand-50 text-brand-400' : 'border-field bg-white text-transparent hover:border-brand-700'"
                :title="fromSet(s.key, a.key) ? 'Ruxsat töplamidan keladi' : a.label"
                @click="toggle(s.key, a.key)"
              >✓</button>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
