import type { Admission, FacultyDetail, FacultyList, FacultyProgram, ProgramList } from '#shared/types/api'

// VAQTINCHALIK MA'LUMOT — ta'lim yo'nalishlari, fakultetlar va qabul (backend tayyor bo'lguncha).
// Bakalavriat ro'yxati uzswlu.uz/bakalavriat sahifasidan (kunduzgi, 2026-10-21).
// Fakultet sahifasidagi raqamlar, dekan va kafedralar — NAMUNA (haqiqiysi HEMIS'dan keladi).

type L = Record<Locale, string>

const FORM = {
  day: { uz: 'Kunduzgi', ru: 'Очная', en: 'Full-time', zh: '全日制' },
  evening: { uz: 'Keçki', ru: 'Вечерняя', en: 'Evening', zh: '夜校' },
  distance: { uz: 'Sirtqi', ru: 'Заочная', en: 'Distance', zh: '函授' },
} satisfies Record<string, L>

const languages: Record<string, { code: string; native: string }> = {
  ingliz: { code: 'en', native: 'English' },
  nemis: { code: 'de', native: 'Deutsch' },
  fransuz: { code: 'fr', native: 'Français' },
  ispan: { code: 'es', native: 'Español' },
  xitoy: { code: 'zh', native: '中文' },
  yapon: { code: 'ja', native: '日本語' },
  koreys: { code: 'ko', native: '한국어' },
  arab: { code: 'ar', native: 'العربية' },
  turk: { code: 'tr', native: 'Türkçe' },
  rus: { code: 'ru', native: 'Русский' },
  italyan: { code: 'it', native: 'Italiano' },
}

const titles: Record<string, L> = {
  '60110700': { uz: 'O‘zbek tili va adabiyoti', ru: 'Узбекский язык и литература', en: 'Uzbek Language and Literature', zh: '乌兹别克语言文学' },
  '60110800': { uz: 'Ona tili va adabiyoti (rus tili va adabiyoti)', ru: 'Родной язык и литература (русский язык и литература)', en: 'Native Language and Literature (Russian)', zh: '母语与文学（俄语语言文学）' },
  '60110900': { uz: 'Xorijiy til va adabiyoti', ru: 'Иностранный язык и литература', en: 'Foreign Language and Literature', zh: '外国语言文学' },
  '60230100': { uz: 'Filologiya va tillarni o‘qitish', ru: 'Филология и преподавание языков', en: 'Philology and Language Teaching', zh: '语文学与语言教学' },
  '60230200': { uz: 'Tarjima nazariyasi va amaliyoti', ru: 'Теория и практика перевода', en: 'Translation Theory and Practice', zh: '翻译理论与实践' },
  '60230400': { uz: 'Kompyuter lingvistikasi', ru: 'Компьютерная лингвистика', en: 'Computational Linguistics', zh: '计算语言学' },
  '60310100': { uz: 'Siyosatshunoslik', ru: 'Политология', en: 'Political Science', zh: '政治学' },
  '60310400': { uz: 'Sotsiologiya', ru: 'Социология', en: 'Sociology', zh: '社会学' },
  '60310200': { uz: 'Xalqaro munosabatlar', ru: 'Международные отношения', en: 'International Relations', zh: '国际关系' },
  '60320100': { uz: 'Jurnalistika (xalqaro jurnalistika)', ru: 'Журналистика (международная журналистика)', en: 'Journalism (International Journalism)', zh: '新闻学（国际新闻）' },
  '60320200': { uz: 'Axborot xizmati va jamoatchilik bilan aloqalar', ru: 'Информационная служба и связи с общественностью', en: 'Information Services and Public Relations', zh: '信息服务与公共关系' },
}

const bachelorGroups: Record<string, L> = {
  phil: { uz: 'Filologiya va tillarni öqitiş', ru: 'Филология и преподавание языков', en: 'Philology and teaching', zh: '语文学与语言教学' },
  tr: { uz: 'Tarjima', ru: 'Перевод', en: 'Translation', zh: '翻译' },
  lit: { uz: 'Til va adabiyot', ru: 'Язык и литература', en: 'Language and literature', zh: '语言文学' },
  soc: { uz: 'Ijtimoiy fanlar va jurnalistika', ru: 'Социальные науки и журналистика', en: 'Social sciences and journalism', zh: '社会科学与新闻' },
}

const bachelor: [string, string | null, string][] = [
  ['60110700', null, 'lit'],
  ['60110800', 'rus', 'lit'],
  ['60110900', 'ingliz', 'lit'],
  ...['ingliz', 'nemis', 'fransuz', 'ispan', 'xitoy', 'yapon', 'koreys', 'arab', 'turk', 'rus'].map(l => ['60230100', l, 'phil'] as [string, string, string]),
  ...['ingliz', 'nemis', 'fransuz', 'italyan', 'arab', 'turk'].map(l => ['60230200', l, 'tr'] as [string, string, string]),
  ['60230400', null, 'soc'],
  ['60310100', null, 'soc'],
  ['60310400', null, 'soc'],
  ['60310200', null, 'soc'],
  ['60320100', null, 'soc'],
  ['60320200', null, 'soc'],
]

// NAMUNA — magistratura mutaxassisliklari ro'yxati backend'dan keladi
const masterGroups: Record<string, L> = {
  ling: { uz: 'Lingvistika', ru: 'Лингвистика', en: 'Linguistics', zh: '语言学' },
  tr: { uz: 'Tarjima', ru: 'Перевод', en: 'Translation', zh: '翻译' },
  soc: { uz: 'Ijtimoiy fanlar va jurnalistika', ru: 'Социальные науки и журналистика', en: 'Social sciences and journalism', zh: '社会科学与新闻' },
}

const masterTitles: Record<string, L> = {
  '70230101': { uz: 'Lingvistika (ingliz tili)', ru: 'Лингвистика (английский язык)', en: 'Linguistics (English)', zh: '语言学（英语）' },
  '70230102': { uz: 'Lingvistika (nemis tili)', ru: 'Лингвистика (немецкий язык)', en: 'Linguistics (German)', zh: '语言学（德语）' },
  '70230103': { uz: 'Lingvistika (şarq tillari)', ru: 'Лингвистика (восточные языки)', en: 'Linguistics (Oriental languages)', zh: '语言学（东方语言）' },
  '70230201': { uz: 'Tarjima nazariyasi va amaliyoti', ru: 'Теория и практика перевода', en: 'Translation Theory and Practice', zh: '翻译理论与实践' },
  '70320101': { uz: 'Jurnalistika', ru: 'Журналистика', en: 'Journalism', zh: '新闻学' },
  '70310201': { uz: 'Xalqaro munosabatlar', ru: 'Международные отношения', en: 'International Relations', zh: '国际关系' },
}

const master: [string, string | null, string][] = [
  ['70230101', 'ingliz', 'ling'],
  ['70230102', 'nemis', 'ling'],
  ['70230103', null, 'ling'],
  ['70230201', 'ingliz', 'tr'],
  ['70320101', null, 'soc'],
  ['70310201', null, 'soc'],
]

export function getMockPrograms(lang: Locale, level: 'bachelor' | 'master'): ProgramList {
  const rows = level === 'bachelor' ? bachelor : master
  const names = level === 'bachelor' ? titles : masterTitles
  const groups = level === 'bachelor' ? bachelorGroups : masterGroups
  return {
    level,
    groups: Object.entries(groups).map(([id, title]) => ({ id, title: title[lang] })),
    items: rows.map(([code, language, group], i) => ({
      id: `${level}-${i + 1}`,
      code,
      title: names[code]![lang],
      language: language ? languages[language]! : null,
      group,
      form: FORM.day[lang],
      years: level === 'bachelor' ? 4 : 2,
    })),
  }
}

// ─── Fakultetlar ────────────────────────────────────────────────────────────

// [slug, kafedralar, yo'nalishlar] — sonlar NAMUNA
const facultyCounts: Record<string, [number, number]> = {
  'english-philology': [5, 6],
  'english-1': [4, 3],
  'english-2': [4, 3],
  'english-3': [4, 3],
  'russian-philology': [4, 4],
  'romance-germanic': [6, 8],
  'oriental-philology': [6, 7],
  'international-journalism': [4, 4],
  'translation': [5, 7],
  'distance-evening': [2, 5],
  'joint-programs': [1, 4],
}

export function getMockFaculties(lang: Locale): FacultyList {
  const items = getMockHome(lang).faculties.map(f => ({
    ...f,
    departments: facultyCounts[f.slug]?.[0] ?? 0,
    programs: facultyCounts[f.slug]?.[1] ?? 0,
  }))
  return { items, summary: { faculties: 11, departments: 47 } }
}

const LEVEL: Record<FacultyProgram['level'], number> = { bachelor: 4, master: 2, phd: 3 }

const PLACE: Record<string, L> = {
  degree: { uz: 'Filologiya fanlari doktori, professor', ru: 'Доктор филологических наук, профессор', en: 'Doctor of Philology, Professor', zh: '语文学博士，教授' },
  deputyStudy: { uz: 'Dekan örinbosari (öquv işlari)', ru: 'Заместитель декана по учебной работе', en: 'Deputy Dean for Academic Affairs', zh: '副院长（教学）' },
  deputyYouth: { uz: 'Dekan örinbosari (yoşlar bilan işlaş)', ru: 'Заместитель декана по работе с молодёжью', en: 'Deputy Dean for Youth Affairs', zh: '副院长（青年工作）' },
  methodist: { uz: 'Dekanat uslubçisi', ru: 'Методист деканата', en: 'Dean’s Office Coordinator', zh: '院办教学秘书' },
  dean: { uz: 'Dekan', ru: 'Декан', en: 'Dean', zh: '院长' },
  hours: { uz: 'Seşanba, payşanba · 14:00–16:00', ru: 'Вторник, четверг · 14:00–16:00', en: 'Tue, Thu · 14:00–16:00', zh: '周二、周四 14:00–16:00' },
  about: {
    uz: 'Fakultet ingliz tili va adabiyoti, tilşunoslik va til öqitiş metodikasi böyiça bakalavr, magistr va tadqiqotçilar tayyorlaydi. Tavsif matni admin panel orqali kiritiladi — bu namunaviy matn.',
    ru: 'Факультет готовит бакалавров, магистров и исследователей в области английского языка и литературы, лингвистики и методики преподавания. Описание добавляется через админ-панель — это демонстрационный текст.',
    en: 'The faculty trains bachelor’s and master’s students and researchers in English language and literature, linguistics and language teaching. The description is added in the admin panel — this is sample text.',
    zh: '学院培养英语语言文学、语言学和语言教学方向的本科生、硕士生和研究人员。简介通过管理后台添加——此为示例文字。',
  },
  address: { uz: 'Boş bino, 2-qavat, 214-xona', ru: 'Главный корпус, 2-й этаж, каб. 214', en: 'Main building, 2nd floor, room 214', zh: '主楼二层214室' },
}

const facultyPrograms: [string, FacultyProgram['level'], keyof typeof FORM][] = [
  ['60230100', 'bachelor', 'day'],
  ['60110900', 'bachelor', 'distance'],
  ['70230101', 'master', 'day'],
  ['10.00.04', 'phd', 'day'],
]

const phdTitle: L = { uz: 'Yevropa, Amerika va Avstraliya xalqlari tili va adabiyoti', ru: 'Языки и литература народов Европы, Америки и Австралии', en: 'Languages and Literature of the Peoples of Europe, America and Australia', zh: '欧洲、美洲和澳大利亚民族语言与文学' }

const chairs: L[] = [
  { uz: 'Ingliz tili leksikologiyasi kafedrasi', ru: 'Кафедра лексикологии английского языка', en: 'Department of English Lexicology', zh: '英语词汇学教研室' },
  { uz: 'Ingliz tili grammatikasi kafedrasi', ru: 'Кафедра грамматики английского языка', en: 'Department of English Grammar', zh: '英语语法教研室' },
  { uz: 'Ingliz tili stilistikasi kafedrasi', ru: 'Кафедра стилистики английского языка', en: 'Department of English Stylistics', zh: '英语文体学教研室' },
  { uz: 'Ingliz adabiyoti kafedrasi', ru: 'Кафедра английской литературы', en: 'Department of English Literature', zh: '英国文学教研室' },
  { uz: 'Ingliz tili öqitiş metodikasi kafedrasi', ru: 'Кафедра методики преподавания английского языка', en: 'Department of English Teaching Methodology', zh: '英语教学法教研室' },
]

export function getMockFaculty(lang: Locale, slug: string): FacultyDetail | null {
  const list = getMockHome(lang).faculties
  const index = list.findIndex(f => f.slug === slug)
  if (index < 0) return null
  const base = list[index]!
  const [departments, programs] = facultyCounts[slug] ?? [0, 0]

  return {
    ...base,
    number: index + 1,
    about: PLACE.about![lang],
    stats: { students: 1850, departments, programs, teachers: 96 },
    dean: { staffId: null, name: '[F.I.Ş.]', role: PLACE.dean![lang], degree: PLACE.degree![lang], photo: null, hours: PLACE.hours![lang], phone: '+998 71 230 13 73', email: `${slug}@uzswlu.uz` },
    programs: facultyPrograms.map(([code, level, form]) => ({
      code,
      title: level === 'phd' ? phdTitle[lang] : (titles[code] ?? masterTitles[code])![lang],
      level,
      form: FORM[form][lang],
      years: form === 'distance' ? 5 : LEVEL[level],
    })),
    departments: chairs.slice(0, Math.max(1, departments)).map((c, i) => ({ id: `${slug}-${i + 1}`, name: c[lang], head: null })),
    deanery: [PLACE.dean!, PLACE.deputyStudy!, PLACE.deputyYouth!, PLACE.methodist!].map(role => ({ staffId: null, name: '[F.I.Ş.]', role: role[lang], photo: null })),
    news: getMockLatest(lang, 'news', 2),
    contact: { address: PLACE.address![lang], phone: '+998 71 230 13 73', email: `${slug}@uzswlu.uz`, mapUrl: 'https://www.google.com/maps/search/?api=1&query=Toshkent%2C%20Kichik%20halqa%20yo%E2%80%98li%2C%2021' },
  }
}

// ─── Qabul ──────────────────────────────────────────────────────────────────

const A: Record<string, L> = {
  docs: { uz: 'Hujjatlar qabuli', ru: 'Приём документов', en: 'Application period', zh: '报名材料受理' },
  exams: { uz: 'Kiriş imtihonlari', ru: 'Вступительные экзамены', en: 'Entrance exams', zh: '入学考试' },
  results: { uz: 'Natijalar e’loni', ru: 'Объявление результатов', en: 'Results', zh: '结果公布' },
  tbd: { uz: 'Sanalar e’lon qilinadi', ru: 'Даты будут объявлены', en: 'Dates to be announced', zh: '日期待公布' },
  passport: { uz: 'Pasport yoki ID-karta', ru: 'Паспорт или ID-карта', en: 'Passport or ID card', zh: '护照或身份证' },
  diploma: { uz: 'Ma’lumot haqidagi hujjat (attestat yoki diplom)', ru: 'Документ об образовании (аттестат или диплом)', en: 'Proof of education (certificate or diploma)', zh: '学历证明（毕业证书或文凭）' },
  photo: { uz: '3×4 rangli fotosurat', ru: 'Цветная фотография 3×4', en: '3×4 colour photo', zh: '3×4彩色照片' },
  address: { uz: 'Boş bino · Toşkent ş., Kiçik halqa yöli köçasi, G9-A, 21-uy', ru: 'Главный корпус · г. Ташкент, ул. Кичик халка йули, G9-A, д. 21', en: 'Main building · 21 Kichik Halqa Yo‘li St, G9-A, Tashkent', zh: '主楼 · 塔什干市 Kichik Halqa Yo‘li 街 G9-A 21号' },
  hours: { uz: 'Duşanba–şanba, 9:00–17:00', ru: 'Понедельник–суббота, 9:00–17:00', en: 'Monday–Saturday, 9:00–17:00', zh: '周一至周六 9:00–17:00' },
}

const faq: [L, L][] = [
  [
    { uz: 'Hujjatlar qaçon va qayerda qabul qilinadi?', ru: 'Когда и где принимают документы?', en: 'When and where are applications accepted?', zh: '何时何地提交报名材料？' },
    { uz: 'Hujjatlar my.uzbmb.uz platformasi orqali onlayn qabul qilinadi. Aniq muddatlar yuqoridagi “Muhim sanalar” blokida e’lon qilinadi.', ru: 'Документы принимаются онлайн через платформу my.uzbmb.uz. Точные сроки публикуются в блоке «Важные даты».', en: 'Applications are submitted online via my.uzbmb.uz. Exact deadlines are published in the “Key dates” block above.', zh: '报名材料通过 my.uzbmb.uz 平台在线提交，具体时间见上方“重要日期”。' },
  ],
  [
    { uz: 'Kontrakt narxi qança va uni bölib tölaş mumkinmi?', ru: 'Сколько стоит контракт и можно ли платить частями?', en: 'How much is tuition and can I pay in instalments?', zh: '学费多少？可以分期支付吗？' },
    { uz: 'Narx yönaliş va ta’lim şakliga boğliq — “Tölov-kontrakt miqdori” sahifasida körsatilgan. Tölov tartibi şartnomada belgilanadi.', ru: 'Стоимость зависит от направления и формы обучения — она указана на странице «Стоимость обучения». Порядок оплаты определяется договором.', en: 'Fees depend on the programme and mode of study — see the “Tuition Fees” page. The payment schedule is set in the contract.', zh: '学费取决于专业和学习形式，详见“学费标准”页面，付款方式以合同为准。' },
  ],
  [
    { uz: 'Davlat granti asosida öqiş mumkinmi?', ru: 'Можно ли учиться на государственном гранте?', en: 'Can I study on a state grant?', zh: '可以获得国家奖学金名额吗？' },
    { uz: 'Ha, har bir yönaliş böyiça grant örinlari kvotasi Qabul komissiyasi tomonidan e’lon qilinadi — “Ta’lim grantlar soni” sahifasiga qarang.', ru: 'Да, квота грантовых мест по каждому направлению объявляется приёмной комиссией — см. страницу «Количество грантов».', en: 'Yes — the grant quota for each programme is announced by the Admissions Committee; see “Number of Grants”.', zh: '可以，各专业的公费名额由招生委员会公布，详见“奖学金名额”页面。' },
  ],
  [
    { uz: 'Xorijiy fuqarolar qanday hujjat topşiradi?', ru: 'Как подают документы иностранные граждане?', en: 'How do international applicants apply?', zh: '外国公民如何报名？' },
    { uz: 'Xorijiy abituriyentlar uçun alohida tartib mavjud — “Xalqaro talabalar va öqituvçilar uçun” bölimiga qarang yoki international@uzswlu.uz manziliga yozing.', ru: 'Для иностранных абитуриентов действует отдельный порядок — см. раздел «Иностранным студентам и преподавателям» или пишите на international@uzswlu.uz.', en: 'There is a separate procedure for international applicants — see “International Students and Faculty” or write to international@uzswlu.uz.', zh: '外国考生有单独的报名程序，详见“国际学生与教师”栏目，或发送邮件至 international@uzswlu.uz。' },
  ],
]

export function getMockAdmission(lang: Locale): Admission {
  const faculties = getMockHome(lang).faculties
  const fac = (slug: string) => faculties.find(f => f.slug === slug)?.name ?? ''
  const rows: [string, FacultyProgram['level'], keyof typeof FORM, string][] = [
    ['60230100', 'bachelor', 'day', 'english-philology'],
    ['60230200', 'bachelor', 'day', 'translation'],
    ['60110900', 'bachelor', 'distance', 'distance-evening'],
    ['60320100', 'bachelor', 'day', 'international-journalism'],
    ['70230102', 'master', 'day', 'romance-germanic'],
    ['70320101', 'master', 'day', 'international-journalism'],
    ['10.00.04', 'phd', 'day', 'oriental-philology'],
  ]
  return {
    year: '2026/2027',
    applyUrl: 'https://my.uzbmb.uz',
    dates: [
      { title: A.docs![lang], period: A.tbd![lang], current: true },
      { title: A.exams![lang], period: A.tbd![lang] },
      { title: A.results![lang], period: A.tbd![lang] },
    ],
    programs: rows.map(([code, level, form, faculty], i) => ({
      id: String(i + 1),
      code,
      title: level === 'phd' ? phdTitle[lang] : (titles[code] ?? masterTitles[code])![lang],
      faculty: fac(faculty),
      level,
      form: FORM[form][lang],
      years: form === 'distance' ? 5 : LEVEL[level],
      price: null,
    })),
    documents: [A.passport![lang], A.diploma![lang], A.photo![lang]],
    documentsUrl: null,
    faq: faq.map(([q, a]) => ({ q: q[lang], a: a[lang] })),
    contact: { address: A.address![lang], hours: A.hours![lang], phone: '+998 71 230 13 73', telegram: 'https://t.me/UzSWLU' },
  }
}
