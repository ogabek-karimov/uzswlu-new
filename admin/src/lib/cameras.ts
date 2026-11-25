// Onlayn kameralar (Online translatsiya): sahifa matnida har kamera bitta xatboşi — «Nomi | https://rtsp.ru/embed/…/».
// Boşida «-» bölsa — saytda yaşirin. Saytda setkani backend quradi (builders_site.cameras_html).
export type Camera = { name: string; url: string; hidden: boolean }

const LINE = /<p>(?:<[^>]+>|\s)*([^<|]{1,60}?)\s*\|\s*(?:<a[^>]*>)?\s*(https:\/\/rtsp\.ru\/embed\/[\w-]+\/?)\s*(?:<\/a>)?(?:<\/[^>]+>|\s)*<\/p>/g

export function parseCameras(html: string): Camera[] {
  return [...(html ?? '').matchAll(LINE)].map(([, name = '', url = '']) => {
    const n = name.trim()
    return { name: n.replace(/^[-#]\s*/, ''), url, hidden: /^[-#]/.test(n) }
  })
}

export const stripCameras = (html: string) => (html ?? '').replace(LINE, '').trim()

const esc = (s: string) => s.replace(/[&<>"|]/g, '')

/** Admin kiritgan havola yoki rtsp.ru bergan to'liq <iframe …> kodi → toza embed havola (bölmasa '') */
export function cameraUrl(input: string): string {
  const m = (input ?? '').match(/https:\/\/rtsp\.ru\/embed\/[\w-]+\/?/)
  return m ? m[0] : ''
}

export function camerasHtml(list: Camera[]): string {
  return list
    .filter(c => c.name.trim() && cameraUrl(c.url))
    .map(c => `<p>${c.hidden ? '- ' : ''}${esc(c.name.trim())} | ${cameraUrl(c.url)}</p>`)
    .join('')
}
