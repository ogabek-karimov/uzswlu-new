// Sessiya tugaganda qaror (sof funksiya, import'larsiz — scripts/test-api.mts sinaydi)

/** 401 kelganda nima qilish (sof qaror — testlanadi): 'ignore' | 'modal' | 'redirect' */
export function onSessionExpired(state: { loggedIn: boolean; expired: boolean; unsaved: number; touched: boolean }): 'ignore' | 'modal' | 'redirect' {
  if (state.expired || !state.loggedIn) return 'ignore'
  return state.unsaved > 0 || state.touched ? 'modal' : 'redirect'
}
