import type { HomeData, SiteData } from '#shared/types/api'

// VAQTINCHALIK MA'LUMOT — backend tayyor bo'lguncha.
// O'zbekcha matnlar uzswlu.uz'dan olingan (2026-10-20 holatiga).
// ru/en/zh tarjimalari, yangilik toifalari va tillar ro'yxati tekshirilishi kerak.

type L = Record<Locale, string>

const faculties: { slug: string; name: L }[] = [
  { slug: 'english-philology', name: { uz: 'Ingliz filologiyasi fakulteti', ru: 'Факультет английской филологии', en: 'Faculty of English Philology', zh: '英语语文学院' } },
  { slug: 'english-1', name: { uz: 'Ingliz tili №1 fakulteti', ru: 'Факультет английского языка №1', en: 'Faculty of English Language No. 1', zh: '第一英语学院' } },
  { slug: 'english-2', name: { uz: 'Ingliz tili №2 fakulteti', ru: 'Факультет английского языка №2', en: 'Faculty of English Language No. 2', zh: '第二英语学院' } },
  { slug: 'english-3', name: { uz: 'Ingliz tili №3 fakulteti', ru: 'Факультет английского языка №3', en: 'Faculty of English Language No. 3', zh: '第三英语学院' } },
  { slug: 'russian-philology', name: { uz: 'Rus filologiyasi fakulteti', ru: 'Факультет русской филологии', en: 'Faculty of Russian Philology', zh: '俄语语文学院' } },
  { slug: 'romance-germanic', name: { uz: 'Roman-german filologiyasi fakulteti', ru: 'Факультет романо-германской филологии', en: 'Faculty of Romance and Germanic Philology', zh: '罗曼-日耳曼语文学院' } },
  { slug: 'oriental-philology', name: { uz: 'Sharq filologiyasi fakulteti', ru: 'Факультет восточной филологии', en: 'Faculty of Oriental Philology', zh: '东方语文学院' } },
  { slug: 'international-journalism', name: { uz: 'Xalqaro jurnalistika fakulteti', ru: 'Факультет международной журналистики', en: 'Faculty of International Journalism', zh: '国际新闻学院' } },
  { slug: 'translation', name: { uz: 'Tarjimonlik fakulteti', ru: 'Переводческий факультет', en: 'Faculty of Translation', zh: '翻译学院' } },
  { slug: 'distance-evening', name: { uz: 'Sirtqi va kechki ta’lim fakulteti', ru: 'Факультет заочного и вечернего обучения', en: 'Faculty of Distance and Evening Education', zh: '函授与夜间教育学院' } },
  { slug: 'joint-programs', name: { uz: 'Qo‘shma ta’lim dasturlarini muvofiqlashtirish bo‘limi', ru: 'Отдел координации совместных образовательных программ', en: 'Joint Programmes Coordination Office', zh: '合作办学项目协调处' } },
]

// Karusel bannerlari uzswlu.uz'dan olingan (1920px WebP'ga siqilgan): public/slides/
const slides: { image: string; alt: L }[] = [
  {
    image: '/slides/slide-1.webp',
    alt: { uz: 'Özbekiston Respublikasi davlat mustaqilligiga 35 yil', ru: '35 лет государственной независимости Республики Узбекистан', en: '35 years of independence of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国独立35周年' },
  },
  {
    image: '/slides/slide-2.webp',
    alt: { uz: 'UI GreenMetric 2026: dunyoda 512-, Osiyoda 296-, Özbekistonda 11-örin', ru: 'UI GreenMetric 2026: 512-е место в мире, 296-е в Азии, 11-е в Узбекистане', en: 'UI GreenMetric 2026: 512th in the world, 296th in Asia, 11th in Uzbekistan', zh: 'UI GreenMetric 2026：全球第512名，亚洲第296名，乌兹别克斯坦第11名' },
  },
  {
    image: '/slides/slide-3.webp',
    alt: { uz: 'QS by Subject 2025 (lingvistika, 251–300) va UI GreenMetric 2024 sertifikatlari', ru: 'Сертификаты QS by Subject 2025 (лингвистика, 251–300) и UI GreenMetric 2024', en: 'QS by Subject 2025 (Linguistics, 251–300) and UI GreenMetric 2024 certificates', zh: 'QS学科排名2025（语言学，251–300）及UI GreenMetric 2024证书' },
  },
  {
    image: '/slides/slide-4.webp',
    alt: { uz: 'Higher Education Ranking 2026: dunyoda 119-, Özbekistonda 12-örin', ru: 'Higher Education Ranking 2026: 119-е место в мире, 12-е в Узбекистане', en: 'Higher Education Ranking 2026: 119th in the world, 12th in Uzbekistan', zh: 'Higher Education Ranking 2026：全球第119名，乌兹别克斯坦第12名' },
  },
  {
    image: '/slides/slide-5.webp',
    alt: { uz: 'QS WUR by Subject 2025: lingvistika yönalişida 251–300-örin', ru: 'QS WUR by Subject 2025: 251–300 место по лингвистике', en: 'QS WUR by Subject 2025: Linguistics 251–300', zh: 'QS学科排名2025：语言学251–300名' },
  },
  {
    image: '/slides/slide-6.webp',
    alt: { uz: 'QS WUR by Subject 2026: lingvistika 201–250, zamonaviy tillar 301–350', ru: 'QS WUR by Subject 2026: лингвистика 201–250, современные языки 301–350', en: 'QS WUR by Subject 2026: Linguistics 201–250, Modern Languages 301–350', zh: 'QS学科排名2026：语言学201–250名，现代语言301–350名' },
  },
  {
    image: '/slides/slide-7.webp',
    alt: { uz: 'THE Impact Rankings 2025 natijalari', ru: 'Результаты THE Impact Rankings 2025', en: 'THE Impact Rankings 2025 results', zh: 'THE影响力排名2025结果' },
  },
]

// Hamkorlar logolari uzswlu.uz'dan olingan: public/logos/partners/
const partners: { logo: string; name: L }[] = [
  { logo: 'partner-1', name: { uz: 'AQŞning Toşkentdagi elçixonasi', ru: 'Посольство США в Ташкенте', en: 'U.S. Embassy in Tashkent', zh: '美国驻塔什干大使馆' } },
  { logo: 'partner-2', name: { uz: 'British Council (IELTS)', ru: 'Британский совет (IELTS)', en: 'British Council (IELTS)', zh: '英国文化协会（IELTS）' } },
  { logo: 'partner-3', name: { uz: 'Dalian texnologiya universiteti', ru: 'Даляньский технологический университет', en: 'Dalian University of Technology', zh: '大连理工大学' } },
  { logo: 'partner-4', name: { uz: 'Özbekiston Respublikasi Mudofaa vazirligi', ru: 'Министерство обороны Республики Узбекистан', en: 'Ministry of Defence of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国国防部' } },
  { logo: 'partner-5', name: { uz: 'KOICA', ru: 'KOICA', en: 'KOICA', zh: '韩国国际协力团（KOICA）' } },
  { logo: 'partner-6', name: { uz: 'Mirzo Uluğbek nomidagi Özbekiston Milliy universiteti', ru: 'Национальный университет Узбекистана имени Мирзо Улугбека', en: 'National University of Uzbekistan', zh: '乌兹别克斯坦国立大学' } },
  { logo: 'partner-7', name: { uz: 'Toşkent davlat şarqşunoslik universiteti', ru: 'Ташкентский государственный университет востоковедения', en: 'Tashkent State University of Oriental Studies', zh: '塔什干国立东方大学' } },
  { logo: 'partner-8', name: { uz: 'Alliance Française', ru: 'Alliance Française', en: 'Alliance Française', zh: '法语联盟' } },
  { logo: 'partner-9', name: { uz: 'DAAD', ru: 'DAAD', en: 'DAAD — German Academic Exchange Service', zh: '德国学术交流中心（DAAD）' } },
  { logo: 'partner-10', name: { uz: 'LAMDIK', ru: 'LAMDIK', en: 'LAMDIK', zh: 'LAMDIK' } },
]

const campuses: { id: string; name: L; address: L }[] = [
  {
    id: 'main',
    name: { uz: 'Bosh bino', ru: 'Главный корпус', en: 'Main building', zh: '主楼' },
    address: { uz: 'Toshkent sh., Kichik halqa yo‘li ko‘chasi, G9-A, 21-uy', ru: 'г. Ташкент, ул. Кичик халка йули, G9-A, д. 21', en: '21 Kichik Halqa Yo‘li St, G9-A, Tashkent', zh: '塔什干市 Kichik Halqa Yo‘li 街 G9-A 21号' },
  },
  {
    id: 'philology',
    name: { uz: 'Filologiya fakulteti', ru: 'Факультет филологии', en: 'Philology building', zh: '语文学院楼' },
    address: { uz: 'Toshkent sh., Uchtepa tumani, Zakovat ko‘chasi, 4', ru: 'г. Ташкент, Учтепинский р-н, ул. Заковат, 4', en: '4 Zakovat St, Uchtepa district, Tashkent', zh: '塔什干市 Uchtepa 区 Zakovat 街4号' },
  },
  {
    id: 'journalism',
    name: { uz: 'Xalqaro jurnalistika', ru: 'Международная журналистика', en: 'International Journalism', zh: '国际新闻学院楼' },
    address: { uz: 'Toshkent sh., Chilonzor tumani, Lutfiy ko‘chasi, 8', ru: 'г. Ташкент, Чиланзарский р-н, ул. Лутфий, 8', en: '8 Lutfiy St, Chilanzar district, Tashkent', zh: '塔什干市 Chilonzor 区 Lutfiy 街8号' },
  },
  {
    id: 'russian',
    name: { uz: 'Rus filologiyasi', ru: 'Русская филология', en: 'Russian Philology', zh: '俄语语文学院楼' },
    address: { uz: 'Toshkent sh., Chilonzor tumani, Muqimiy ko‘chasi, 104', ru: 'г. Ташкент, Чиланзарский р-н, ул. Мукими, 104', en: '104 Muqimiy St, Chilanzar district, Tashkent', zh: '塔什干市 Chilonzor 区 Muqimiy 街104号' },
  },
]

// Tekshirish kerak: universitetda o'qitiladigan tillarning aniq ro'yxati backend'dan keladi
const languages = [
  { code: 'en', native: 'English' },
  { code: 'de', native: 'Deutsch' },
  { code: 'fr', native: 'Français' },
  { code: 'es', native: 'Español' },
  { code: 'it', native: 'Italiano' },
  { code: 'ru', native: 'Русский' },
  { code: 'zh', native: '中文' },
  { code: 'ja', native: '日本語' },
  { code: 'ko', native: '한국어' },
  { code: 'ar', native: 'العربية' },
  { code: 'tr', native: 'Türkçe' },
  { code: 'fa', native: 'فارسی' },
]

export function getMockHome(lang: Locale): HomeData {
  return {
    slides: slides.map((s, i) => ({ id: String(i + 1), image: s.image, alt: s.alt[lang], link: null })),
    // Haqiqiy integratsiyada bu raqamlar HEMIS'dan keladi
    stats: [
      { key: 'faculties', value: 11 },
      { key: 'staff', value: 1100 },
      { key: 'departments', value: 47 },
      { key: 'students', value: 17000 },
    ],
    faculties: faculties.map((f, i) => ({
      id: String(i + 1),
      slug: f.slug,
      name: f.name[lang],
      // Logolar uzswlu.uz'dan olingan: public/logos/faculties/<slug>.webp
      logo: `/logos/faculties/${f.slug}.webp`,
    })),
    // Yangiliklar, e'lonlar va tadbirlar — mock-posts.ts dan (ichki sahifalar bilan bir xil)
    news: getMockLatest(lang, 'news', 4),
    announcements: getMockLatest(lang, 'announcements', 4).map(({ id, slug, date, title }) => ({ id, slug, date, title })),
    events: getMockUpcomingEvents(lang, 3),
    languages,
    partners: partners.map((p, i) => ({ id: String(i + 1), name: p.name[lang], logo: `/logos/partners/${p.logo}.webp`, url: null })),
    updatedAt: new Date().toISOString(),
  }
}

export function getMockSite(lang: Locale): SiteData {
  return {
    menu: getMockMenu(lang),
    phone: '+998 71 230 13 73',
    phoneExt: '1061–1064',
    emails: ['uzdjtu@uzswlu.uz', 'international@uzswlu.uz'],
    campuses: campuses.map(c => ({ id: c.id, name: c.name[lang], address: c.address[lang] })),
    socials: [
      { network: 'telegram', url: 'https://t.me/UzSWLU' },
      { network: 'instagram', url: 'https://www.instagram.com/uzswlu_official' },
      { network: 'facebook', url: 'https://www.facebook.com/uzswlu.uz' },
      { network: 'youtube', url: 'https://www.youtube.com/c/Ozbekistondavlatjahontillariuniversiteti' },
      { network: 'x', url: 'https://www.twitter.com/uzswlu' },
    ],
  }
}
