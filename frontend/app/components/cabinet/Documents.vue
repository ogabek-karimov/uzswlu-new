<script setup lang="ts">
import type { CabinetDocSection, StaffCabinet, StaffDocSection } from '#shared/types/api'

// "Hujjatlarim": 5 ta karta (oldingi saytdagidek) — rangli ikonka, soni, Staff'da ko'rinishi (CV, Kitoblar, Maqolalar;
// boshida ochiq), Taqdimotlar va Videolar — faqat dashboard'da; pastida "Hujjat yuklash" (oyna ochiladi)
defineProps<{ documents: StaffCabinet['documents'] }>()
const emit = defineEmits<{ toggle: [section: StaffDocSection, visible: boolean]; open: [section: CabinetDocSection] }>()

const { t } = useI18n()

const SECTIONS: { key: CabinetDocSection; icon: string; color: string; soft: string; toggleable: boolean }[] = [
  { key: 'cv', icon: 'lucide:file-user', color: '#d64545', soft: 'rgb(214 69 69 / 0.08)', toggleable: true },
  { key: 'books', icon: 'lucide:book-open', color: '#2f6fd6', soft: 'rgb(47 111 214 / 0.08)', toggleable: true },
  { key: 'presentations', icon: 'lucide:presentation', color: '#e07a1f', soft: 'rgb(224 122 31 / 0.1)', toggleable: false },
  { key: 'articles', icon: 'lucide:newspaper', color: '#1f9d66', soft: 'rgb(31 157 102 / 0.1)', toggleable: true },
  { key: 'videos', icon: 'lucide:video', color: '#e53935', soft: 'rgb(229 57 53 / 0.08)', toggleable: false },
]
</script>

<template>
  <section>
    <p class="mt-2 flex items-center gap-3.5 text-xs font-bold tracking-[0.18em] text-muted uppercase">
      {{ t('cabinet.docs.title') }}
      <span class="h-px flex-1 bg-line" />
    </p>
    <ul class="mt-4 grid grid-cols-2 gap-3.5 md:grid-cols-3 xl:grid-cols-5">
      <li
        v-for="s in SECTIONS"
        :key="s.key"
        class="group/doc relative flex flex-col overflow-hidden rounded-[22px] border border-t-4 border-line bg-white px-4 pt-4.5 pb-4 transition duration-300 hover:-translate-y-1 hover:scale-[1.03]"
        :style="{ borderTopColor: s.color }"
      >
        <span aria-hidden="true" class="pointer-events-none absolute -top-10 -right-10 size-28 rounded-full" :style="{ background: s.soft }" />
        <span class="relative flex items-center gap-2.5">
          <span class="grid size-10 shrink-0 place-items-center rounded-xl text-white transition-transform group-hover/doc:-translate-y-1" :style="{ background: s.color }">
            <Icon :name="s.icon" class="size-5" />
          </span>
          <b class="text-[15px] leading-tight text-ink">{{ t(`cabinet.docs.sections.${s.key}`) }}</b>
        </span>
        <span class="relative mt-3.5 text-muted">
          <b class="font-display text-[40px] leading-none text-ink">{{ documents[s.key].count }}</b>
          {{ t('cabinet.docs.count') }}
        </span>
        <span class="relative mt-3 flex min-h-9 items-center gap-2 border-t border-dashed border-line pt-3 text-xs leading-snug text-muted">
          <template v-if="s.toggleable">
            <button
              type="button"
              role="switch"
              :aria-checked="documents[s.key].visible"
              :aria-label="t(`cabinet.docs.sections.${s.key}`)"
              class="relative h-6 w-10.5 shrink-0 rounded-full p-[3px] transition-colors"
              :class="documents[s.key].visible ? 'bg-accent-600' : 'bg-[#cfcbd8]'"
              @click="emit('toggle', s.key as StaffDocSection, !documents[s.key].visible)"
            >
              <span class="block size-[18px] rounded-full bg-white transition-transform" :class="documents[s.key].visible && 'translate-x-[18px]'" />
            </button>
            {{ documents[s.key].visible ? t('cabinet.docs.visible') : t('cabinet.docs.hidden') }}
          </template>
          <template v-else>
            <Icon name="lucide:lock" class="size-3.5 shrink-0" />
            {{ t('cabinet.docs.dashboardOnly') }}
          </template>
        </span>
        <button
          type="button"
          aria-haspopup="dialog"
          class="relative mt-3 flex h-10.5 items-center justify-center gap-1.5 rounded-xl border bg-white text-[13px] font-bold text-ink transition-colors hover:bg-(--c) hover:text-white"
          :style="{ borderColor: s.color, '--c': s.color }"
          @click="emit('open', s.key)"
        >
          <Icon name="lucide:upload" class="size-[15px]" />
          {{ s.key === 'videos' ? t('cabinet.docs.addLink') : t('cabinet.docs.upload') }}
        </button>
      </li>
    </ul>
  </section>
</template>
