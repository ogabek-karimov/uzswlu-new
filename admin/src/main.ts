import { createApp } from 'vue'
import App from './App.vue'
import { loadSiteSettings } from './lib/settings'
import { router } from './router'
import './styles.css'

createApp(App).use(router).mount('#app')
loadSiteSettings()
