// Backend bilan kelishiladigan API shartnomasi (frontend shu turlarga tayanadi).
// Barcha matnli maydonlar so'ralgan tilda (?lang=uz|ru|en|zh) qaytariladi.
import type { Locale } from '../utils/locale'

export interface Slide {
  id: string
  /** Banner rasmi URL'i. Nisbati 16:9 bo'lishi shart (1920×1080) — karusel aynan shu o'lchamda; boshqa nisbat qirqilmaydi, lekin chetlari xira fon bilan to'ldiriladi */
  image: string
  /** Ekran o'quvchilar uchun rasm mazmuni (so'ralgan tilda) */
  alt: string
  /** Bosilganda ochiladigan sahifa (ixtiyoriy) */
  link?: string | null
}

export interface Partner {
  id: string
  name: string
  logo: string
  url?: string | null
}

export interface Stat {
  key: 'faculties' | 'staff' | 'departments' | 'students'
  /** Aniq son (masalan HEMIS'dan 17384). Qisqartirishni frontend o'zi qiladi: 17384 → "17K+" */
  value: number
}

export interface Faculty {
  id: string
  slug: string
  name: string
  /** Fakultet logosi URL'i */
  logo?: string | null
}

export interface NewsItem {
  id: string
  slug: string
  title: string
  category: string
  /** ISO sana: 2026-10-20 */
  date: string
  image?: string | null
  /** BRM (barqaror rivojlanish) maqsadi raqami 1–17 — kartada rangli belgi; kirmasa null */
  sdg?: number | null
}

export interface Announcement {
  id: string
  slug: string
  title: string
  date: string
  /** E'lon surati (odatda tik afisha) */
  image?: string | null
  sdg?: number | null
}

export interface EventItem {
  id: string
  slug: string
  title: string
  category: string
  /** Boshlanish vaqti, ISO 8601 vaqt mintaqasi bilan: 2026-11-07T10:00:00+05:00 */
  startsAt: string
  endsAt?: string | null
  location: string
  image?: string | null
}

export interface TaughtLanguage {
  code: string
  /** Tilning o'z yozuvidagi nomi: Deutsch, 中文, العربية */
  native: string
  /** Shu tilda o'qitiladigan yo'nalishlar soni */
  programs?: number
  /** Shu tilda yo'nalishi bor fakultetlar soni */
  faculties?: number
}

/** GET /home?lang= — bosh sahifa */
export interface HomeData {
  /** Bosh sahifa karuseli, ko'rsatish tartibida */
  slides: Slide[]
  stats: Stat[]
  faculties: Faculty[]
  news: NewsItem[]
  announcements: Announcement[]
  /** Yaqin tadbirlar, boshlanish vaqti bo'yicha o'sish tartibida (3 tagacha) */
  events: EventItem[]
  languages: TaughtLanguage[]
  partners: Partner[]
  /** Bayram banneri — admin panelda bitta rasm; yashirilgan yoki rasmi yo'q bo'lsa null */
  banner?: HomeBanner | null
  /** «Universitet haqida» video turi — admin panelda («Universitet haqida» bo'limi) kiritiladi; havola yo'q yoki yashirilgan bo'lsa null */
  videoTour?: HomeVideoTour | null
  /** «Tezkor xizmatlar» kartalari — admin panelda alohida sahifadan boshqariladi; bo'sh bo'lsa blok chiqmaydi */
  quickLinks?: QuickLinkItem[]
  /** HEMIS ma'lumotlari oxirgi marta yangilangan vaqt (ISO) */
  updatedAt: string
}

export interface HomeBanner {
  image: string
  /** Asl rasm o'lchami — rasm yuklanguncha joyi oldindan ajratiladi */
  width?: number | null
  height?: number | null
  /** Rasm tavsifi (bo'sh bo'lishi mumkin) */
  alt: string
  /** Bosilganda ochiladi: /ichki-sahifa yoki https://… */
  link?: string | null
}

export interface Campus {
  id: string
  name: string
  address: string
}

export interface SocialLink {
  network: 'telegram' | 'instagram' | 'facebook' | 'youtube' | 'x'
  url: string
}

export interface MenuLink {
  title: string
  /** Ichki yo'l ("/universitet-haqida") yoki to'liq URL (PDF, tashqi sayt) */
  url: string
  /** Fayl turi — yonida belgi chiqadi */
  file?: 'pdf' | null
  /** Ajratib ko'rsatiladigan havola (masalan "Qabul – 2026/2027") */
  highlight?: boolean
  /** BRM bo'limi: BMT barqaror rivojlanish maqsadi raqami (1–17) — rangli plitka bo'lib chiqadi */
  sdg?: number | null
}

export interface MenuGroup {
  /** Barqaror kalit: university | applicants | activity | news | sdg | programs | video | contact (ikonka shunga qarab tanlanadi) */
  id: string
  title: string
  description?: string | null
  /** Bitta sahifali bo'lim (Yangiliklar, Aloqa) — ochiladigan menyu o'rniga to'g'ridan-to'g'ri havola */
  url?: string | null
  /** Bo'limning umumiy sahifasi (BRM → "/brm"): mega-menyuda bo'lim nomi va belgisi shu sahifaga havola bo'ladi */
  overview?: string | null
  links: MenuLink[]
}

/** Xodim guruhi — ro'yxatdagi filtr tugmalari shunga qarab ishlaydi */
export type StaffGroup = 'lead' | 'faculty' | 'chair' | 'unit'

export interface StaffDepartment {
  id: string
  name: string
  group: StaffGroup
  /** Bo'limdagi xodimlar soni */
  count: number
}

/** HEMIS kod + nom juftligi (staffPosition, employmentForm, employeeStatus, employeeType) */
export interface HemisRef {
  code: string
  name: string
}

/**
 * Xodimning bitta ish joyi — HEMIS'dagi bitta qator, o'zgartirmasdan (HEMIS tartibida).
 * Frontend oldingi saytdagi qoidalarni o'zi qo'llaydi: status 14 (ishdan bo'shagan) ko'rsatilmaydi;
 * lavozimlarda avval boshqaruv/asosiy lavozim, keyin o'qituvchilik lavozimlari (kod 11–15); bo'limlar ham shu tartibda.
 */
export interface HemisEmployment {
  department: { id: string; name: string }
  /** HEMIS staffPosition. Kod 11–15 — o'qituvchilik lavozimlari (Stajer-o'qituvchi … Professor); HEMIS'da alohida "unvon" maydoni yo'q */
  position: HemisRef
  /** HEMIS employmentForm: "Asosiy ish joy", "O'rindoshlik (ichki-asosiy)" … */
  form?: HemisRef | null
  /** Stavka: 1, 0.5 … */
  rate?: number | null
  /** HEMIS employeeStatus. Kod 14 — ishdan bo'shagan */
  status?: HemisRef | null
  /** HEMIS employeeType. Kod 10 — "Boshqa" (dashboard'da ko'rsatilmaydi) */
  type?: HemisRef | null
}

/** Ro'yxat kartasi uchun qisqa ma'lumot — HEMIS'dan */
/** Sahifa chaqiruv bloki: sarlavha, matn, tugma yozuvi va havola (tashqi bo'lsa yangi oynada) */
/** Ichki sahifa kartasi: lucide belgi nomi, nom, manzil, hujjatlar */
/** Kartali blok: kirish gapi, raqamlar, ustunlar (raqamli yoki ✓ belgili bandlar: nom + ixtiyoriy izoh), xulosa gapi */
export interface PageShowcase {
  n: number
  intro: string | null
  stats: { value: string; label: string }[]
  columns: { title: string; icon: string | null; style: 'numbers' | 'checks'; items: { name: string; note: string | null }[] }[]
  outro: string | null
  /** Blok suratlari: url — katta, thumb — kichik nusxa */
  photos: { url: string; thumb: string; alt: string; width?: number | null; height?: number | null }[]
  /** Suratlar slayderda (bittadan, ← 1 2 3 →) */
  slider?: boolean
  /** Havolali kartalar: rasm + nom, bosilsa sahifaga */
  cards?: { title: string; url: string; photo: string | null }[]
}

export interface PageChild {
  slug: string
  title: string
  icon: string | null
  url: string
  attachments: Attachment[]
}

export interface PageCta {
  title: string | null
  text: string | null
  label: string
  url: string
}

/** Sahifadagi bo'lim xodimi kartasi: telefon / e-pochta / qabul kunlari kiritilmagan bo'lsa null */
export interface PageStaff extends StaffSummary {
  position: string | null
  phone: string | null
  email: string | null
  hours: string | null
}

export interface StaffSummary {
  /** Saytdagi xodim ID'si (uzswlu.uz/teacher/7731 dagi kabi) */
  id: string
  /** HEMIS'dagi ism, tartibi o'zgarishsiz: "IBRAGIMOV OTABEK" yoki "TUXTASINOV ILXOMJON MADAMINOVICH" */
  name: string
  /** Sharif (HEMIS `patronymic`). `name` da bo'lmasa frontend oxiriga qo'shadi; vizitkada alohida qatorda chiqadi */
  patronymic?: string | null
  /** Ko'rsatiladigan surat: xodim saytga o'zi yuklagan bo'lsa — o'shasi, aks holda HEMIS surati */
  photo?: string | null
  /** O'z surati ochilmasa ishlatiladigan HEMIS surati (ikkalasi ham bo'lmasa — bosh harflar) */
  photoFallback?: string | null
  /** HEMIS ish joylari (bo'lim + lavozim), HEMIS tartibida */
  employments: HemisEmployment[]
  /** Ro'yxat filtri uchun guruh — asosiy ish joyi bo'limining turidan (HEMIS structureType) */
  group: StaffGroup
}

/** GET /staff?lang=&q=&department=&group=&page=&perPage= — xodimlar ro'yxati */
export interface StaffList {
  items: StaffSummary[]
  /** Filtrlangan natijalar soni */
  total: number
  page: number
  perPage: number
  /** Har bir guruhdagi xodimlar soni (q va department hisobga olinadi, group — yo'q) */
  groups: Record<'all' | StaffGroup, number>
  /** Bo'lim tanlash ro'yxati, nom bo'yicha tartiblangan */
  departments: StaffDepartment[]
  /** Filtrsiz umumiy sonlar (sahifa sarlavhasidagi statistika) */
  summary: { staff: number; departments: number }
}

/** Aloqa turlari (oldingi saytdagi dashboard maydonlari): office — "Qabul joyi" (manzil, xaritada ochiladi) */
export type StaffContactType = 'email' | 'telegram' | 'whatsapp' | 'mobile' | 'phone' | 'office'
export type StaffNetwork = 'instagram' | 'threads' | 'facebook' | 'linkedin' | 'x' | 'youtube'
export type StaffScienceNetwork = 'orcid' | 'scholar' | 'scopus' | 'researchgate'
/** Staff sahifasida chiqishi mumkin bo'lgan hujjat bo'limlari (Taqdimotlar va Videolar — faqat dashboard'da) */
export type StaffDocSection = 'cv' | 'books' | 'articles'

/**
 * GET /staff/:id?lang= — xodim profili (faqat ko'rish).
 * Ism, surat, bo'lim va lavozim HEMIS'dan; qolganini xodimning o'zi saytga kirib,
 * dashboard sahifasida qo'shadi va o'zgartiradi. Bo'sh maydonlar umuman yuborilmaydi/chiqmaydi.
 */
export interface StaffProfile extends StaffSummary {
  /** "Xodim haqida" — so'ralgan tilda (uz/ru/en/zh), tarjima bo'lmasa o'zbekchasi; kiritilmagan bo'lsa null */
  about?: string | null
  /** Aloqa: faqat xodim to'ldirganlari, ko'rsatish tartibida. E-pochta bir nechta bo'lishi mumkin */
  contacts: { type: StaffContactType; value: string }[]
  /** Ijtimoiy tarmoqlar: faqat to'ldirilganlari */
  socials: { network: StaffNetwork; url: string }[]
  /** Ilmiy profillar: faqat to'ldirilganlari */
  science: { network: StaffScienceNetwork; url: string }[]
  /** Hujjatlar: faqat xodim "Staff'da ko'rinadi" qoldirgan (boshlanishida ochiq) va bo'sh bo'lmagan bo'limlar; sarlavha so'ralgan tilda */
  documents: { section: StaffDocSection; items: { title: string; url: string }[] }[]
  /** Server yaratgan vizitka rasmi (PNG) — "rasm sifatida yuklab olish" uchun, ixtiyoriy */
  cardImage?: string | null
}

/** Xodim kabinetidagi barcha hujjat bo'limlari (Taqdimotlar va Videolar faqat kabinetda) */
export type CabinetDocSection = StaffDocSection | 'presentations' | 'videos'

/** 4 tildagi matn (xodim kiritadi; bo'sh tillar uchun o'zbekchasi ishlatiladi) */
export interface LocalizedText {
  uz: string
  ru: string
  en: string
  zh: string
}

/** Kabinetdagi bitta hujjat (ro'yxat va yuklash oynasi uchun) */
export interface CabinetDocument {
  id: string
  /** Nomi 4 tilda; zh bo'sh bo'lsa en, u ham bo'sh bo'lsa uz ko'rsatiladi */
  title: LocalizedText
  /** Fayl havolasi (videolarda — tashqi havola) */
  url: string
  /** ISO sana */
  createdAt: string
}

/**
 * GET /me — xodim kabineti (dashboard). Faqat saytga HEMIS (my.gov) orqali kirgan xodimga;
 * kirmagan bo'lsa 401. Ism, sharif, tug'ilgan kun, telefon, e-pochta, ish joylari — HEMIS'dan (faqat o'qish).
 */
/** Kabinet roli: HEMIS lavozimidan avtomatik (dekan > kafedra mudiri > o'qituvchi > xodim); talaba — HEMIS talaba kirishi ulanganda */
/** GET /me/notifications — kabinet qo'ng'iroqchasi (faqat o'z bildirishnomalari) */
export interface CabinetNotification {
  id: number
  kind: 'role' | 'post' | 'application' | 'security' | 'system'
  title: string
  body: string | null
  link: string | null
  read: boolean
  createdAt: string
}

export interface CabinetNotifications {
  unread: number
  docs: CabinetNotification[]
  /** Sayt serveri qo'shadi: xodim kirganmi (mehmonda false — qo'ng'iroqcha chiqmaydi) */
  signedIn?: boolean
}

export interface CabinetAdminSection {
  key: string
  label: string
  group: string
  level: 'read' | 'write'
  /** Aniq amallar: read (ko'rish), create (qo'shish), update (tahrirlash), delete (o'chirish) */
  actions?: ('read' | 'create' | 'update' | 'delete')[]
}

export interface CabinetAdminLink {
  available: boolean
  url: string | null
  /** Admin paneldagi rol nomi */
  role: string | null
  /** Rolga ruxsat etilgan bo'limlar (admin yon menyusidagi tartibda) */
  sections: CabinetAdminSection[]
  /** Sayt serveri qo'shadi: xodim kabinetga kirganmi (mehmonda false) */
  signedIn?: boolean
  /** `?list=1` da: shu xodim yozgan postlar (kabinet bosh sahifasidagi rol paneli) */
  stats?: { published: number, drafts: number, month: number }
}

export type CabinetRole = 'dean' | 'chair_head' | 'teacher' | 'staff' | 'student'

export interface CabinetPanel {
  position: string
  department: string
  /** Dekan uchun: fakultet ko'rsatkichlari va kafedralar */
  faculty?: {
    slug: string
    name: string
    stats: { students?: number; departments?: number; programs?: number; teachers?: number }
    chairs: { id: string; name: string; staffCount: number }[]
  }
  /** Kafedra mudiri uchun: kafedra xodimlari */
  team?: { count: number; members: { id: string; name: string; position: string; photo?: string | null }[] }
}

export interface StaffCabinet {
  role: CabinetRole
  panel: CabinetPanel
  /** Ommaviy profil (Staff sahifasidagi bilan bir xil ko'rinish uchun) */
  profile: StaffProfile
  hemis: {
    firstName: string
    lastName: string
    patronymic?: string | null
    /** ISO sana */
    birthDate?: string | null
    phone?: string | null
    email?: string | null
  }
  /** "Xodim haqida" 4 tilda (tahrirlash uchun) */
  about: LocalizedText
  /** Xodimning o'zi yuklagan surat bormi (✕ — HEMIS suratiga qaytarish faqat shunda chiqadi) */
  hasOwnPhoto: boolean
  /** Superadmin bergan rol bormi (Foydalanuvchilar → rol + HEMIS ID). Yo'q bo'lsa — faqat Dashboard va KPI, hech narsa o'zgartirilmaydi */
  hasRole?: boolean
  /** Hujjat bo'limlari: soni va Staff'da ko'rinishi (cv/books/articles; boshida ochiq) */
  documents: Record<CabinetDocSection, CabinetDocStat>
}

export interface CabinetDocStat {
  count: number
  /** Staff sahifasida ko'rinadimi (presentations/videos uchun doim false) */
  visible: boolean
}

/** PATCH /me — o'zgartirilgan qismlarni yuboriladi; javob — yangilangan StaffCabinet */
export interface CabinetPatch {
  about?: LocalizedText
  contacts?: StaffProfile['contacts']
  socials?: StaffProfile['socials']
  science?: StaffProfile['science']
  visibility?: Partial<Record<StaffDocSection, boolean>>
}

/** «Tezkor xizmatlar» kartasi: `external` — tashqi havola (yangi oynada ochiladi) */
export interface QuickLinkItem {
  id: string
  icon: string
  url: string
  external: boolean
  title: string
  text?: string | null
}

/** Bosh sahifadagi video tur: `url` — ko'mish (iframe/video) manzili */
export interface HomeVideoTour {
  kind: 'youtube' | 'vimeo' | 'file'
  url: string
  poster?: string | null
  title?: string | null
  text?: string | null
}

/** GET /site?lang= — har bir sahifada kerak bo'ladigan umumiy ma'lumot (menyu, footer, kontaktlar) */
export interface SiteData {
  /** Asosiy menyu, ko'rsatish tartibida (admin panelda boshqariladi) */
  menu: MenuGroup[]
  phone: string
  phoneExt: string
  emails: string[]
  campuses: Campus[]
  socials: SocialLink[]
  /** Chap panelda «O'quv binolari» belgisi (admin panelda yoqiladi/o'chiriladi); berilmasa — ko'rsatiladi */
  showBuildings?: boolean
  /** Faol qabul yili (admin → Qabul yillari), masalan "2026/2027" */
  admissionYear?: string
  /** Davlat ramzlari (bosh sahifa bloki va footer) — admin panelda boshqariladi; berilmasa saytdagi standart havolalar */
  symbols?: StateSymbol[] | null
  /** «Davlat ramzlari» orqa foni (bayroq va gerb) — admin panelda yoqiladi/yashiriladi; berilmasa ko'rsatiladi */
  symbolsBackground?: boolean
}

/** Davlat ramzi: bayroq, gerb yoki madhiya */
export interface StateSymbol {
  key: 'flag' | 'emblem' | 'anthem'
  title: string
  /** Qisqa tavsif (ixtiyoriy) */
  description?: string | null
  image?: string | null
  /** Madhiya audio fayli (MP3) */
  audio?: string | null
  /** Rasmiy manba sahifasi (archive.uz, YouTube) */
  href?: string | null
  /** Manba nomi: "archive.uz" */
  source?: string | null
}

// ─── Ichki sahifalar ────────────────────────────────────────────────────────

/** Biriktirilgan fayl yoki havola (sahifa, hujjat ro'yxati, BRM) */
export interface Attachment {
  title: string
  url: string
  /** pdf — fayl (yuklab olinadi), link — tashqi sahifa */
  kind: 'pdf' | 'link'
  /** Qo'shimcha izoh: "PDF · 2.4 MB", "22.02.2023", "inglizcha" */
  meta?: string | null
  /**
   * PDF saytda qanday ko'rinadi (admin tanlaydi): embed — ichi ko'rinadi (o'z ramkasida aylantiriladi),
   * open — karta, yangi oynada ochiladi, download — karta, yuklab olinadi,
   * link — matn ostida faqat nomi (masalan, "AVTOREFERAT"). Berilmasa — open.
   */
  display?: 'embed' | 'open' | 'download' | 'link' | null
  /** embed uchun ramka balandligi, px (480 / 680 / 880) */
  height?: number | null
}

/**
 * GET /pages/:slug?lang= — oddiy matnli sahifa (Universitet haqida, Tuzilma, Stipendiyalar …).
 * Yon menyu va "Oldingi/Keyingi" frontend'da GET /site menyusidan hisoblanadi.
 */
export interface ContentPage {
  slug: string
  title: string
  /** Sarlavha ostidagi qisqa kirish matni */
  lead?: string | null
  parent?: { title: string; url: string; cards: { title: string; url: string; photo: string | null }[]; trail?: { title: string; url: string }[] } | null
  /** Raqamlar qatori (ixtiyoriy): [{ value: "23 168", label: "talaba" }] */
  facts: { value: string; label: string }[]
  /**
   * Sahifa matni — HTML. Ruxsat etilgan teglar: h2, h3, p, ul, ol, li, a, strong, em, blockquote, figure, img, figcaption, table.
   * Backend tozalab (sanitize) beradi; frontend uni shu ko'rinishda chiqaradi.
   */
  body: string
  /**
   * Vaqt chizig'i (ixtiyoriy): [{ label: "1949", text: "…" }]; highlight — ajratilgan (to'q) karta.
   * body ichida `<!-- timeline -->` belgisi bo'lsa — shu joyga, bo'lmasa matndan keyin qo'yiladi.
   */
  timeline: { label: string; text: string; highlight?: boolean }[]
  attachments: Attachment[]
  /** Hujjat uslubi: Times New Roman, sarlavhalar markazda */
  docStyle?: boolean
  /** Bo'limlar kartalari (admin → Bo'limlar), sahifada yoqilgan bo'lsa */
  /** Bo'lim xodimlari — HEMIS'dan avtomatik (admin → Sahifalar'da bo'lim tanlanadi); rahbar birinchi */
  staff?: PageStaff[]
  /** Matndan keyin chaqiruv bloki (admin → Sahifalar); havola va tugma yozuvi bo'lmasa null */
  cta?: PageCta | null
  /** Ichki sahifalar kartalari (admin'da yoqilgan bo'lsa): belgi, nom, hujjatlar */
  children?: PageChild[]
  /** Kartali bloklar — matndagi <!-- showcase:N --> joyida (N — blok raqami) */
  showcase?: PageShowcase[]
  units?: { unit?: string | null; count?: number | null; name?: string | null; position?: string | null; photo?: string | null; phone?: string | null; ext?: string | null; email?: string | null; url?: string | null; source?: 'hemis' | 'admin' }[]
  /** Matndan keyin rektor kartasi (admin: «Matndan keyin rektor kartasi»; ma'lumot — Rahbariyat'dan) */
  rector?: { name: string; role: string; photo?: string | null; hours?: string | null; phone?: string | null; ext?: string | null; email?: string | null } | null
  /** ISO sana-vaqt */
  updatedAt: string
}

/** Yangilik, e'lon yoki tadbir turi (URL: /news/:slug, /announcements/:slug, /events/:slug) */
export type PostType = 'news' | 'announcements' | 'events'

/** Ro'yxatdagi post kartasi (NewsItem bilan mos) */
export interface PostSummary extends NewsItem {
  type: PostType
  /** Qisqa kirish matni (asosiy yangilik kartasida) */
  excerpt?: string | null
}

/** GET /posts?lang=&type=&q=&month=YYYY-MM&sdg=&page=&perPage= — yangiliklar, e'lonlar, tadbirlar ro'yxati */
export interface PostList {
  items: PostSummary[]
  total: number
  page: number
  perPage: number
  /** Har bir tur bo'yicha son (tablar uchun; q, month va sdg hisobga olinadi) */
  counts: Record<PostType, number>
  /** Oy filtri uchun: post bor oylar, yangidan eskiga (YYYY-MM) */
  months: string[]
}

/** Postning bir tildagi varianti: manzil — /{lang}/{type}/{slug} (o'zbekcha — prefikssiz) */
export interface PostTranslation {
  lang: Locale
  image?: string | null
}

/** GET /posts/:type/:slug?lang= — bitta yangilik / e'lon / tadbir */
export interface PostLink {
  slug: string
  title: string
  type: 'news' | 'announcements' | 'events'
}

export interface Post extends PostSummary {
  /** Matn — HTML (ContentPage.body qoidalari bilan) */
  body: string
  /** Kim joylagan — admin'ning HEMIS profilidan avtomatik (avatar: HEMIS surati URL'i) */
  author?: { name: string; role?: string | null; avatar?: string | null } | null
  /** Nashr vaqti, ISO 8601 vaqt mintaqasi bilan: 2026-10-23T19:00:00+05:00 — saytda 24 soatlik formatda (19:00) */
  publishedAt?: string | null
  /**
   * Asosiy surat o'lchami, px — tik yoki yotiqligini bilish uchun (tik surat sarlavha yonida turadi).
   * Backend bermasa, Nuxt serveri faylning o'zidan aniqlaydi
   */
  imageWidth?: number | null
  imageHeight?: number | null
  /**
   * Post qaysi tillarda bor va har tildagi asosiy surat — Telegram'da 4 tildagi havola bilan ulashish uchun.
   * Backend bermasa, Nuxt serveri har tilni so'rab aniqlaydi
   */
  translations?: PostTranslation[]
  /** Galereya rasmlari */
  gallery: string[]
  /** Biriktirilgan PDF'lar (dastur, avtoreferat …) — matn ostida, har biri o'z ko'rinishida */
  attachments?: Attachment[]
  tags: string[]
  /** Taxminiy o'qish vaqti, daqiqa */
  readingMinutes: number
  /** Tadbirlar uchun: boshlanish/tugash vaqti va joyi */
  startsAt?: string | null
  endsAt?: string | null
  location?: string | null
  /** Oldingi (avvalroq) va keyingi (keyinroq) post — shu turdagi */
  prev?: PostLink | null
  next?: PostLink | null
  /** O'xshash postlar (3 ta) */
  related: PostSummary[]
  /** So'nggi postlar (4 ta, yon panel) */
  latest: PostSummary[]
}

/** GET /events?lang=&month=YYYY-MM — tadbirlar taqvimi (oy bo'yicha) */
export interface EventMonth {
  /** YYYY-MM */
  month: string
  /** Shu oydagi tadbirlar, boshlanish vaqti bo'yicha */
  items: EventItem[]
  /** Bugundan keyingi yaqin tadbirlar (3 tagacha) */
  upcoming: EventItem[]
}

/** Rahbar (rektorat sahifasi) */
export interface Leader {
  /** Staff sahifasidagi ID (/teacher/:id), bo'lmasa null */
  staffId?: string | null
  name: string
  role: string
  photo?: string | null
  /** Qabul kunlari: "Dushanba, 15:00–17:00" */
  hours?: string | null
  phone?: string | null
  /** Ichki raqam */
  ext?: string | null
  email?: string | null
}

/** GET /leadership?lang= — rektorat */
export interface Leadership {
  rector: Leader
  prorectors: Leader[]
  /** Matbuot kotibi */
  press?: Leader | null
}

/** Me'yoriy hujjat */
export interface DocumentItem extends Attachment {
  id: string
  /** DocumentList.categories dagi id */
  category: string
}

/** GET /documents?lang= — me'yoriy hujjatlar (ro'yxat to'liq keladi; qidiruv va toifa frontend'da) */
export interface DocumentList {
  categories: { id: string; title: string }[]
  items: DocumentItem[]
}

/** Ta'lim yo'nalishi */
export interface Program {
  id: string
  /** Yo'nalish shifri: 60230100 */
  code: string
  title: string
  /** O'qitiladigan til (bo'lmasa — o'zbek tilida) */
  language?: TaughtLanguage | null
  /** ProgramList.groups dagi id */
  group: string
  /** Ta'lim shakli: "Kunduzgi", "Kechki", "Sirtqi" */
  form: string
  /** O'qish muddati, yil */
  years: number
}

/** GET /programs?lang=&level=bachelor|master — ta'lim yo'nalishlari */
export interface ProgramList {
  level: 'bachelor' | 'master'
  groups: { id: string; title: string }[]
  items: Program[]
}

/** Fakultet kartasi (fakultetlar ro'yxati) */
export interface FacultySummary extends Faculty {
  departments: number
  programs?: number
}

/** GET /faculties?lang= */
export interface FacultyList {
  items: FacultySummary[]
  summary: { faculties: number; departments: number }
}

/** Fakultet xodimi (dekan, dekanat) */
export interface FacultyPerson {
  staffId?: string | null
  name: string
  role: string
  /** Ilmiy daraja, unvon */
  degree?: string | null
  photo?: string | null
}

/** Fakultet ta'lim yo'nalishi (jadval qatori) */
export interface FacultyProgram {
  code: string
  title: string
  level: 'bachelor' | 'master' | 'phd'
  form: string
  years: number
}

/** GET /faculties/:slug?lang= — fakultet sahifasi */
export interface FacultyDetail extends Faculty {
  /** Tartib raqami (1, 2 …) */
  number: number
  about: string
  /** HEMIS'dan */
  stats: { students: number; departments: number; programs: number; teachers: number }
  dean: FacultyPerson & { hours?: string | null; phone?: string | null; email?: string | null }
  programs: FacultyProgram[]
  departments: { id: string; name: string; head?: string | null }[]
  deanery: FacultyPerson[]
  news: PostSummary[]
  contact: { address: string; phone: string; email?: string | null; mapUrl?: string | null; mapEmbed?: string | null }
}

/** GET /admission?lang= — qabul sahifasi */
export interface Admission {
  /** "2026/2027" */
  year: string
  /** true — arxiv yili (/qabul/2025-2026) */
  archived?: boolean
  /** Saytda ko'rinadigan arxiv yillari (yangidan eskiga) */
  archive?: { year: string; slug: string }[]
  /** Onlayn ariza havolasi */
  applyUrl: string
  /** Muhim sanalar; current — hozirgi bosqich */
  dates: { title: string; period: string; current?: boolean }[]
  programs: (FacultyProgram & { id: string; faculty: string; price?: string | null })[]
  documents: string[]
  documentsUrl?: string | null
  faq: { q: string; a: string }[]
  contact: { address: string; hours: string; phone: string; telegram: string }
}

/** Reyting o'rni: "#512" va o'tgan yilga nisbatan o'zgarish (+57) */
export interface RankValue {
  rank: string
  change?: number | null
}

/** BRM maqsadi (ro'yxat) */
export interface SdgGoalSummary {
  /** 1–17 */
  n: number
  /** Sahifa manzili: "/brm-6-toza-suv-va-sanitariya" */
  url: string
  title: string
  /** THE Impact reyting o'rni ("401–600", "30"); ishtirok etmagan bo'lsa null */
  rank?: string | null
  score?: string | null
}

/** GET /sdg?lang= — BRM (barqaror rivojlanish maqsadlari) bosh sahifasi */
export interface SdgOverview {
  greenmetric: {
    year: number
    world: RankValue
    asia: RankValue
    country: RankValue
    /** Ajratilgan natija: "Water yo'nalishi bo'yicha O'zbekistonda #1" */
    highlight?: { text: string; url: string } | null
  }
  /** GreenMetric 6 yo'nalishi; badge — ajratilgan natija ("O'zbekistonda #1") */
  categories: { code: string; title: string; subtitle: string; badge?: string | null; url: string }[]
  /** 17 maqsad, 1 dan 17 gacha */
  goals: SdgGoalSummary[]
  /** THE Impact Rankings yili */
  impactYear: number
  reports: Attachment[]
  /** "Ta'lim va barqarorlik" bloki */
  education: { title: string; text: string; tags: string[]; url: string }
  /** Yashil universitet yangiliklari */
  news: PostSummary[]
}

/** GET /sdg/:n?lang= — BRM maqsad sahifasi. Faoliyat (yangiliklar) — GET /posts?sdg=n */
export interface SdgGoal extends SdgGoalSummary {
  /** BMT maqsadi ta'rifi */
  subtitle: string
  /** Ajratilgan natija kartasi (to'q): GreenMetric va h.k. */
  highlight?: { label: string; value: string } | null
  /** Ichki bo'limlar (tablar): Suvni o'lchash, Suvni tozalash … body — HTML */
  sections: { id: string; title: string; body: string; images: string[] }[]
  documents: Attachment[]
}

/** GET /videos?lang= — video darsliklar */
export interface VideoList {
  live: { isLive: boolean; url: string; next?: { title: string; startsAt: string } | null }
  channelUrl: string
  /** greeting — kartadagi bezak so'z ("Hello", "你好"), lang — uning tili */
  categories: { id: string; title: string; greeting: string; lang: string }[]
  items: { id: string; category: string; title: string; teacher?: string | null; duration?: string | null; url: string; thumbnail?: string | null }[]
}

/** GET /contact?lang= — aloqa sahifasi */
export interface ContactPage {
  hotline: { phone: string; ext?: string | null }
  emails: { title: string; value: string; extra: string[] }[]
  /** Binolar (bosh sahifadagi «Biz bilan bog'lanish» kartalari ham) — admin panel: Sozlamalar → Binolar va xarita.
   * mapEmbed — sahifadagi kichik xarita (iframe), mapUrl — «Xaritada ochish» */
  campuses: (Campus & { phone: string; email?: string | null; mapUrl: string; mapEmbed?: string | null; logo?: string | null })[]
  leaders: { name: string; role: string; ext: string; phone: string }[]
  /** Telefonlar ma'lumotnomasi (admin → Telefonlar): section=true — bo'lim sarlavhasi (position matni) */
  phones?: { section: boolean; name?: string | null; position: string; ext?: string | null; phone?: string | null }[]
  /** Murojaatda taqiqlangan so'zlar (admin → Haqoratli so'zlar): «*» — so'z boshi */
  rudeWords?: string[]
  reception: string
  /** Virtual qabulxona: "Kimga" ro'yxati */
  recipients: { id: string; title: string }[]
}

/** POST /appeals — virtual qabulxona murojaati (multipart: name, phone, email, recipient, message, consent, file?) */
export interface AppealResult {
  /** Murojaat raqami — foydalanuvchiga ko'rsatiladi */
  number: string
}

/** Qidiruv natijasi turi */
/** pages — sahifalar, fakultetlar, kafedralar, yo'nalishlar, video darslar; people — rahbariyat va xodimlar */
export type SearchKind = 'pages' | 'news' | 'documents' | 'people'

/** GET /search?lang=&q=&type=&page= — sayt bo'yicha qidiruv */
export interface SearchResults {
  q: string
  counts: Record<SearchKind, number>
  /** Tezkor javob — so'rovga eng mos sahifa (ixtiyoriy) */
  quick?: { title: string; text: string; url: string } | null
  /**
   * excerpt — oddiy matn (HTML emas); topilgan so'zni frontend o'zi ajratib ko'rsatadi.
   * meta — qisqa izoh: sahifa uchun menyu bo'limi, yangilik uchun toifa, hujjat uchun "PDF"
   */
  items: { kind: SearchKind; title: string; url: string; excerpt?: string | null; meta: string; date?: string | null }[]
  total: number
  page: number
  perPage: number
}

/** Kabinetdan boshqariladigan post (yangilik / e'lon / tadbir) — panel javobining kerakli qismi */
export interface CabinetPostDoc {
  id: number
  type: 'news' | 'announcements' | 'events'
  title: Partial<Record<'uz' | 'ru' | 'en' | 'zh', string>>
  excerpt: Partial<Record<'uz' | 'ru' | 'en' | 'zh', string>>
  body: Partial<Record<'uz' | 'ru' | 'en' | 'zh', string>>
  location: Partial<Record<'uz' | 'ru' | 'en' | 'zh', string>>
  status: 'draft' | 'published'
  slug: string | null
  cover: { id: number, url: string } | null
  publishedAt: string | null
  startsAt: string | null
  endsAt: string | null
  /** Shu xodim tahrirlay/o'chira oladimi */
  own: boolean
}

export interface CabinetPostList {
  docs: CabinetPostDoc[]
  totalDocs: number
  totalPages: number
  page: number
}
