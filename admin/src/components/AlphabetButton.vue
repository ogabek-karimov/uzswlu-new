<script setup lang="ts">
import { computed, ref } from 'vue'
import { convertUzDeep, toNewAlphabet } from '@/lib/alphabet'

// «Yangi alifboga ögiriş»: formadagi barcha özbekça (uz) maydonlarni Oʻ→Ö, Gʻ→Ğ, Sh→Ş, Ch→Ç qiladi.
// Teglar, havolalar, xorijiy sözlar (Dashboard…) tegilmaydi. Natija saqlanmaguncha bazaga yozilmaydi.
const props = defineProps<{ target: object }>()
const result = ref('')

const pending = computed(() => {
  let n = 0
  const walk = (v: unknown) => {
    if (Array.isArray(v)) return v.forEach(walk)
    if (!v || typeof v !== 'object') return
    for (const [k, x] of Object.entries(v)) {
      if (k === 'uz' && typeof x === 'string') { if (toNewAlphabet(x) !== x) n++ }
      else walk(x)
    }
  }
  walk(props.target)
  return n
})

function run() {
  const n = convertUzDeep(props.target)
  result.value = n ? `${n} ta maydon yangi alifboga ögirildi — saqlaşni unutmang` : 'Hammasi allaqaçon yangi alifboda'
  setTimeout(() => (result.value = ''), 5000)
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2.5">
    <button
      type="button"
      class="inline-flex h-9 items-center gap-2 rounded-full border px-3.5 text-[13px] font-semibold transition-colors"
      :class="pending ? 'border-brand-700 bg-brand-700 text-white hover:bg-brand-800' : 'border-field bg-white text-muted'"
      title="Oʻ→Ö, Gʻ→Ğ, Sh→Ş, Ch→Ç — barça özbekça maydonlarda (sarlavha, tavsif, matn…)"
      @click="run"
    >
      <span class="font-bold">Ö</span> Yangi alifboga ögiriş<template v-if="pending"> ({{ pending }})</template>
    </button>
    <span v-if="result" role="status" class="text-[13px] font-semibold text-[#0B5A43]">{{ result }}</span>
  </div>
</template>
