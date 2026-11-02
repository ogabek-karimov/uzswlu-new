import type {
  CabinetDocSection, CabinetDocument, CabinetPatch, HemisEmployment, LocalizedText, StaffCabinet,
  StaffDepartment, StaffDocSection, StaffGroup, StaffList, StaffProfile, StaffSummary,
} from '#shared/types/api'

// VAQTINCHALIK MA'LUMOT — backend tayyor bo'lguncha.
// Xodimlar uzswlu.uz/staff sahifasidan namuna (2026-10-21 holatiga), ID'lar saytdagidek.
// Suratlar ataylab berilmagan — bosh harflar chiqadi; haqiqiysini backend HEMIS'dan beradi.
// Ismlar barcha tillarda lotin yozuvida; bo'lim va lavozim tarjimalari tekshirilishi kerak.

type L = Record<Locale, string>

const departments: Record<string, { group: StaffGroup; name: L }> = {
  'rahbariyat': { group: 'lead', name: { uz: 'Rahbariyat', ru: 'Руководство', en: 'Leadership', zh: '校领导' } },
  'ingliz-tili-tarjima-nazariyasi-kafedrasi': { group: 'chair', name: { uz: 'Ingliz tili tarjima nazariyasi kafedrasi', ru: 'Кафедра теории перевода английского языка', en: 'Department of English Translation Theory', zh: '英语翻译理论教研室' } },
  'ingliz-filologiyasi-fakulteti': { group: 'faculty', name: { uz: 'Ingliz filologiyasi fakulteti', ru: 'Факультет английской филологии', en: 'Faculty of English Philology', zh: '英语语文学院' } },
  'xalqaro-jurnalistika-fakulteti': { group: 'faculty', name: { uz: 'Xalqaro jurnalistika fakulteti', ru: 'Факультет международной журналистики', en: 'Faculty of International Journalism', zh: '国际新闻学院' } },
  'tarjimonlik-fakulteti': { group: 'faculty', name: { uz: 'Tarjimonlik fakulteti', ru: 'Переводческий факультет', en: 'Faculty of Translation', zh: '翻译学院' } },
  'pedagogika-va-psixologiya-kafedrasi': { group: 'chair', name: { uz: 'Pedagogika va psixologiya kafedrasi', ru: 'Кафедра педагогики и психологии', en: 'Department of Pedagogy and Psychology', zh: '教育学与心理学教研室' } },
  'xitoy-filologiyasi-kafedrasi': { group: 'chair', name: { uz: 'Xitoy filologiyasi kafedrasi', ru: 'Кафедра китайской филологии', en: 'Department of Chinese Philology', zh: '汉语语文学教研室' } },
  'yapon-filologiyasi-kafedrasi': { group: 'chair', name: { uz: 'Yapon filologiyasi kafedrasi', ru: 'Кафедра японской филологии', en: 'Department of Japanese Philology', zh: '日语语文学教研室' } },
  'koreys-filologiyasi-kafedrasi': { group: 'chair', name: { uz: 'Koreys filologiyasi kafedrasi', ru: 'Кафедра корейской филологии', en: 'Department of Korean Philology', zh: '韩语语文学教研室' } },
  'jahon-adabiyoti-kafedrasi': { group: 'chair', name: { uz: 'Jahon adabiyoti kafedrasi', ru: 'Кафедра мировой литературы', en: 'Department of World Literature', zh: '世界文学教研室' } },
  'nemis-tili-nazariy-fanlar-kafedrasi': { group: 'chair', name: { uz: 'Nemis tili nazariy fanlar kafedrasi', ru: 'Кафедра теоретических дисциплин немецкого языка', en: 'Department of German Theoretical Studies', zh: '德语理论教研室' } },
  'raqamli-talim-texnologiyalari-markazi': { group: 'unit', name: { uz: 'Raqamli ta’lim texnologiyalari markazi', ru: 'Центр цифровых образовательных технологий', en: 'Digital Education Technologies Centre', zh: '数字教育技术中心' } },
  'axborot-resurs-markazi': { group: 'unit', name: { uz: 'Axborot-resurs markazi', ru: 'Информационно-ресурсный центр', en: 'Information Resource Centre', zh: '信息资源中心' } },
  'xalqaro-hamkorlik-bolimi': { group: 'unit', name: { uz: 'Xalqaro hamkorlik bo‘limi', ru: 'Отдел международного сотрудничества', en: 'International Cooperation Office', zh: '国际合作处' } },
  'marketing-bolimi': { group: 'unit', name: { uz: 'Marketing bo‘limi', ru: 'Отдел маркетинга', en: 'Marketing Office', zh: '市场营销处' } },
}

const positions: Record<string, L> = {
  'rector': { uz: 'Rektor', ru: 'Ректор', en: 'Rector', zh: '校长' },
  'first-vice-academic': { uz: 'O‘quv ishlari bo‘yicha birinchi prorektor', ru: 'Первый проректор по учебной работе', en: 'First Vice-Rector for Academic Affairs', zh: '第一副校长（教学）' },
  'vice-research': { uz: 'Ilmiy ishlar va innovatsiyalar bo‘yicha prorektor', ru: 'Проректор по научной работе и инновациям', en: 'Vice-Rector for Research and Innovation', zh: '副校长（科研与创新）' },
  'vice-international': { uz: 'Xalqaro hamkorlik bo‘yicha prorektor', ru: 'Проректор по международному сотрудничеству', en: 'Vice-Rector for International Cooperation', zh: '副校长（国际合作）' },
  'vice-youth': { uz: 'Yoshlar bilan ishlash bo‘yicha prorektor', ru: 'Проректор по работе с молодёжью', en: 'Vice-Rector for Youth Affairs', zh: '副校长（青年工作）' },
  'rector-assistant': { uz: 'Rektor yordamchisi', ru: 'Помощник ректора', en: 'Assistant to the Rector', zh: '校长助理' },
  'press-secretary': { uz: 'Matbuot kotibi', ru: 'Пресс-секретарь', en: 'Press Secretary', zh: '新闻秘书' },
  'dean': { uz: 'Dekan', ru: 'Декан', en: 'Dean', zh: '院长' },
  'deputy-dean': { uz: 'Dekan muovini', ru: 'Заместитель декана', en: 'Deputy Dean', zh: '副院长' },
  'tutor': { uz: 'Tyutor', ru: 'Тьютор', en: 'Tutor', zh: '辅导员' },
  'head-chair': { uz: 'Kafedra mudiri', ru: 'Заведующий кафедрой', en: 'Head of Department', zh: '教研室主任' },
  'professor': { uz: 'Professor', ru: 'Профессор', en: 'Professor', zh: '教授' },
  'docent': { uz: 'Dotsent', ru: 'Доцент', en: 'Associate Professor', zh: '副教授' },
  'senior-lecturer': { uz: 'Katta o‘qituvchi', ru: 'Старший преподаватель', en: 'Senior Lecturer', zh: '高级讲师' },
  'assistant': { uz: 'Assistent', ru: 'Ассистент', en: 'Assistant Lecturer', zh: '助教' },
  'trainee': { uz: 'Stajer-o‘qituvchi', ru: 'Стажёр-преподаватель', en: 'Trainee Lecturer', zh: '实习教师' },
  'sysadmin': { uz: 'Tizim administratori', ru: 'Системный администратор', en: 'System Administrator', zh: '系统管理员' },
  'engineer': { uz: 'Muhandis', ru: 'Инженер', en: 'Engineer', zh: '工程师' },
  'engineer-1': { uz: '1-toifali muhandis', ru: 'Инженер 1-й категории', en: 'Engineer, 1st category', zh: '一级工程师' },
  'head-section': { uz: 'Bo‘lim mudiri', ru: 'Заведующий отделом', en: 'Head of Section', zh: '部门主任' },
  'head-office': { uz: 'Bo‘lim boshlig‘i', ru: 'Начальник отдела', en: 'Head of Office', zh: '处长' },
  'chief-specialist': { uz: 'Bosh mutaxassis', ru: 'Главный специалист', en: 'Chief Specialist', zh: '首席专员' },
}

// [ID, ism, bo'lim, lavozim] — rahbariyat lavozim tartibida, qolganlar bo'limlar bo'yicha
const people: [string, string, string, string][] = [
  ['9300', 'Tuxtasinov Ilxomjon Madaminovich', 'rahbariyat', 'rector'],
  ['7909', 'Chutpulatov Muxammad Chariyevich', 'rahbariyat', 'first-vice-academic'],
  ['8098', 'Yusupov Otabek Yakubovich', 'rahbariyat', 'vice-research'],
  ['8450', 'Nasirov Abduraxim Abdimutalipovich', 'rahbariyat', 'vice-international'],
  ['9004', 'Sadiyev Valijon Alijonovich', 'rahbariyat', 'vice-youth'],
  ['9394', 'Nurov Azizbek Elmurotovich', 'rahbariyat', 'rector-assistant'],
  ['7731', 'Ibragimov Otabek Alisherovich', 'rahbariyat', 'press-secretary'],
  ['8007', 'Shahzoda Bo‘stonova', 'ingliz-filologiyasi-fakulteti', 'tutor'],
  ['8421', 'Sadullayev Fayyoz Farxadovich', 'ingliz-filologiyasi-fakulteti', 'tutor'],
  ['8439', 'Nurullayeva Sadoqat Baxtiyor qizi', 'ingliz-filologiyasi-fakulteti', 'tutor'],
  ['8654', 'Metyakubov Alisher Djumanazarovich', 'xalqaro-jurnalistika-fakulteti', 'dean'],
  ['8041', 'Shermatov Eldorjon Yovmiddinovich', 'xalqaro-jurnalistika-fakulteti', 'deputy-dean'],
  ['7765', 'Malika Saburova', 'xalqaro-jurnalistika-fakulteti', 'tutor'],
  ['8395', 'Jaloliddin Tursunboboyev', 'xalqaro-jurnalistika-fakulteti', 'tutor'],
  ['7949', 'Yo‘ldoshev Ulug‘bek Ravshanbekovich', 'tarjimonlik-fakulteti', 'dean'],
  ['8537', 'Musabekova Madina Narimanbekovna', 'tarjimonlik-fakulteti', 'deputy-dean'],
  ['8929', 'Hasan Isomov', 'tarjimonlik-fakulteti', 'tutor'],
  ['8930', 'Amir Abdurahmonov', 'tarjimonlik-fakulteti', 'tutor'],
  ['7768', 'Djurayev Dusmurod Uralovich', 'pedagogika-va-psixologiya-kafedrasi', 'head-chair'],
  ['7792', 'Isakulova Nilufar Janikulovna', 'pedagogika-va-psixologiya-kafedrasi', 'professor'],
  ['7790', 'Miliyeva Muattar Gaffarovna', 'pedagogika-va-psixologiya-kafedrasi', 'docent'],
  ['7769', 'Xolboyev Asqarali Mirxoldorovich', 'pedagogika-va-psixologiya-kafedrasi', 'assistant'],
  ['7957', 'Djurayev Dilshod Mamadiyarovich', 'xitoy-filologiyasi-kafedrasi', 'docent'],
  ['7755', 'Azamat Jabborov', 'xitoy-filologiyasi-kafedrasi', 'assistant'],
  ['7942', 'Nurmuxamedova Muqaddas Abdufattox qizi', 'xitoy-filologiyasi-kafedrasi', 'assistant'],
  ['7757', 'Abdullayeva Nuriya Baxodir qizi', 'xitoy-filologiyasi-kafedrasi', 'trainee'],
  ['8091', 'Xamidova Nargiza Mirvaxidovna', 'yapon-filologiyasi-kafedrasi', 'head-chair'],
  ['8068', 'Inoyatov Javohir Ne’matillo o‘g‘li', 'yapon-filologiyasi-kafedrasi', 'trainee'],
  ['8089', 'Shohjahon Pirmaxmatov', 'yapon-filologiyasi-kafedrasi', 'trainee'],
  ['8092', 'Azimjon Mamadiyev', 'yapon-filologiyasi-kafedrasi', 'trainee'],
  ['8496', 'Ugiloy Xujayeva', 'koreys-filologiyasi-kafedrasi', 'senior-lecturer'],
  ['8230', 'Kyung Ae Kim', 'koreys-filologiyasi-kafedrasi', 'assistant'],
  ['8497', 'Sa’dullayeva Ozoda Zoid qizi', 'koreys-filologiyasi-kafedrasi', 'assistant'],
  ['8366', 'Sobirov Elbek Davron o‘g‘li', 'koreys-filologiyasi-kafedrasi', 'trainee'],
  ['7819', 'Xalliyeva Gulnoz Iskandarovna', 'jahon-adabiyoti-kafedrasi', 'head-chair'],
  ['8005', 'Feruza Sapaeva', 'jahon-adabiyoti-kafedrasi', 'professor'],
  ['7818', 'Qahharova Dilafro‘z Abdug‘aforovna', 'jahon-adabiyoti-kafedrasi', 'senior-lecturer'],
  ['8470', 'Ma’diyeva Adiba Dovudovna', 'jahon-adabiyoti-kafedrasi', 'senior-lecturer'],
  ['7878', 'Ziyadullayev Ilxom Oblakulovich', 'nemis-tili-nazariy-fanlar-kafedrasi', 'head-chair'],
  ['8140', 'Madazimova Mavjudaxon Muminovna', 'nemis-tili-nazariy-fanlar-kafedrasi', 'senior-lecturer'],
  ['7947', 'Yaxyayeva Zumrad Islomovna', 'nemis-tili-nazariy-fanlar-kafedrasi', 'assistant'],
  ['8199', 'Raxmatova Dilnavoz Abdimuradovna', 'nemis-tili-nazariy-fanlar-kafedrasi', 'trainee'],
  ['7715', 'Abduvoxidov Davlatbek Shuxratjon o‘g‘li', 'raqamli-talim-texnologiyalari-markazi', 'sysadmin'],
  ['7919', 'Mirjalol Safarov', 'raqamli-talim-texnologiyalari-markazi', 'engineer-1'],
  ['7917', 'Og‘abek Karimov', 'raqamli-talim-texnologiyalari-markazi', 'engineer'],
  ['7921', 'G‘ayrat Karshiyev', 'raqamli-talim-texnologiyalari-markazi', 'engineer'],
  ['7955', 'Mashkura Muxamedjanova', 'axborot-resurs-markazi', 'head-section'],
  ['7959', 'Iroda Ashurova', 'axborot-resurs-markazi', 'head-section'],
  ['7960', 'Saida Inogamova', 'axborot-resurs-markazi', 'head-section'],
  ['7961', 'Sardor To‘xtayev', 'axborot-resurs-markazi', 'head-section'],
  ['8402', 'Xusanboy Yuldashev', 'xalqaro-hamkorlik-bolimi', 'head-office'],
  ['9025', 'Qaramanov Obid Xudayberdiyevich', 'marketing-bolimi', 'chief-specialist'],
  ['9198', 'Ulug‘bek Ramazanov', 'marketing-bolimi', 'chief-specialist'],
  ['9195', 'Minosidinov Sherzod Baxromjonovich', 'marketing-bolimi', 'chief-specialist'],
  ['9285', 'Diyorbek Musurmonov', 'marketing-bolimi', 'chief-specialist'],
]

// Xodimlar dashboard'da to'ldirgan ma'lumotlar (namuna). E-pochta va ichki telefonlar — uzswlu.uz/rektorat dagi
// ochiq ma'lumotlar; mobil/WhatsApp raqamlari — namuna (+998 90 123 45 67), haqiqiy shaxsiy raqam emas.
// Qolgan xodimlarda bo'sh: profil "hali qo'shilmagan" holatini ko'rsatadi.
type Extra = Partial<Pick<StaffProfile, 'contacts' | 'socials' | 'science' | 'documents'>> & {
  about?: L
  /** HEMIS'dagidek bir nechta ish joyi: [bo'lim, lavozim], HEMIS tartibida */
  employments?: [string, string][]
}
const CAMPUS = 'Toshkent sh., Kichik halqa yo‘li ko‘chasi, G9-A, 21-uy'
const extras: Record<string, Extra> = {
  '9300': {
    // HEMIS'da avval Professor (kafedra, asosiy ish joy), keyin Rektor (o'rindoshlik) keladi — frontend "Rektor, Professor" qilib ko'rsatadi
    employments: [['ingliz-tili-tarjima-nazariyasi-kafedrasi', 'professor'], ['rahbariyat', 'rector']],
    about: {
      uz: 'Rektor, pedagogika fanlari doktori (DSc), professor',
      ru: 'Ректор, доктор педагогических наук (DSc), профессор',
      en: 'Rector, Doctor of Pedagogical Sciences (DSc), Professor',
      zh: '校长，教育学博士（DSc），教授',
    },
    contacts: [
      { type: 'email', value: 'rector@uzswlu.uz' },
      { type: 'email', value: 'uzdjtu@uzswlu.uz' },
      { type: 'whatsapp', value: '+998 90 123 45 67' },
      { type: 'mobile', value: '+998 90 123 45 67' },
      { type: 'phone', value: '+998 71 230 12 91' },
      { type: 'office', value: CAMPUS },
    ],
    socials: [
      { network: 'instagram', url: 'https://www.instagram.com/uzswlu_official' },
      { network: 'facebook', url: 'https://www.facebook.com/uzswlu' },
    ],
  },
  '7909': { contacts: [{ type: 'email', value: 'm.chutpulatov@uzswlu.uz' }, { type: 'phone', value: '+998 71 230 12 94' }, { type: 'office', value: CAMPUS }] },
  '8098': { contacts: [{ type: 'email', value: 'o.yusupov@uzswlu.uz' }, { type: 'phone', value: '+998 71 230 12 93' }] },
  '8450': { contacts: [{ type: 'email', value: 'a.nasirov@uzswlu.uz' }, { type: 'phone', value: '+998 71 230 13 73' }] },
  '9004': { contacts: [{ type: 'email', value: 'v.sadiyev@uzswlu.uz' }, { type: 'phone', value: '+998 71 230 13 40' }] },
  // uzswlu.uz/teacher/7731 dagi ochiq profil
  '7731': {
    contacts: [
      { type: 'email', value: 'o.ibragimov@uzswlu.uz' },
      { type: 'telegram', value: 'https://t.me/Otabek_Ibragimov' },
    ],
    socials: [
      { network: 'instagram', url: 'https://www.instagram.com/otabek__ibragimov' },
      { network: 'threads', url: 'https://www.threads.net/@otabek__ibragimov' },
      { network: 'facebook', url: 'https://www.facebook.com/farrux.ibragimov.756' },
    ],
  },
  // Ilmiy profil va hujjatlar bo'limlarini ko'rsatish uchun namuna (havolalar umumiy, shaxsiy emas)
  '7792': {
    about: {
      uz: 'Pedagogika va psixologiya böyiça dars beradi. (Namuna matn — backend ulanganda xodimning özi yozgani çiqadi.)',
      ru: 'Преподаёт педагогику и психологию. (Пример текста.)',
      en: 'Teaches pedagogy and psychology. (Sample text.)',
      zh: '讲授教育学与心理学。（示例文本）',
    },
    contacts: [{ type: 'email', value: 'namuna@uzswlu.uz' }, { type: 'phone', value: '+998 71 230 13 73' }],
    science: [
      { network: 'orcid', url: 'https://orcid.org' },
      { network: 'scholar', url: 'https://scholar.google.com' },
    ],
    documents: [
      { section: 'cv', items: [{ title: 'CV (namuna)', url: '#' }] },
      { section: 'articles', items: [{ title: 'Namuna maqola 1', url: '#' }, { title: 'Namuna maqola 2', url: '#' }] },
    ],
  },
}

type Row = (typeof people)[number]

// Namunada sharif ism oxirida turadi ("… qizi" / "… o‘g‘li" ikki so'z)
function patronymicOf(name: string) {
  const words = name.split(' ')
  if (words.length < 3) return null
  return /^(qizi|o‘g‘li)$/.test(words.at(-1)!) ? words.slice(-2).join(' ') : words.at(-1)!
}

// HEMIS lavozim kodlari: 11–15 — o'qituvchilik lavozimlari (frontend shunga qarab tartiblaydi);
// qolgan kodlar namunaviy, HEMIS'dagi haqiqiysini backend beradi
const positionCodes: Record<string, string> = {
  'trainee': '11', 'assistant': '12', 'senior-lecturer': '13', 'docent': '14', 'professor': '15',
  'rector': '21', 'first-vice-academic': '22', 'vice-research': '23', 'vice-international': '23', 'vice-youth': '23',
  'rector-assistant': '24', 'press-secretary': '25', 'dean': '31', 'deputy-dean': '32', 'tutor': '33', 'head-chair': '34',
  'sysadmin': '41', 'engineer': '42', 'engineer-1': '43', 'head-section': '44', 'head-office': '45', 'chief-specialist': '46',
}
const FORM_MAIN = { code: '11', name: 'Asosiy ish joy' }
const FORM_INNER = { code: '12', name: 'O‘rindoshlik (ichki-asosiy)' }
const WORKING = { code: '11', name: 'Ishlamoqda' }

function employment(dept: string, position: string, lang: Locale, form = FORM_MAIN): HemisEmployment {
  const code = positionCodes[position]!
  const group = departments[dept]!.group
  return {
    department: { id: dept, name: departments[dept]!.name[lang] },
    position: { code, name: positions[position]![lang] },
    form,
    rate: 1,
    status: WORKING,
    type: /^1[1-5]$/.test(code)
      ? { code: '12', name: 'Professor-o‘qituvchi xodim' }
      : group === 'lead' ? { code: '11', name: 'Administrativ-boshqaruv xodim' } : { code: '10', name: 'Boshqa' },
  }
}

function summary([id, name, dept, position]: Row, lang: Locale): StaffSummary {
  const extra = extras[id]
  return {
    id,
    name,
    patronymic: patronymicOf(name),
    photo: null,
    photoFallback: null,
    employments: extra?.employments
      ? extra.employments.map(([d, p], i) => employment(d, p, lang, i ? FORM_INNER : FORM_MAIN))
      : [employment(dept, position, lang)],
    group: departments[dept]!.group,
  }
}

// Qidiruvda tutuq belgilari va katta-kichik harf farqi hisobga olinmaydi: "yo'ldoshev" = "Yo‘ldoshev"
const fold = (s: string) => s.toLowerCase().replace(/[‘’'`ʻʼ]/g, '')

export interface StaffQuery {
  q?: string
  department?: string
  group?: StaffGroup | 'all'
  page?: number
  perPage?: number
  /** Saytda yashirilgan xodimlar (admin panel) */
  exclude?: Set<string>
}

export function getMockStaffList(lang: Locale, query: StaffQuery): StaffList {
  const words = fold(query.q ?? '').split(/\s+/).filter(Boolean)
  const base = people.filter(([id, name, dept]) =>
    !query.exclude?.has(id) && (!query.department || dept === query.department) && words.every(w => fold(name).includes(w)))

  const groupOf = (row: Row) => departments[row[2]]!.group
  const groups = { all: base.length, lead: 0, faculty: 0, chair: 0, unit: 0 }
  for (const row of base) groups[groupOf(row)]++

  const filtered = !query.group || query.group === 'all' ? base : base.filter(row => groupOf(row) === query.group)
  const perPage = query.perPage ?? 24
  const page = Math.min(Math.max(1, query.page ?? 1), Math.max(1, Math.ceil(filtered.length / perPage)))

  const deptList: StaffDepartment[] = Object.entries(departments)
    .map(([id, d]) => ({ id, name: d.name[lang], group: d.group, count: people.filter(p => p[2] === id).length }))
    .sort((a, b) => a.name.localeCompare(b.name, lang))

  return {
    items: filtered.slice((page - 1) * perPage, page * perPage).map(row => summary(row, lang)),
    total: filtered.length,
    page,
    perPage,
    groups,
    departments: deptList,
    summary: { staff: people.length, departments: deptList.length },
  }
}

export function getMockStaffProfile(lang: Locale, id: string): StaffProfile | null {
  const row = people.find(p => p[0] === id)
  if (!row) return null
  const extra = extras[id] ?? {}
  const base = summary(row, lang)
  const isDemo = id === DEMO_USER
  return {
    ...base,
    photo: isDemo ? cabinet.ownPhoto : base.photo,
    about: extra.about ? extra.about[lang] || extra.about.uz || null : null,
    contacts: extra.contacts ?? [],
    socials: extra.socials ?? [],
    science: extra.science ?? [],
    // Demo xodimda hujjatlar kabinetdan: faqat "Staff'da ko'rinadi" va bo'sh bo'lmaganlari
    documents: isDemo ? demoPublicDocuments(lang) : extra.documents ?? [],
    cardImage: null,
  }
}

// ---------------------------------------------------------------------------
// Xodim kabineti (dashboard) — demo: saytga kirgan xodim rektor (9300) deb hisoblanadi.
// O'zgarishlar faqat server xotirasida (dev server qayta ishga tushsa — tiklanadi).
// Haqiqiy backend'da: HEMIS (my.gov) orqali kirgan xodimning sessiyasi bo'yicha.

export const DEMO_USER = '9300'

const cabinet = {
  ownPhoto: null as string | null,
  visibility: { cv: true, books: true, articles: true } as Record<StaffDocSection, boolean>,
  docs: {
    cv: [{ id: 'cv-1', title: { uz: 'CV (namuna)', ru: 'Резюме (пример)', en: 'CV (sample)', zh: '' }, url: '#', createdAt: '2026-10-01' }],
    books: [],
    presentations: [{ id: 'pr-1', title: { uz: 'Namuna taqdimot', ru: 'Пример презентации', en: 'Sample presentation', zh: '' }, url: '#', createdAt: '2026-09-20' }],
    articles: [
      { id: 'ar-1', title: { uz: 'Namuna maqola 1', ru: 'Пример статьи 1', en: 'Sample article 1', zh: '' }, url: '#', createdAt: '2026-10-12' },
      { id: 'ar-2', title: { uz: 'Namuna maqola 2', ru: 'Пример статьи 2', en: 'Sample article 2', zh: '' }, url: '#', createdAt: '2026-09-03' },
    ],
    videos: [],
  } as Record<CabinetDocSection, CabinetDocument[]>,
}

/** Nom: so'ralgan tilda; xitoychasi bo'lmasa inglizcha, u ham bo'lmasa o'zbekcha (oldingi saytdagi qoida) */
export function docTitle(title: LocalizedText, lang: Locale) {
  return title[lang] || (lang === 'zh' ? title.en : '') || title.uz
}

function demoPublicDocuments(lang: Locale): StaffProfile['documents'] {
  return (['cv', 'books', 'articles'] as const)
    .filter(s => cabinet.visibility[s] && cabinet.docs[s].length)
    .map(s => ({ section: s, items: cabinet.docs[s].map(d => ({ title: docTitle(d.title, lang), url: d.url })) }))
}

export function getMockCabinet(lang: Locale): StaffCabinet {
  const extra = extras[DEMO_USER]!
  const about = { uz: '', ru: '', en: '', zh: '', ...extra.about }
  const documents = Object.fromEntries((Object.keys(cabinet.docs) as CabinetDocSection[]).map(s => [s, {
    count: cabinet.docs[s].length,
    visible: s === 'presentations' || s === 'videos' ? false : cabinet.visibility[s as StaffDocSection],
  }])) as StaffCabinet['documents']
  return {
    profile: getMockStaffProfile(lang, DEMO_USER)!,
    // Tug'ilgan kun ataylab berilmagan (shaxsiy ma'lumot) — haqiqiysini backend HEMIS'dan beradi
    hemis: { firstName: 'Ilxomjon', lastName: 'Tuxtasinov', patronymic: 'Madaminovich', birthDate: null, phone: '+998 71 230 12 91', email: 'rector@uzswlu.uz' },
    about,
    hasOwnPhoto: !!cabinet.ownPhoto,
    documents,
  }
}

export function patchMockCabinet(patch: CabinetPatch) {
  const extra = extras[DEMO_USER]!
  if (patch.about) extra.about = { ...patch.about }
  if (patch.contacts) extra.contacts = patch.contacts
  if (patch.socials) extra.socials = patch.socials
  if (patch.science) extra.science = patch.science
  if (patch.visibility) Object.assign(cabinet.visibility, patch.visibility)
}

export function setMockPhoto(dataUrl: string | null) {
  cabinet.ownPhoto = dataUrl
}

export function listMockDocs(section: CabinetDocSection) {
  return cabinet.docs[section]
}

export function addMockDoc(section: CabinetDocSection, doc: Omit<CabinetDocument, 'id' | 'createdAt'>) {
  const item: CabinetDocument = { ...doc, id: `${section}-${Date.now()}`, createdAt: new Date().toISOString() }
  cabinet.docs[section].unshift(item)
  return item
}

export function deleteMockDoc(section: CabinetDocSection, id: string) {
  const list = cabinet.docs[section]
  const i = list.findIndex(d => d.id === id)
  if (i < 0) return false
  list.splice(i, 1)
  return true
}
