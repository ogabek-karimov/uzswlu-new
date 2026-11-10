import { createApp } from 'vue'
import App from './App.vue'
import { loadSiteSettings } from './lib/settings'
import { router } from './router'
import { installSessionGuards } from './lib/session'
import './styles.css'

installSessionGuards(router)
createApp(App).use(router).mount('#app')
loadSiteSettings()
