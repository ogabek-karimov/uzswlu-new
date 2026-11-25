<script setup lang="ts">
// E-poçta manzili: bosilsa pochta ilovasi oçiladi (mailto), yonidagi tugma — manzilni nusxalaydi.
// Aloqa sahifasidagi e-poçta kartalari va bino kartalarida ishlatiladi.
const props = defineProps<{ email: string; label?: string | null; strong?: boolean }>()

const { t } = useI18n()
const local = computed(() => props.email.slice(0, props.email.lastIndexOf('@')))
const domain = computed(() => props.email.slice(props.email.lastIndexOf('@') + 1))
const copied = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined
async function copy() {
  let ok = false
  try {
    await navigator.clipboard.writeText(props.email)
    ok = true
  }
  catch {
    // Clipboard API yöq yoki ruxsat berilmadi (eski brauzer, http) — yaşirin maydon orqali nusxalaymiz
    const area = Object.assign(document.createElement('textarea'), { value: props.email, readOnly: true })
    area.style.cssText = 'position:fixed;opacity:0;pointer-events:none'
    document.body.append(area)
    area.select()
    ok = document.execCommand('copy')
    area.remove()
  }
  if (!ok) return
  copied.value = true
  clearTimeout(timer)
  timer = setTimeout(() => { copied.value = false }, 1800)
}
onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <div class="group/mail flex items-center gap-2 rounded-2xl px-3 py-2 transition-colors hover:bg-brand-50/80">
    <span class="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700 transition duration-300 group-hover/mail:bg-brand-800 group-hover/mail:text-accent-400" aria-hidden="true">
      <Icon name="lucide:mail" class="size-[18px]" />
    </span>
    <a :href="`mailto:${email}`" class="min-w-0 flex-1 leading-tight" :title="t('contact.mail.write', { email })">
      <span v-if="label" class="block text-xs font-medium text-muted">{{ label }}</span>
      <span class="block [overflow-wrap:anywhere] transition-colors group-hover/mail:text-brand-700" :class="strong ? 'text-[17px] font-semibold' : 'text-[15px] font-medium'">{{ local }}@<wbr>{{ domain }}</span>
    </a>
    <Icon name="lucide:arrow-up-right" class="size-4 shrink-0 -translate-x-1 text-brand-700 opacity-0 transition duration-300 group-hover/mail:translate-x-0 group-hover/mail:opacity-100" aria-hidden="true" />
    <button
      type="button"
      class="grid size-8 shrink-0 place-items-center rounded-lg opacity-60 transition hover:bg-white hover:opacity-100 focus-visible:opacity-100 group-hover/mail:opacity-100"
      :class="copied && 'text-brand-700'"
      :aria-label="copied ? t('contact.mail.copied') : t('contact.mail.copy', { email })"
      :title="copied ? t('contact.mail.copied') : t('contact.mail.copy', { email })"
      @click="copy"
    >
      <Icon :name="copied ? 'lucide:check' : 'lucide:copy'" class="size-4" />
    </button>
    <span class="sr-only" aria-live="polite">{{ copied ? t('contact.mail.copied') : '' }}</span>
  </div>
</template>
