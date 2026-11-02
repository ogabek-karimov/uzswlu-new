<script setup lang="ts">
import type { StaffProfile } from '#shared/types/api'

// Chap profil kartasi — Staff sahifasi va xodim kabinetida bir xil (oldingi saytdagi effektlar bilan).
// editablePhoto: kabinetda rasm ustida kamera (kompyuterda hover, telefonda burchak belgisi) va
// o'z rasmi bo'lsa ✕ (HEMIS rasmiga qaytarish). Pastki tugmalar — slot orqali.
const props = defineProps<{ person: StaffProfile; editablePhoto?: boolean; hasOwnPhoto?: boolean; busy?: boolean }>()
const emit = defineEmits<{ photo: [file: File]; removePhoto: [] }>()

const { t } = useI18n()

const names = computed(() => staffName(props.person.name, props.person.patronymic))
const positionText = computed(() => staffRoles(props.person.employments).positions.join(', '))

// Yumaloq ikonkalar: Telegram, WhatsApp (aloqadan) + ijtimoiy tarmoqlar
const quickLinks = computed(() => [
  ...(['telegram', 'whatsapp'] as const).flatMap((type) => {
    const c = props.person.contacts.find(x => x.type === type)
    return c ? [{ key: type, label: t(`staff.contact.${type}`), icon: staffContacts[type].icon, hover: staffContacts[type].hover, href: staffContacts[type].href(c.value) }] : []
  }),
  ...props.person.socials.map(s => ({ key: s.network, label: staffNetworks[s.network].label, icon: staffNetworks[s.network].icon, hover: staffNetworks[s.network].hover, href: s.url })),
])

// Halqa doim sekin aylanadi; kursor kelganda sakrashsiz tezlashadi (2.4×)
const ring = ref<HTMLElement>()
function ringSpeed(rate: number) {
  ring.value?.getAnimations().forEach(a => a.updatePlaybackRate(rate))
}

const fileInput = ref<HTMLInputElement>()
function onFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('photo', file)
  input.value = ''
}
</script>

<template>
  <aside
    class="staff-card relative overflow-hidden rounded-[32px] bg-[linear-gradient(160deg,var(--color-brand-800)_0%,var(--color-brand-900)_60%,var(--color-brand-950)_100%)] px-6 pt-9 pb-7 text-center text-white shadow-[0_10px_30px_rgba(17,12,46,0.25)] sm:px-8"
    @mouseenter="ringSpeed(2.4)"
    @mouseleave="ringSpeed(1)"
  >
    <!-- Universitet belgisi: burchakdagi yarim halqa markazida xira emblema -->
    <span aria-hidden="true" class="decor pointer-events-none absolute -top-[70px] -right-[70px] size-[280px] rounded-full border-[32px] border-accent-400/6" />
    <img src="/logos/mark.webp" alt="" aria-hidden="true" class="decor pointer-events-none absolute top-3.5 right-[26px] w-[88px] opacity-20 select-none">

    <span class="group/ava relative mx-auto block size-44">
      <span ref="ring" aria-hidden="true" class="staff-ring absolute inset-0 rounded-full" />
      <StaffAvatar :id="person.id" :name="names.full" :photo="person.photo" :fallback="person.photoFallback" class="absolute inset-[5px] size-[calc(100%-10px)] rounded-full border-4 border-brand-900 bg-brand-800! text-[56px] text-white/85!" />

      <template v-if="editablePhoto">
        <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" tabindex="-1" @change="onFile">
        <!-- Kompyuterda: kursor kelganda kamera; telefonda: burchakdagi belgi (rasmning o'zi ham bosiladi) -->
        <button
          type="button"
          :disabled="busy"
          class="absolute inset-[5px] grid place-items-center rounded-full bg-brand-950/55 text-white opacity-0 transition-opacity group-hover/ava:opacity-100 focus-visible:opacity-100 pointer-coarse:opacity-0"
          @click="fileInput?.click()"
        >
          <span class="grid justify-items-center gap-1.5 text-xs font-semibold">
            <Icon :name="busy ? 'lucide:loader-circle' : 'lucide:camera'" class="size-7" :class="busy && 'animate-spin'" />
            {{ t('cabinet.photo.change') }}
          </span>
        </button>
        <button
          type="button"
          :aria-label="t('cabinet.photo.change')"
          class="absolute right-2 bottom-2 hidden size-10 place-items-center rounded-full border-[3px] border-brand-900 bg-accent-400 text-ink shadow pointer-coarse:grid"
          @click="fileInput?.click()"
        >
          <Icon name="lucide:camera" class="size-[18px]" />
        </button>
        <button
          v-if="hasOwnPhoto"
          type="button"
          :aria-label="t('cabinet.photo.remove')"
          :title="t('cabinet.photo.remove')"
          class="absolute top-2.5 right-2.5 grid size-8 place-items-center rounded-full border-2 border-brand-900 bg-white text-ink shadow transition hover:bg-[#fdecec] hover:text-[#c62828]"
          @click="emit('removePhoto')"
        >
          <Icon name="lucide:x" class="size-4" />
        </button>
      </template>
    </span>

    <h1 class="relative mt-5 font-display text-3xl leading-tight font-semibold">{{ names.full }}</h1>
    <p class="relative mt-2 text-[15px] text-white/80">{{ positionText }}</p>

    <!-- Xodim haqida: faqat kiritilgan bo'lsa; matn uzun bo'lsa karta cho'ziladi -->
    <p v-if="person.about" class="relative mt-4 rounded-2xl border border-white/20 bg-white/6 px-4 py-3 text-sm leading-relaxed text-white/90">
      {{ person.about }}
    </p>

    <ul v-if="quickLinks.length" :aria-label="t('staff.profile.socials')" class="relative z-10 mt-5 flex flex-wrap justify-center gap-2.5">
      <li v-for="q in quickLinks" :key="q.key" class="group/q relative">
        <a
          :href="q.href"
          target="_blank"
          rel="noopener"
          class="grid size-11 place-items-center rounded-full bg-white/10 text-white transition duration-200 hover:-translate-y-[3px] hover:scale-110 hover:shadow-[0_8px_18px_rgba(0,0,0,0.3)] focus-visible:-translate-y-[3px]"
          :class="q.hover"
        >
          <Icon :name="q.icon" class="size-[18px]" />
          <span class="sr-only">{{ q.label }} ({{ t('staff.profile.newTab') }})</span>
        </a>
        <!-- Nomi: kursor kelganda ostida chiqadi (tugmalar ustida qoladi) -->
        <span aria-hidden="true" class="pointer-events-none absolute top-[calc(100%+8px)] left-1/2 z-10 -translate-x-1/2 -translate-y-1 rounded-md bg-white px-2 py-1 text-[11px] leading-none font-semibold whitespace-nowrap text-ink opacity-0 transition duration-200 group-hover/q:translate-y-0 group-hover/q:opacity-100">
          {{ q.label }}
        </span>
      </li>
    </ul>

    <div class="relative">
      <slot />
    </div>
  </aside>
</template>
