// Murojaat matni «haqiqiy matn»mi: tasodifiy harflar (asdfgh, ааааа), bir so'zni takrorlash va belgilar to'plamini rad etadi.
// 4 til: o'zbek (lotin/kirill), rus, ingliz, xitoy. Qisqartmalar (BRM, AKT, PhD, IELTS), raqamli so'zlar, havola va e-pochtalar hisobga olinmaydi.
// Backend'dagi apps/api/text_quality.py bilan bir xil qoidalar.

const VOWELS = /[aeiouyöüıаеёиоуыэюяўіїє]/i
const CONSONANT_RUN = /[bcdfghjklmnpqrstvwxzğşçбвгджзйклмнпрстфхцчшщқғҳ]{5,}/i
const VOWELS_G = /[aeiouyöüıаеёиоуыэюяўіїє]/gi
const ROWS = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm', 'йцукенгшщзхъ', 'фывапролджэ', 'ячсмитьбю']
// Klaviatura qatori bo'yicha 5+ harf ketma-ket (asdfg, фывап); 4 bo'lsa ruscha «запрос», «проложить» ham tushib qolardi
const keyboardRun = (w: string) => { const l = w.toLowerCase(); for (let i = 0; i + 5 <= l.length; i++) if (ROWS.some(r => r.includes(l.slice(i, i + 5)))) return true; return false }
// Unlisi juda kam uzun so'z (inglizcha spring, grants, strong bu chegaradan o'tadi)
const lowVowels = (w: string) => w.length >= 7 && (w.match(VOWELS_G)?.length ?? 0) / w.length < 0.125   // ruscha «средств» (1/7) o'tadi
// Kichik harf bilan ham yoziladigan ilmiy daraja/atama qisqartmalari
const ABBR = new Set(['phd', 'dsc', 'msc', 'bsc', 'mba', 'llm', 'md', 'ielts', 'toefl', 'sat', 'gpa', 'cefr', 'brm', 'akt', 'dtm', 'otm', 'hemis'])

// ── Haqoratli so'zlar ──
// Asosiy ro'yxat admin panelda (admin → Haqoratli so'zlar), sayt uni GET /contact → rudeWords orqali oladi.
// Quyidagisi — faqat API ro'yxat bermaganda (mock rejim) ishlatiladigan zaxira (backend/seed_data/rude_words.json bilan bir xil).
export const DEFAULT_RUDE_WORDS: string[] = ["jalab*", "qanjiq*", "dalbayob*", "dalbayop*", "dalbayeb*", "ahmoq*", "axmoq*", "itvachcha*", "haromi", "haromzoda*", "siktir*", "sikaman*", "sikay*", "qotoq*", "qutoq*", "tentak*", "onangni*ski*", "kalanga*", "shalava*", "жалаб*", "қанжиқ*", "канжик*", "далбаёб*", "аҳмоқ*", "ахмоқ*", "ахмок*", "итвачча*", "ҳароми", "сиктир*", "қутоқ*", "тентак*", "хуй*", "хуе*", "хуё*", "хуя*", "хуи*", "нахуй*", "нахер*", "пизд*", "ебат*", "ебан*", "ебал*", "ебл*", "ебу*", "заеб*", "выеб*", "уеб*", "отъеб*", "долбоеб*", "долбаеб*", "бляд*", "блят*", "бля", "сука", "суки", "сучка*", "мудак*", "мудил*", "гандон*", "пидор*", "пидар*", "педик*", "залуп*", "шлюх*", "дебил*", "урод*", "мразь*", "мрази", "тварь", "твари", "козел", "козёл", "идиот*", "дура", "дурак*", "придур*", "fuck*", "motherf*", "shit*", "bullshit*", "bitch*", "bastard*", "asshole*", "dick", "dickhead*", "cunt*", "whore*", "slut*", "idiot*", "moron*", "stupid", "retard*", "jerk", "scum*", "wtf", "stfu", "傻逼", "傻b", "他妈的", "妈的", "操你", "草泥马", "混蛋", "王八蛋", "去死", "婊子", "狗日", "贱人", "滚蛋", "白痴", "脑残"]

export type RudeTest = (token: string) => boolean

// Yashirish usullari: katta/kichik harf, ё→е, tutuq belgilari, @/0/1/$/3/4 almashtirish, kirill so'zdagi lotin o'xshash harflar
const LEET: Record<string, string> = { '@': 'a', '0': 'o', '1': 'i', '$': 's', '3': 'e', '4': 'a' }
const LAT2CYR: Record<string, string> = { a: 'а', e: 'е', o: 'о', p: 'р', c: 'с', x: 'х', y: 'у', k: 'к', m: 'м', t: 'т', h: 'н', b: 'в' }
// Kirill → lotin «skelet»: rus so'zi lotincha yozilsa ham ushlanadi (blyad, nahuy, pizda). «x» → «h» QILINMAYDI (o'zbekcha «xuy-atvor»)
const CYR2LAT: Record<string, string> = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'e', ж: 'j', з: 'z', и: 'i', й: 'i', к: 'k', л: 'l', м: 'm', н: 'n', о: 'o', п: 'p', р: 'r',
  с: 's', т: 't', у: 'u', ф: 'f', х: 'h', ц: 'c', ч: 'ch', ш: 'sh', щ: 'sh', ъ: '', ы: 'i', ь: '', э: 'e', ю: 'iu', я: 'ia', ў: 'o', қ: 'q', ғ: 'g', ҳ: 'h',
}
const LAT_SKELETON: [string, string][] = [['sch', 'sh'], ['shch', 'sh'], ['kh', 'h'], ['zh', 'j'], ['ya', 'ia'], ['ja', 'ia'], ['yu', 'iu'], ['ju', 'iu'], ['yo', 'e'],
  ['ye', 'e'], ['ts', 'c'], ['tz', 'c'], ['y', 'i'], ['w', 'v']]   // «j→i» yo'q: o'zbekcha «hujjat» ≠ «хуй»
const CYRILLIC = /[а-яёўқғҳ]/
const cyrSkeleton = (w: string) => [...w].map(c => CYR2LAT[c] ?? c).join('')
const latSkeleton = (w: string) => LAT_SKELETON.reduce((acc, [x, y]) => acc.split(x).join(y), w)

function rudeKey(token: string): string {
  let w = token.toLowerCase().replace(/ё/g, 'е').replace(/[‘’ʻʼ`']/g, '').replace(/[@01$34]/g, c => LEET[c]!)
  w = w.replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '')
  if (CYRILLIC.test(w)) w = w.replace(/[aeopcxykmthb]/g, c => LAT2CYR[c]!)
  return w
}

/** Ro'yxatdan tekshirgich: «*» bilan tugasa — so'z boshi, ichida «*» — namuna, aks holda — aynan so'z; xitoycha — matn ichida.
 *  Backend'dagi apps/api/text_quality.py → RudeMatcher bilan bir xil. */
export function makeRudeTest(words: string[]): RudeTest {
  const exact = new Set<string>(); const prefix: string[] = []; const cjk: string[] = []; const pattern: RegExp[] = []
  const latExact = new Set<string>(); const latPrefix: string[] = []
  for (const raw of words) {
    const w = (raw ?? '').trim().toLowerCase().replace(/ё/g, 'е')
    if (!w) continue
    if (/[\u3400-\u9FFF]/.test(w)) cjk.push(w)
    else if (w.slice(0, -1).includes('*')) pattern.push(new RegExp(`^${w.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*')}`))
    else if (w.endsWith('*')) { prefix.push(w.slice(0, -1)); if (CYRILLIC.test(w)) latPrefix.push(cyrSkeleton(w.slice(0, -1))) }
    else { exact.add(w); if (CYRILLIC.test(w)) latExact.add(cyrSkeleton(w)) }
  }
  return (token: string) => {
    if (cjk.some(r => token.includes(r))) return true
    const w = rudeKey(token)
    if (w.length < 2) return false
    if (exact.has(w) || prefix.some(p => w.startsWith(p)) || pattern.some(r => r.test(w))) return true
    if (/^[a-z]+$/.test(w)) { const sk = latSkeleton(w); return latExact.has(sk) || latPrefix.some(p => sk.startsWith(p)) }
    return false
  }
}
const defaultRude = makeRudeTest(DEFAULT_RUDE_WORDS)
const noRude: RudeTest = () => false
/** Server (Nuxt) tomoni uchun: haqoratli so'zlarni backend o'z ro'yxati bilan tekshiradi */
export const SKIP_RUDE = noRude

const CJK = /[㐀-鿿豈-﫿]/g

/** Matn muammosi: null — yaxshi; 'rude' — haqoratli so'z; 'short' — juda qisqa / 3 so'zdan kam; 'random' — tasodifiy harflar yoki belgilar; 'repeat' — bir so'z takrori */
export type TextIssue = 'rude' | 'short' | 'random' | 'repeat' | null

export function isMeaningfulText(raw: string, rude: RudeTest = defaultRude): boolean {
  return textIssue(raw, rude) === null
}

export function textIssue(raw: string, rude: RudeTest = defaultRude): TextIssue {
  const text = raw.trim()
  if (text.split(/\s+/).some(rude)) return 'rude'
  if (text.length < 10) return 'short'
  // Bir belgi 5+ marta ketma-ket (aaaaa, !!!!!, 11111)
  if (/(.)\1{4,}/u.test(text.replace(/\s/g, ''))) return 'random'

  // Xitoycha: kamida 5 ta ierogli bo'lsa — yetarli
  const cjk = text.match(CJK)?.length ?? 0
  if (cjk >= 5) return null

  const tokens = text.split(/\s+/).filter(Boolean)
  // Havola, e-pochta, raqamli so'zlar va qisqartmalar (KATTA HARFLAR, ≤ 8) baholanmaydi
  const words = tokens
    .filter(w => !/[/@]|\.\w/.test(w) && !/\d/.test(w))
    .map(w => w.replace(/^[^\p{L}]+|[^\p{L}]+$/gu, ''))
    .filter(w => w.length >= 2)
  // Qisqa, lekin tasodifiy harfli bo'lsa — asosiy sabab tasodifiy harflar
  if (words.length < 3) return tokens.some(isJunkWord) ? 'random' : 'short'

  const letters = (text.match(/\p{L}/gu) ?? []).length
  const visible = text.replace(/\s/g, '').length
  if (letters / visible < 0.6) return 'random'

  // Qisqartmalar (BRM, AKT, PhD, DSc, DsC, MSc): so'z sifatida sanaladi, lekin shubhali deb baholanmaydi
  const isAbbr = (w: string) => ABBR.has(w.toLowerCase()) || w.length <= 8 && /\p{Lu}/u.test(w.slice(1)) || (w.length <= 8 && w === w.toUpperCase() && w !== w.toLowerCase())
  if (words.filter(w => !isAbbr(w)).length < 2) return tokens.some(isJunkWord) ? 'random' : 'short'   // faqat qisqartmalardan iborat matn emas
  const junk = words.filter(w => !isAbbr(w) && isJunkWord(w)).length   // qizil belgilash bilan bir xil qoida
  if (junk / words.length > 0.25) return 'random'

  const lower = words.map(w => w.toLowerCase())
  if (lower.length >= 6 && new Set(lower).size / lower.length < 0.35) return 'repeat'
  if (repeatFlags(lower).some(Boolean)) return 'repeat'
  return null
}

/** Takror: bir so'z ketma-ket ikki marta 2+ joyda (shunday shunday … qanday qanday) yoki 3+ marta ketma-ket (bugun bugun bugun),
 *  yoki bitta so'z matnning 40% dan ko'pi (kamida 3 marta, 5+ so'zda). Bitta «juda juda» — ruxsat.
 *  Ortiqcha takrorlar uchun true (birinchi ishlatilishi — false). */
function repeatFlags(lower: string[]): boolean[] {
  const dup = lower.map((w, i) => i >= 1 && w === lower[i - 1])
  const triple = lower.some((w, i) => i >= 2 && w === lower[i - 1] && w === lower[i - 2])
  const flags = triple || dup.filter(Boolean).length >= 2 ? dup : lower.map(() => false)
  if (lower.length >= 5) {
    const freq = new Map<string, number>()
    for (const w of lower) freq.set(w, (freq.get(w) ?? 0) + 1)
    const seen = new Set<string>()
    lower.forEach((w, i) => {
      const n = freq.get(w)!
      if (n >= 3 && n / lower.length > 0.4 && seen.has(w)) flags[i] = true
      seen.add(w)
    })
  }
  return flags
}

const norm = (token: string) => token.replace(/^[^\p{L}\d]+|[^\p{L}\d]+$/gu, '').toLowerCase()

/** Matn oynasida qizil bilan belgilanadigan bo'laklar (bo'sh joy bilan ajratilgan, tartib bo'yicha): tasodifiy harflar yoki ortiqcha takror. */
export function junkFlags(text: string, rude: RudeTest = defaultRude): boolean[] {
  const tokens = text.split(/\s+/).filter(Boolean)
  const idx: number[] = []
  const lower: string[] = []
  tokens.forEach((t, i) => { const w = norm(t); if (w.length >= 2) { idx.push(i); lower.push(w) } })
  const flags = tokens.map(t => isJunkWord(t) || rude(t))
  repeatFlags(lower).forEach((f, j) => { if (f) flags[idx[j]!] = true })
  return flags
}

/** Bitta so'z (bo'sh joysiz bo'lak) tasodifiy harflarmi — matn oynasida qizil bilan belgilash uchun. Qisqartma, raqam, havola — yo'q. */
export function isJunkWord(token: string): boolean {
  if (/(.)\1{4,}/u.test(token)) return true
  if (/[\u3400-\u9FFF\uF900-\uFAFF\u0590-\u08FF]/.test(token)) return false   // xitoycha, arabcha/forscha — unli/undosh qoidalari tegishli emas
  if (/[/@]|\.\w/.test(token) || /\d/.test(token)) return false
  const w = token.replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '')
  if (w.length < 2 || ABBR.has(w.toLowerCase()) || (w.length <= 8 && (/\p{Lu}/u.test(w.slice(1)) || (w === w.toUpperCase() && w !== w.toLowerCase())))) return false
  return (w.length >= 5 && !VOWELS.test(w)) || CONSONANT_RUN.test(w) || keyboardRun(w) || lowVowels(w) || w.length > 30
}

/** Barcha muammolar (ogohlantirishda hammasi aytiladi): avval tasodifiy harflar, keyin takror; ular bo'lsa «qisqa» aytilmaydi. */
export function textIssues(raw: string, rude: RudeTest = defaultRude): Exclude<TextIssue, null>[] {
  const main = textIssue(raw, rude)
  if (!main) return []
  const set = new Set<Exclude<TextIssue, null>>([main])
  const tokens = raw.trim().split(/\s+/).filter(Boolean)
  if (tokens.some(rude)) set.add('rude')
  if (tokens.some(isJunkWord)) set.add('random')
  const lower = tokens.map(norm).filter(w => w.length >= 2)
  if ((lower.length >= 6 && new Set(lower).size / lower.length < 0.35) || repeatFlags(lower).some(Boolean)) set.add('repeat')
  if (set.has('random') || set.has('repeat')) set.delete('short')
  return (['rude', 'random', 'repeat', 'short'] as const).filter(k => set.has(k))
}
