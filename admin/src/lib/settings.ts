import { reactive } from 'vue'
import { api, type I18n } from './api'

// Sayt sozlamalaridan admin panelga kerakli qism (texnik yordam havolasi)
export const siteSettings = reactive<{ supportUrl: string; supportText: string; showInAdmin: boolean; loaded: boolean }>({
  supportUrl: 'https://t.me/Uzswlu_rttm',
  supportText: 'Texnik yordam',
  showInAdmin: true,
  loaded: false,
})

export async function loadSiteSettings() {
  try {
    const s = await api.get<{ support?: { telegram?: string; text?: I18n; showInAdmin?: boolean } }>('/globals/settings')
    if (s.support?.telegram) siteSettings.supportUrl = s.support.telegram
    if (s.support?.text?.uz) siteSettings.supportText = s.support.text.uz
    siteSettings.showInAdmin = s.support?.showInAdmin !== false
  }
  catch {
    // standart qiymatlar qoladi
  }
  siteSettings.loaded = true
}
