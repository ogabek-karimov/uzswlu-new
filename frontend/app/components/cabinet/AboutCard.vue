<script setup lang="ts">
import type { LocalizedText } from '#shared/types/api'

// "Xodim haqida": ko'rish; tahrirlashda 4 tilda maydonlar, X va "Bekor qilish" — o'zgarish bo'lsa
// saytning o'zidagi tasdiqlash oynasi chiqadi (oldingi saytdagidek)
const props = defineProps<{ about: LocalizedText; text?: string | null; saving?: boolean }>()
const emit = defineEmits<{ save: [about: LocalizedText] }>()

const { t } = useI18n()
const LANGS = ['uz', 'ru', 'en', 'zh'] as const

const editing = ref(false)
const draft = reactive<LocalizedText>({ uz: '', ru: '', en: '', zh: '' })
const confirmOpen = ref(false)

function start() {
  Object.assign(draft, props.about)
  editing.value = true
}
const dirty = computed(() => LANGS.some(l => draft[l] !== props.about[l]))
function tryClose() {
  if (dirty.value) confirmOpen.value = true
  else editing.value = false
}
function save() {
  emit('save', { uz: draft.uz.trim(), ru: draft.ru.trim(), en: draft.en.trim(), zh: draft.zh.trim() })
}
// Saqlangan qiymat qaytgach tahrir yopiladi (boshqa sabab bilan yangilanishda — masalan, rasm almashganda — qoralama saqlanib qoladi)
watch(() => props.about, (saved) => {
  if (editing.value && LANGS.every(l => saved[l] === draft[l].trim())) editing.value = false
}, { deep: true })
</script>

<template>
  <StaffSection :title="t('staff.profile.about')" :active="editing">
    <template #action>
      <button
        v-if="!editing"
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-sm font-semibold text-brand-700 transition-colors hover:bg-brand-50"
        @click="start"
      >
        <Icon :name="text ? 'lucide:square-pen' : 'lucide:plus'" class="size-4" />
        {{ text ? t('cabinet.edit') : t('cabinet.about.add') }}
      </button>
      <button
        v-else
        type="button"
        :aria-label="t('cabinet.close')"
        class="grid size-9 place-items-center rounded-full bg-[#fdecec] text-[#c62828] transition-colors hover:bg-[#fbd5d5]"
        @click="tryClose"
      >
        <Icon name="lucide:x" class="size-4" />
      </button>
    </template>

    <p class="mt-3.5 text-[17px] leading-relaxed" :class="text ? 'text-ink' : 'text-muted'">{{ text || t('cabinet.about.placeholder') }}</p>

    <form v-if="editing" class="mt-5 border-t border-line pt-5" @submit.prevent="save">
      <label v-for="l in LANGS" :key="l" class="mt-3.5 block text-[13px] text-muted first:mt-0">
        {{ t('cabinet.about.field', { lang: t(`cabinet.langs.${l}`) }) }}
        <textarea
          v-model="draft[l]"
          rows="3"
          maxlength="2000"
          :lang="l === 'zh' ? 'zh' : l"
          :placeholder="t('cabinet.about.placeholder')"
          class="mt-1.5 block w-full resize-y rounded-2xl border border-line bg-white px-3.5 py-3 text-[15px] text-ink outline-none focus:border-accent-600 focus:ring-4 focus:ring-accent-600/15"
        />
      </label>
      <div class="mt-4 flex flex-wrap gap-2.5">
        <button type="submit" :disabled="saving" class="flex h-12 items-center gap-2 rounded-[14px] bg-accent-400 px-6 font-bold text-ink transition-colors hover:bg-accent-300 disabled:opacity-60">
          <Icon v-if="saving" name="lucide:loader-circle" class="size-4 animate-spin" />
          {{ t('cabinet.save') }}
        </button>
        <button type="button" class="h-12 rounded-[14px] border border-line bg-white px-6 font-semibold text-ink transition-colors hover:border-accent-500" @click="tryClose">
          {{ t('cabinet.cancel') }}
        </button>
      </div>
    </form>

    <AppConfirm
      v-model:open="confirmOpen"
      :title="t('cabinet.discard.title')"
      :text="t('cabinet.discard.text')"
      :confirm-label="t('cabinet.discard.yes')"
      :cancel-label="t('cabinet.discard.no')"
      danger
      @confirm="editing = false"
    />
  </StaffSection>
</template>
