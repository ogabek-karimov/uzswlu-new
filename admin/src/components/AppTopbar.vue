<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth, initials, ROLE_LABELS } from '@/lib/auth'
import Icon from './Icon.vue'

defineEmits<{ menu: [] }>()
const router = useRouter()
const userOpen = ref(false)

async function logout() {
  await auth.logout()
  router.push('/kirish')
}
</script>

<template>
  <header class="sticky top-0 z-20 flex min-h-[72px] flex-wrap items-center gap-3.5 border-b border-line bg-white px-4 py-3 sm:px-7">
    <button type="button" aria-label="Menyuni oçiş" class="grid size-10 place-items-center rounded-xl border border-line text-muted lg:hidden" @click="$emit('menu')">
      <Icon name="menu" :size="18" />
    </button>

    <div class="ml-auto flex items-center gap-2.5">
      <RouterLink to="/postlar/news/yangi" class="btn-primary h-[42px]">
        <Icon name="plus" :size="16" />
        <span class="hidden sm:inline">Yangi qöşiş</span>
      </RouterLink>

      <div class="relative">
        <button type="button" class="flex items-center gap-2.5 border-l border-line pl-3" :aria-expanded="userOpen" @click="userOpen = !userOpen">
          <span class="grid size-[42px] place-items-center rounded-full bg-gradient-to-br from-brand-700 to-night text-sm font-bold text-mint">{{ initials(auth.user.value?.name) }}</span>
          <span class="hidden text-left leading-tight sm:block">
            <span class="block text-sm font-semibold">{{ auth.user.value?.name }}</span>
            <span class="block text-xs text-muted">{{ ROLE_LABELS[auth.user.value?.role ?? 'editor'] }}</span>
          </span>
          <Icon name="chevronDown" :size="16" class="text-muted" />
        </button>
        <div v-if="userOpen" class="absolute right-0 mt-2 w-56 rounded-2xl border border-line bg-white p-1.5 shadow-xl" @click="userOpen = false">
          <RouterLink to="/profil" class="flex h-10 items-center gap-2.5 rounded-xl px-3 text-sm font-medium hover:bg-canvas">Mening profilim</RouterLink>
          <button type="button" class="flex h-10 w-full items-center gap-2.5 rounded-xl px-3 text-sm font-medium text-red-700 hover:bg-red-50" @click="logout">
            <Icon name="logout" :size="16" /> Çiqiş
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
