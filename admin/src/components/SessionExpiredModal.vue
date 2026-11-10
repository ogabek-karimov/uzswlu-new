<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { abandonSession, recheckSession, session } from '@/lib/session'

// Sessiya tugaganda, lekin sahifada saqlanmagan ish bo'lsa: sahifa o'z holicha qoladi.
const router = useRouter()

const openLogin = () => window.open('/kirish?close=1', '_blank')
const recheck = () => { if (session.expired) void recheckSession(router) }

onMounted(() => {
  window.addEventListener('focus', recheck)
  document.addEventListener('visibilitychange', recheck)
})
onBeforeUnmount(() => {
  window.removeEventListener('focus', recheck)
  document.removeEventListener('visibilitychange', recheck)
})
</script>

<template>
  <div v-if="session.expired" class="fixed inset-0 z-[90] grid place-items-center bg-night/55 p-4">
    <section role="alertdialog" aria-modal="true" aria-labelledby="session-title" aria-describedby="session-text" class="w-full max-w-[460px] rounded-[22px] bg-white p-6 shadow-2xl">
      <h2 id="session-title" class="text-xl font-bold tracking-tight">Sessiya muddati tugadi</h2>
      <p id="session-text" class="mt-2 text-[15px] leading-relaxed text-muted">
        Xavfsizlik uchun kirish muddati tugadi. Yozganlaringiz bu oynada saqlanib turibdi.
        Yangi oynada qayta kiring, so‘ng shu yerga qaytib «Saqlash» tugmasini bosing.
      </p>
      <div class="mt-5 flex flex-wrap items-center gap-3">
        <button type="button" class="btn-primary" @click="openLogin">Qayta kirish (yangi oynada)</button>
        <button type="button" class="text-[14px] font-semibold text-muted underline-offset-2 hover:underline" @click="abandonSession(router)">Saqlamasdan chiqish</button>
      </div>
    </section>
  </div>
</template>
