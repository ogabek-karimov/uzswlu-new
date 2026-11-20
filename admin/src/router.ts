import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from './components/AdminLayout.vue'
import { auth } from './lib/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/kirish', name: 'login', component: () => import('./pages/LoginPage.vue'), meta: { public: true, title: 'Kiriş' } },
    {
      path: '/',
      component: AdminLayout,
      children: [
        { path: '', name: 'dashboard', component: () => import('./pages/DashboardPage.vue'), meta: { title: 'Boşqaruv paneli', section: 'dashboard' } },
        { path: 'postlar/:type(news|announcements|events)', name: 'posts', component: () => import('./pages/PostsPage.vue'), meta: { title: 'Postlar' } },
        { path: 'postlar/:type(news|announcements|events)/yangi', name: 'post-new', component: () => import('./pages/PostEditPage.vue'), meta: { title: 'Yangi post' } },
        { path: 'postlar/:type(news|announcements|events)/:id(\\d+)', name: 'post-edit', component: () => import('./pages/PostEditPage.vue'), meta: { title: 'Postni tahrirlaş' } },
        { path: 'foydalanuvchilar', name: 'users', component: () => import('./pages/UsersPage.vue'), meta: { title: 'Foydalanuvçilar', superOnly: true } },
        { path: 'rollar', name: 'roles', component: () => import('./pages/RolesPage.vue'), meta: { title: 'Rollar', superOnly: true } },
        { path: 'kirish-tarixi', name: 'logins', component: () => import('./pages/LoginHistoryPage.vue'), meta: { title: 'Kiriş tarixi', superOnly: true } },
        { path: 'faollik', name: 'activity', component: () => import('./pages/ActivityPage.vue'), meta: { title: 'Faollik jurnali', superOnly: true } },
        { path: 'sozlamalar', name: 'settings', component: () => import('./pages/SettingsPage.vue'), meta: { title: 'Sayt sozlamalari', superOnly: true } },
        { path: 'profil', name: 'profile', component: () => import('./pages/ProfilePage.vue'), meta: { title: 'Mening profilim' } },
        { path: 'tezkor-xizmatlar', name: 'quick-links', component: () => import('./pages/QuickLinksPage.vue'), meta: { title: 'Tezkor xizmatlar', section: 'quick-links' } },
        { path: 'telefonlar', name: 'phones', component: () => import('./pages/PhonesPage.vue'), meta: { title: 'Telefonlar', section: 'phones' } },
        { path: 'haqoratli-sozlar', name: 'rude-words', component: () => import('./pages/RudeWordsPage.vue'), meta: { title: 'Haqoratli sözlar', section: 'rude-words' } },
        { path: 'karusel', name: 'carousel', component: () => import('./pages/CarouselPage.vue'), meta: { title: 'Boş sahifa karuseli', superOnly: true } },
        { path: 'media', name: 'media', component: () => import('./pages/MediaPage.vue'), meta: { title: 'Media kutubxona', section: 'media' } },
        { path: 'hujjatlar', name: 'documents', component: () => import('./pages/DocumentsPage.vue'), meta: { title: 'Hujjatlar', section: 'documents' } },
        { path: 'video', name: 'videos', component: () => import('./pages/VideosPage.vue'), meta: { title: 'Video darsliklar', section: 'videos' } },
        { path: 'rahbariyat', name: 'leaders', component: () => import('./pages/LeadersPage.vue'), meta: { title: 'Rahbariyat', section: 'leaders' } },
        { path: 'ramzlar', name: 'symbols', component: () => import('./pages/SymbolsPage.vue'), meta: { title: 'Ramzlar', superOnly: true } },
        { path: 'fakultetlar', name: 'faculties', component: () => import('./pages/FacultiesPage.vue'), meta: { title: 'Fakultetlar', section: 'faculties' } },
        { path: 'kafedralar', name: 'departments', component: () => import('./pages/DepartmentsPage.vue'), meta: { title: 'Kafedralar', section: 'departments' } },
        { path: 'xodimlar', name: 'staff', component: () => import('./pages/StaffPage.vue'), meta: { title: 'Xodimlar', section: 'staff' } },
        { path: 'brm', name: 'sdg', component: () => import('./pages/BrmPage.vue'), meta: { title: 'BRM', section: 'sdg' } },
        { path: 'sahifalar', name: 'pages', component: () => import('./pages/PagesPage.vue'), meta: { title: 'Sahifalar', section: 'pages' } },
        { path: 'statistika', name: 'stats', component: () => import('./pages/StatsPage.vue'), meta: { title: 'Statistika', superOnly: true } },
        { path: ':rest(.*)*', redirect: '/' },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (!auth.state.checked) await auth.me()
  const user = auth.state.user
  if (to.meta.public) return user && to.name === 'login' ? '/' : true
  if (!user) return { name: 'login', query: to.fullPath !== '/' ? { r: to.fullPath } : undefined }
  // Boshlang'ich sahifa: rolga ruxsat berilgan birinchi bo'lim
  const home = auth.homePath()
  if (to.meta.superOnly) return user.role === 'superadmin' ? true : home
  const section = (to.meta.section as string | undefined)
    ?? (to.params.type ? String(to.params.type) : undefined)
  if (section && !auth.can(section)) return to.fullPath === home ? true : home
  return true
})

router.afterEach((to) => {
  document.title = `${to.meta.title ?? 'Boşqaruv paneli'} — ÖzDJTU`
})
