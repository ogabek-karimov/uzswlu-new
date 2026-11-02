import type { ContactPage, ContentPage, DocumentList, Leader, Leadership, VideoList } from '#shared/types/api'

// VAQTINCHALIK MA'LUMOT — ichki sahifalar (backend tayyor bo'lguncha).
// Matnlar uzswlu.uz sahifalaridan (2026-10-21); ru/en/zh tarjimalari tekshirilishi kerak.

type L = Record<Locale, string>

const OLD = 'https://uzswlu.uz'

// ─── Matnli sahifalar ───────────────────────────────────────────────────────

const aboutBody: L = {
  uz: `<h2>Tarix</h2>
<p>O‘zbekiston davlat jahon tillari universiteti (O‘zDJTU) 1949-yilda Toshkent chet tillari pedagogika instituti nomi bilan faoliyatini boshlagan.</p>
<p>1992-yil 12-maydagi O‘zbekiston Respublikasi Prezidentining PF-401-sonli Farmoni bilan Toshkent chet tillari pedagogika instituti hamda Respublika Rus tili va adabiyoti instituti birlashib, O‘zbekiston davlat jahon tillari universiteti maqomiga ega bo‘ldi.</p>
<!-- timeline -->
<h2>Bugungi kun</h2>
<p>Bugungi kunda universitetda 23 168 nafar talaba 20 ga yaqin xorijiy tilni jahon ta’lim standartlari asosida o‘rganmoqda. Har yili universitetda 27 ta ta’lim yo‘nalishida bakalavr, 19 ta ta’lim yo‘nalishida magistrlik darajasiga ega mutaxassislar tayyorlanadi.</p>
<blockquote>Oliy ta’lim muassasasida til va madaniyat o‘rtasidagi aloqa ta’lim tizimining asosiy tamoyili hisoblanadi.</blockquote>
<p>Universitet talabalari chuqur bilim va ko‘nikmalar asosida til o‘rganish, o‘qitish, tarjima va talqin qilish malakalariga ega bo‘lmoqda. Kun sayin rivojlanib borayotgan tezkor zamonda ta’lim tizimi ham o‘zgarmoqda.</p>
<figure><img src="/images/campus-aerial.webp" alt="O‘zDJTU kampusi yuqoridan"><figcaption>O‘zDJTU kampusi</figcaption></figure>
<h2>Fakultetlar</h2>
<p>Ingliz tili birinchi, ikkinchi va uchinchi fakultetlari, Roman-german filologiyasi, Rus filologiyasi, Ingliz filologiyasi, Sharq filologiyasi fakultetlarida bo‘lajak pedagoglar til o‘qitishning sir-asrorlarini o‘rganmoqdalar. Tarjimonlik fakultetida esa ingliz, nemis, koreys, yapon, xitoy tili yo‘nalishlarida tarjima mahoratidan tahsil olmoqdalar. Xalqaro jurnalistika fakultetida esa mahoratli jurnalistlar yetishib chiqmoqda.</p>
<p><a href="/fakultetlar-va-kafedralar">Barcha fakultetlar →</a></p>`,
  ru: `<h2>История</h2>
<p>Узбекский государственный университет мировых языков (УзГУМЯ) начал свою деятельность в 1949 году как Ташкентский педагогический институт иностранных языков.</p>
<p>Указом Президента Республики Узбекистан № УП-401 от 12 мая 1992 года Ташкентский педагогический институт иностранных языков и Республиканский институт русского языка и литературы были объединены и получили статус Узбекского государственного университета мировых языков.</p>
<!-- timeline -->
<h2>Сегодня</h2>
<p>Сегодня 23 168 студентов университета изучают около 20 иностранных языков в соответствии с мировыми образовательными стандартами. Ежегодно университет готовит бакалавров по 27 и магистров по 19 направлениям.</p>
<blockquote>Связь языка и культуры — основной принцип образовательной системы вуза.</blockquote>
<p>Опираясь на глубокие знания и навыки, студенты университета овладевают умениями изучать, преподавать, переводить и интерпретировать языки. В стремительно меняющемся мире меняется и система образования.</p>
<figure><img src="/images/campus-aerial.webp" alt="Кампус УзГУМЯ с высоты"><figcaption>Кампус УзГУМЯ</figcaption></figure>
<h2>Факультеты</h2>
<p>На трёх факультетах английского языка, факультетах романо-германской, русской, английской и восточной филологии будущие педагоги постигают секреты преподавания языков. На переводческом факультете студенты осваивают мастерство перевода с английского, немецкого, корейского, японского и китайского языков, а факультет международной журналистики готовит профессиональных журналистов.</p>
<p><a href="/fakultetlar-va-kafedralar">Все факультеты →</a></p>`,
  en: `<h2>History</h2>
<p>Uzbekistan State University of World Languages (UzSWLU) was founded in 1949 as the Tashkent Pedagogical Institute of Foreign Languages.</p>
<p>By Presidential Decree No. UP-401 of 12 May 1992, the Tashkent Pedagogical Institute of Foreign Languages and the Republican Institute of Russian Language and Literature were merged and granted the status of Uzbekistan State University of World Languages.</p>
<!-- timeline -->
<h2>Today</h2>
<p>Today 23,168 students study nearly 20 foreign languages at the university in line with international educational standards. Every year the university trains bachelor’s graduates in 27 programmes and master’s graduates in 19.</p>
<blockquote>The link between language and culture is the core principle of the university’s education system.</blockquote>
<p>Building on deep knowledge and skills, our students learn to study, teach, translate and interpret languages. In a fast-changing world, education is changing too.</p>
<figure><img src="/images/campus-aerial.webp" alt="Aerial view of the UzSWLU campus"><figcaption>UzSWLU campus</figcaption></figure>
<h2>Faculties</h2>
<p>At the three Faculties of English Language and the Faculties of Romance and Germanic, Russian, English and Oriental Philology, future teachers master the art of language teaching. The Faculty of Translation trains translators of English, German, Korean, Japanese and Chinese, and the Faculty of International Journalism prepares skilled journalists.</p>
<p><a href="/fakultetlar-va-kafedralar">All faculties →</a></p>`,
  zh: `<h2>历史</h2>
<p>乌兹别克斯坦国立世界语言大学创建于1949年，前身为塔什干外国语师范学院。</p>
<p>根据1992年5月12日乌兹别克斯坦共和国总统第УП-401号令，塔什干外国语师范学院与共和国俄语语言文学学院合并，组建为乌兹别克斯坦国立世界语言大学。</p>
<!-- timeline -->
<h2>今天</h2>
<p>目前，学校共有23168名学生按照国际教育标准学习近20种外语。学校每年在27个本科专业和19个硕士专业培养人才。</p>
<blockquote>语言与文化的联系是学校教育体系的基本原则。</blockquote>
<p>学生在扎实的知识与技能基础上，掌握语言学习、教学、翻译与阐释的能力。在飞速发展的时代，教育体系也在不断变革。</p>
<figure><img src="/images/campus-aerial.webp" alt="校园鸟瞰"><figcaption>校园鸟瞰</figcaption></figure>
<h2>学院</h2>
<p>在三个英语学院以及罗曼-日耳曼语文、俄语语文、英语语文和东方语文学院，未来的教师们学习语言教学的奥秘；翻译学院培养英语、德语、韩语、日语和汉语翻译人才；国际新闻学院培养优秀的新闻工作者。</p>
<p><a href="/fakultetlar-va-kafedralar">全部学院 →</a></p>`,
}

const pages: Record<string, { lead?: L; body: L; facts?: [string, L][]; timeline?: [L, L, boolean?][]; attachments?: { title: L; url: string; meta: L }[]; updatedAt: string }> = {
  'universitet-haqida': {
    lead: {
      uz: '1949-yildan buyon xorijiy tillar, tarjimonlik va xalqaro jurnalistika bo‘yicha mutaxassislar tayyorlab kelayotgan universitet.',
      ru: 'С 1949 года университет готовит специалистов в области иностранных языков, перевода и международной журналистики.',
      en: 'Since 1949 the university has trained specialists in foreign languages, translation and international journalism.',
      zh: '自1949年起，学校致力于培养外语、翻译和国际新闻领域的专业人才。',
    },
    body: aboutBody,
    facts: [
      ['23 168', { uz: 'talaba', ru: 'студентов', en: 'students', zh: '名学生' }],
      ['~20', { uz: 'xorijiy til', ru: 'иностранных языков', en: 'foreign languages', zh: '种外语' }],
      ['27', { uz: 'bakalavriat yo‘nalishi', ru: 'направлений бакалавриата', en: 'bachelor’s programmes', zh: '个本科专业' }],
      ['19', { uz: 'magistratura yo‘nalishi', ru: 'направлений магистратуры', en: 'master’s programmes', zh: '个硕士专业' }],
    ],
    timeline: [
      [{ uz: '1949', ru: '1949', en: '1949', zh: '1949' }, { uz: 'Toshkent chet tillari pedagogika instituti', ru: 'Ташкентский педагогический институт иностранных языков', en: 'Tashkent Pedagogical Institute of Foreign Languages', zh: '塔什干外国语师范学院' }],
      [{ uz: '1992', ru: '1992', en: '1992', zh: '1992' }, { uz: 'PF-401-sonli Farmon — universitet maqomi', ru: 'Указ УП-401 — статус университета', en: 'Decree UP-401 — university status', zh: '第УП-401号总统令——获大学地位' }],
      [{ uz: 'Bugun', ru: 'Сегодня', en: 'Today', zh: '今天' }, { uz: '11 fakultet, 23 168 talaba', ru: '11 факультетов, 23 168 студентов', en: '11 faculties, 23,168 students', zh: '11个学院，23168名学生' }, true],
    ],
    attachments: [
      {
        title: { uz: 'Universitet nizomi', ru: 'Устав университета', en: 'University Charter', zh: '大学章程' },
        url: `${OLD}/backend/web/files/O%27zDJTU%20nizomi.pdf`,
        meta: { uz: 'ÖzDJTU nizomi · PDF', ru: 'Устав УзГУМЯ · PDF', en: 'UzSWLU Charter · PDF', zh: '大学章程 · PDF' },
      },
    ],
    updatedAt: '2026-10-21T09:00:00+05:00',
  },
}

const SAMPLE_BODY: L = {
  uz: '<p>Bu sahifaning matni, rasmlari va hujjatlari admin panel orqali kiritiladi. Hozir dizaynni körsatiş uçun namunaviy matn turibdi.</p>',
  ru: '<p>Текст, изображения и документы этой страницы добавляются через админ-панель. Сейчас показан демонстрационный текст.</p>',
  en: '<p>The text, images and documents of this page are added in the admin panel. Sample text is shown for now.</p>',
  zh: '<p>本页面的文字、图片和文件通过管理后台添加，目前显示的是示例文字。</p>',
}

/** Menyudagi sahifa bo'lsa — matnli sahifa (to'liq matn faqat "Universitet haqida" uchun), aks holda null → 404 */
export function getMockContentPage(lang: Locale, slug: string): ContentPage | null {
  const link = getMockMenu(lang).flatMap(g => g.links).find(l => l.url === `/${slug}`)
  if (!link) return null

  const page = pages[slug]
  return {
    slug,
    title: link.title,
    lead: page?.lead?.[lang] ?? null,
    facts: (page?.facts ?? []).map(([value, label]) => ({ value, label: label[lang] })),
    body: page?.body[lang] ?? SAMPLE_BODY[lang],
    timeline: (page?.timeline ?? []).map(([label, text, highlight]) => ({ label: label[lang], text: text[lang], highlight: highlight ?? false })),
    attachments: (page?.attachments ?? []).map(a => ({ title: a.title[lang], url: a.url, kind: 'pdf' as const, meta: a.meta[lang] })),
    updatedAt: page?.updatedAt ?? '2026-10-21T09:00:00+05:00',
  }
}

// ─── Rektorat ───────────────────────────────────────────────────────────────

const MONDAY: L = { uz: 'Dushanba, 15:00–17:00', ru: 'Понедельник, 15:00–17:00', en: 'Monday, 15:00–17:00', zh: '周一 15:00–17:00' }

type LeaderSeed = Omit<Leader, 'role' | 'hours'> & { role: L; hours?: L }

const rector: LeaderSeed = {
  staffId: '9300', name: 'Tuxtasinov Ilxomjon Madaminovich', hours: MONDAY, phone: '+998 71 230 12 91', ext: '1001', email: 'rector@uzswlu.uz',
  role: { uz: 'Rektor', ru: 'Ректор', en: 'Rector', zh: '校长' },
}

// uzswlu.uz/rektorat sahifasidan (2026-10-21)
const prorectors: LeaderSeed[] = [
  { staffId: '9004', name: 'Sadiyev Valijon Alijonovich', hours: MONDAY, phone: '+998 71 230 13 40', ext: '1009', email: 'v.sadiyev@uzswlu.uz', role: { uz: 'Yoshlar masalalari va ma’naviy-ma’rifiy ishlar bo‘yicha birinchi prorektor', ru: 'Первый проректор по делам молодёжи и духовно-просветительской работе', en: 'First Vice-Rector for Youth Affairs and Spiritual and Educational Work', zh: '第一副校长（青年事务与思想教育）' } },
  { staffId: '7909', name: 'Chutpulatov Muxammad Chariyevich', hours: MONDAY, phone: '+998 71 230 12 94', ext: '1015', email: 'm.chutpulatov@uzswlu.uz', role: { uz: 'O‘quv ishlari bo‘yicha prorektor', ru: 'Проректор по учебной работе', en: 'Vice-Rector for Academic Affairs', zh: '副校长（教学）' } },
  { staffId: '8450', name: 'Nasirov Abduraxim Abdimutalipovich', hours: MONDAY, phone: '+998 71 230 13 73', ext: '1008', email: 'a.nasirov@uzswlu.uz', role: { uz: 'Xalqaro hamkorlik masalalari bo‘yicha prorektor', ru: 'Проректор по международному сотрудничеству', en: 'Vice-Rector for International Cooperation', zh: '副校长（国际合作）' } },
  { staffId: '8098', name: 'Yusupov Otabek Yakubovich', hours: MONDAY, phone: '+998 71 230 12 93', ext: '1011', email: 'o.yusupov@uzswlu.uz', role: { uz: 'Ilmiy ishlar va innovatsiyalar bo‘yicha prorektor', ru: 'Проректор по научной работе и инновациям', en: 'Vice-Rector for Research and Innovation', zh: '副校长（科研与创新）' } },
  { staffId: null, name: 'Xamrayev Maqsudjon Saidaxmadovich', hours: { uz: 'Ish vaqti: 8:30–16:30', ru: 'Рабочее время: 8:30–16:30', en: 'Working hours: 8:30–16:30', zh: '工作时间：8:30–16:30' }, phone: '+998 71 230 12 93', ext: '1007', email: null, role: { uz: 'Moliya-iqtisod ishlari bo‘yicha prorektor', ru: 'Проректор по финансово-экономическим вопросам', en: 'Vice-Rector for Finance and Economics', zh: '副校长（财务经济）' } },
]

const press: LeaderSeed = {
  staffId: '7731', name: 'Ibragimov Otabek Alisherovich', phone: '+998 97 777 99 26', email: 'o.ibragimov@uzswlu.uz',
  role: { uz: 'Axborot siyosati masalalari bo‘yicha rektor maslahatchisi', ru: 'Советник ректора по вопросам информационной политики', en: 'Adviser to the Rector on Information Policy', zh: '校长信息政策顾问' },
}

const leader = (l: LeaderSeed, lang: Locale): Leader => ({ ...l, role: l.role[lang], hours: l.hours?.[lang] ?? null, photo: null })

export function getMockLeadership(lang: Locale): Leadership {
  return { rector: leader(rector, lang), prorectors: prorectors.map(p => leader(p, lang)), press: leader(press, lang) }
}

// ─── Me'yoriy hujjatlar ─────────────────────────────────────────────────────

const docCategories: Record<string, L> = {
  uni: { uz: 'Universitet hujjatlari', ru: 'Документы университета', en: 'University documents', zh: '大学文件' },
  study: { uz: 'Öquv va imtihon jarayoni', ru: 'Учебный процесс и экзамены', en: 'Teaching and examinations', zh: '教学与考试' },
  law: { uz: 'Qonunçilik', ru: 'Законодательство', en: 'Legislation', zh: '法律法规' },
}

// uzswlu.uz/meyoriy-hujjatlar sahifasidan (2026-10-21). Fayl havolalari backend'dan keladi — hozir eski sahifaga olib boradi.
const DOCS_PAGE = `${OLD}/meyoriy-hujjatlar`
const docs: [string, 'pdf' | 'link', L, string?][] = [
  ['uni', 'pdf', { uz: 'O‘zDJTU ustavi', ru: 'Устав УзГУМЯ', en: 'UzSWLU Charter', zh: '大学章程' }],
  ['uni', 'pdf', { uz: 'O‘zDJTU ichki mehnat tartib qoidalari', ru: 'Правила внутреннего трудового распорядка УзГУМЯ', en: 'UzSWLU internal labour regulations', zh: '内部劳动规章' }],
  ['uni', 'pdf', { uz: 'Xodimlarni ishga qabul qilish tartibi to‘g‘risidagi nizom', ru: 'Положение о порядке приёма сотрудников на работу', en: 'Regulations on staff recruitment', zh: '员工招聘规定' }],
  ['uni', 'pdf', { uz: 'O‘zDJTU odob-axloq kodeksi', ru: 'Кодекс этики УзГУМЯ', en: 'UzSWLU Code of Ethics', zh: '道德行为准则' }],
  ['uni', 'pdf', { uz: 'O‘zDJTU faoliyatida manfaatlar to‘qnashuvini boshqarish bo‘yicha nizom', ru: 'Положение об управлении конфликтом интересов в деятельности УзГУМЯ', en: 'Conflict of interest management policy', zh: '利益冲突管理规定' }],
  ['uni', 'link', { uz: 'Manfaatlar to‘qnashuvi deklaratsiyasi', ru: 'Декларация о конфликте интересов', en: 'Conflict of interest declaration', zh: '利益冲突申报' }],
  ['study', 'pdf', { uz: 'Filologiya va tillarni o‘qitish (roman-german tillari) bakalavriat ta’lim yo‘nalishining malaka talablari', ru: 'Квалификационные требования бакалавриата «Филология и преподавание языков (романо-германские языки)»', en: 'Qualification requirements: Philology and Language Teaching (Romance and Germanic languages), BA', zh: '本科专业资格要求：语文学与语言教学（罗曼-日耳曼语）' }],
  ['study', 'pdf', { uz: 'Tarjima nazariyasi va amaliyoti (roman-german tillari) bakalavriat ta’lim yo‘nalishining malaka talablari', ru: 'Квалификационные требования бакалавриата «Теория и практика перевода (романо-германские языки)»', en: 'Qualification requirements: Translation Theory and Practice (Romance and Germanic languages), BA', zh: '本科专业资格要求：翻译理论与实践（罗曼-日耳曼语）' }],
  ['law', 'link', { uz: 'O‘zbekiston Respublikasi qonunlari', ru: 'Законы Республики Узбекистан', en: 'Laws of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国法律' }, 'https://lex.uz'],
  ['law', 'link', { uz: 'O‘zbekiston Respublikasi Mehnat kodeksi', ru: 'Трудовой кодекс Республики Узбекистан', en: 'Labour Code of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国劳动法典' }, 'https://lex.uz'],
  ['law', 'link', { uz: 'O‘zbekiston Respublikasi Prezidentining qarorlari', ru: 'Постановления Президента Республики Узбекистан', en: 'Resolutions of the President of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国总统决议' }, 'https://lex.uz'],
  ['law', 'link', { uz: 'O‘zbekiston Respublikasi Vazirlar Mahkamasining qarorlari', ru: 'Постановления Кабинета Министров Республики Узбекистан', en: 'Resolutions of the Cabinet of Ministers of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国内阁决议' }, 'https://lex.uz'],
  ['law', 'link', { uz: 'Oliy ta’lim muassasalariga o‘qishga qabul qilish, talabalar o‘qishini ko‘chirish, qayta tiklash va o‘qishdan chetlashtirish tartibi to‘g‘risidagi nizomlar', ru: 'Положения о порядке приёма, перевода, восстановления и отчисления студентов высших учебных заведений', en: 'Regulations on admission, transfer, reinstatement and expulsion of students', zh: '高校招生、转学、复学和退学规定' }, 'https://lex.uz'],
]

export function getMockDocuments(lang: Locale): DocumentList {
  return {
    categories: Object.entries(docCategories).map(([id, title]) => ({ id, title: title[lang] })),
    items: docs.map(([category, kind, title, url], i) => ({
      id: String(i + 1),
      category,
      kind,
      title: title[lang],
      url: url ?? DOCS_PAGE,
      meta: kind === 'pdf' ? 'PDF' : null,
    })),
  }
}

// ─── Aloqa ──────────────────────────────────────────────────────────────────

const campusPhones: Record<string, string> = {
  main: '+998 71 230 13 73',
  philology: '+998 71 230 03 44',
  journalism: '+998 71 231 10 16',
  russian: '+998 71 281 21 03',
}

export function getMockContact(lang: Locale): ContactPage {
  const site = getMockSite(lang)
  const uzCampuses = getMockSite('uz').campuses
  return {
    hotline: { phone: site.phone, ext: site.phoneExt },
    emails: [
      { title: { uz: 'Umumiy e-poçta', ru: 'Общая почта', en: 'General email', zh: '综合邮箱' }[lang], value: 'uzdjtu@uzswlu.uz', extra: ['uzgumya@exat.uz', 'uzgumya1@exat.uz'] },
      { title: { uz: 'Xalqaro hamkorlik', ru: 'Международное сотрудничество', en: 'International cooperation', zh: '国际合作' }[lang], value: 'international@uzswlu.uz', extra: [`${{ uz: 'Reytinglar', ru: 'Рейтинги', en: 'Rankings', zh: '排名' }[lang]}: uzswluranking@gmail.com`] },
    ],
    campuses: site.campuses.map(c => ({
      ...c,
      phone: campusPhones[c.id] ?? site.phone,
      mapUrl: `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(uzCampuses.find(u => u.id === c.id)?.address ?? c.address)}`,
    })),
    // uzswlu.uz/aloqa sahifasidan (2026-10-21)
    leaders: [
      { name: 'Sadiyev Valijon Alijonovich', role: prorectors[0]!.role[lang], ext: '1009', phone: '71 230 13 40' },
      { name: 'Yusupov Otabek Yakubovich', role: prorectors[3]!.role[lang], ext: '1006', phone: '71 230 12 93' },
      { name: 'Xamrayev Maqsudjon Saidaxmadovich', role: prorectors[4]!.role[lang], ext: '1007', phone: '71 230 12 97' },
      { name: 'Nasirov Abduraxim Abdimutalipovich', role: prorectors[2]!.role[lang], ext: '1008', phone: '71 230 12 90' },
    ],
    reception: '71 230 13 62',
    recipients: [
      { id: 'rector', title: { uz: 'Rektor', ru: 'Ректор', en: 'Rector', zh: '校长' }[lang] },
      { id: 'first-vice', title: { uz: 'Birinçi prorektor', ru: 'Первый проректор', en: 'First Vice-Rector', zh: '第一副校长' }[lang] },
      { id: 'vice-academic', title: { uz: 'Öquv işlari böyiça prorektor', ru: 'Проректор по учебной работе', en: 'Vice-Rector for Academic Affairs', zh: '副校长（教学）' }[lang] },
      { id: 'admission', title: { uz: 'Qabul komissiyasi', ru: 'Приёмная комиссия', en: 'Admissions Committee', zh: '招生委员会' }[lang] },
    ],
  }
}

// ─── Video darsliklar ───────────────────────────────────────────────────────

const CHANNEL = 'https://www.youtube.com/c/Ozbekistondavlatjahontillariuniversiteti'

// Toifalar uzswlu.uz/video-darsliklar sahifasidan; darslar — NAMUNA
const videoCategories: { id: string; greeting: string; title: L }[] = [
  { id: 'en', greeting: 'Hello', title: { uz: 'Ingliz tilini o‘qitish metodikasi', ru: 'Методика преподавания английского языка', en: 'English language teaching methodology', zh: '英语教学法' } },
  { id: 'es', greeting: '¡Hola!', title: { uz: 'Ispan tili', ru: 'Испанский язык', en: 'Spanish', zh: '西班牙语' } },
  { id: 'fr', greeting: 'Bonjour', title: { uz: 'Fransuz tili', ru: 'Французский язык', en: 'French', zh: '法语' } },
  { id: 'de', greeting: 'Hallo', title: { uz: 'Nemis tili', ru: 'Немецкий язык', en: 'German', zh: '德语' } },
  { id: 'zh', greeting: '你好', title: { uz: 'Xitoy tili', ru: 'Китайский язык', en: 'Chinese', zh: '汉语' } },
]

const lessonTitle: Record<Locale, (cat: string, n: number) => string> = {
  uz: (c, n) => `${c} — ${n}-dars`,
  ru: (c, n) => `${c} — урок ${n}`,
  en: (c, n) => `${c} — lesson ${n}`,
  zh: (c, n) => `${c}——第${n}课`,
}

export function getMockVideos(lang: Locale): VideoList {
  return {
    live: { isLive: false, url: `${CHANNEL}/live`, next: null },
    channelUrl: CHANNEL,
    categories: videoCategories.map(c => ({ id: c.id, title: c.title[lang], greeting: c.greeting, lang: c.id })),
    items: videoCategories.flatMap(c => [1, 2, 3, 4, 5, 6].map(n => ({
      id: `${c.id}-${n}`,
      category: c.id,
      title: lessonTitle[lang](c.title[lang], n),
      teacher: null,
      duration: null,
      url: CHANNEL,
      thumbnail: null,
    }))),
  }
}
