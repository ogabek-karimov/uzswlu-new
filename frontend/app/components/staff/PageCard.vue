<script setup lang="ts">
import type { PageStaff } from '#shared/types/api'

// Sahifadagi bölim xodimi kartasi (eski saytdagidek): surat, F.I.Sh., lavozim, telefon, qabul kunlari, e-poçta.
// Telefon / e-poçta / qabul kunlari kiritilmagan bölsa — qatori körinmaydi. Ism va surat — xodim profiliga.
const props = defineProps<{ person: PageStaff }>()

const { t } = useI18n()
const localePath = useLocalePath()
const fullName = computed(() => staffName(props.person.name, props.person.patronymic).full)
const profile = computed(() => localePath(`/teacher/${props.person.id}`))
const tel = computed(() => props.person.phone ? `tel:${props.person.phone.replace(/[^\d+]/g, '')}` : '')
</script>

<template>
  <article class="group flex h-full flex-col overflow-hidden rounded-3xl border border-line bg-white transition duration-300 hover:border-accent-500 hover:shadow-[0_20px_44px_-30px_var(--color-accent-600)]">
    <NuxtLink :to="profile" tabindex="-1" aria-hidden="true" class="block overflow-hidden bg-paper">
      <StaffAvatar :id="person.id" :name="fullName" :photo="person.photo" :fallback="person.photoFallback" decorative class="aspect-[4/3.4] w-full rounded-none text-5xl transition-transform duration-500 group-hover:scale-[1.03]" />
    </NuxtLink>
    <div class="flex flex-1 flex-col gap-1.5 p-4 sm:p-[18px]">
      <h3 class="leading-snug font-bold text-ink">
        <NuxtLink :to="profile" class="hover:text-brand-700">{{ fullName }}</NuxtLink>
      </h3>
      <p v-if="person.position" class="text-[13px] leading-snug font-semibold text-brand-700">{{ person.position }}</p>
      <dl v-if="person.phone || person.hours || person.email" class="mt-1.5 flex flex-col gap-1.5 border-t border-line pt-2.5 text-[13px] leading-snug text-ink/80">
        <div v-if="person.phone" class="flex gap-2">
          <dt class="flex shrink-0 items-center"><Icon name="lucide:phone" class="size-3.5 text-muted" /><span class="sr-only">{{ t('page.staffPhone') }}</span></dt>
          <dd><a :href="tel" class="tabular-nums hover:text-brand-700">{{ person.phone }}</a></dd>
        </div>
        <div v-if="person.hours" class="flex gap-2">
          <dt class="flex shrink-0 items-start pt-0.5"><Icon name="lucide:clock-3" class="size-3.5 text-muted" /><span class="sr-only">{{ t('page.staffHours') }}</span></dt>
          <dd>{{ person.hours }}</dd>
        </div>
        <div v-if="person.email" class="flex gap-2">
          <dt class="flex shrink-0 items-center"><Icon name="lucide:mail" class="size-3.5 text-muted" /><span class="sr-only">E-mail</span></dt>
          <dd class="min-w-0"><a :href="`mailto:${person.email}`" class="break-all hover:text-brand-700">{{ person.email }}</a></dd>
        </div>
      </dl>
    </div>
  </article>
</template>
