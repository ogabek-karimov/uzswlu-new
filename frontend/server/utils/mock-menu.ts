import type { MenuGroup, MenuLink } from '#shared/types/api'

// VAQTINCHALIK MA'LUMOT — asosiy menyu uzswlu.uz'dagi bilan bir xil (2026-10-21 holatiga):
// bo'limlar, tartib va manzillar (slug) o'zgarmagan, shunda eski havolalar va Google'dagi o'rinlar saqlanadi.
// Tuzatilgan: "BRM 9" sarlavhasi saytda bo'sh edi, BRM 11 va 13 dagi imlo xatolari.

type L = Record<Locale, string>
type Link = { t: L; url: string; file?: 'pdf'; highlight?: boolean; sdg?: number }
type Group = { id: string; t: L; d?: L; url?: string; overview?: string; links: Link[] }

const OLD = 'https://uzswlu.uz'

const menu: Group[] = [
  {
    id: 'university',
    t: { uz: 'Universitet', ru: 'Университет', en: 'University', zh: '大学概况' },
    overview: '/universitet-haqida',
    d: { uz: 'Tarix, tuzilma, rahbariyat va kampus — universitet haqida hammasi.', ru: 'История, структура, руководство и кампус — всё об университете.', en: 'History, structure, leadership and campus — all about the university.', zh: '历史、机构、领导与校园——关于大学的一切。' },
    links: [
      { t: { uz: 'Universitet haqida', ru: 'Об университете', en: 'About the University', zh: '学校简介' }, url: '/universitet-haqida' },
      { t: { uz: 'Rektorat', ru: 'Ректорат', en: 'Rectorate', zh: '校领导' }, url: '/rektorat' },
      { t: { uz: 'Tuzilma', ru: 'Структура', en: 'Structure', zh: '组织机构' }, url: '/tuzilma' },
      { t: { uz: 'Universitet nizomi', ru: 'Устав университета', en: 'University Charter', zh: '大学章程' }, url: `${OLD}/backend/web/files/O%27zDJTU%20nizomi.pdf`, file: 'pdf' },
      { t: { uz: 'Bo‘limlar', ru: 'Отделы', en: 'Offices', zh: '职能部门' }, url: '/bolimlar' },
      { t: { uz: 'Fakultetlar va kafedralar', ru: 'Факультеты и кафедры', en: 'Faculties and Departments', zh: '学院与教研室' }, url: '/fakultetlar-va-kafedralar' },
      { t: { uz: 'Universitet tarixi', ru: 'История университета', en: 'History', zh: '校史' }, url: '/universitet-tarixi' },
      { t: { uz: 'Staff', ru: 'Сотрудники', en: 'Staff', zh: '教职工' }, url: '/staff' },
      { t: { uz: 'Universitet ta’lim siyosati', ru: 'Образовательная политика', en: 'Education Policy', zh: '教育政策' }, url: '/universitet-talim-siyosati' },
      { t: { uz: 'Axborot-resurs markazi', ru: 'Информационно-ресурсный центр', en: 'Information Resource Centre', zh: '信息资源中心' }, url: '/axborot-resurs-markazi' },
      { t: { uz: 'Yoshlar ittifoqi boshlang‘ich tashkiloti', ru: 'Первичная организация Союза молодёжи', en: 'Youth Union', zh: '青年联盟基层组织' }, url: '/yoshlar-ittifoqi-boshlangich-tashkiloti' },
      { t: { uz: 'O‘quv binolari', ru: 'Учебные корпуса', en: 'Academic Buildings', zh: '教学楼' }, url: '/oquv-binolari' },
      { t: { uz: 'Mavjud qulayliklar', ru: 'Условия и удобства', en: 'Facilities', zh: '校园设施' }, url: '/mavjud-qulayliklar' },
      { t: { uz: 'Innovatsion yechimlar', ru: 'Инновационные решения', en: 'Innovative Solutions', zh: '创新方案' }, url: '/innovatsion-yechimlar' },
      { t: { uz: 'O‘zbekiston–Xitoy II ta’lim forumi dasturi', ru: 'II Узбекско-китайский образовательный форум', en: '2nd Uzbekistan–China Education Forum', zh: '第二届乌中教育论坛' }, url: '/ozbekiston-xitoy-ii-talim-forumi-dasturi' },
      { t: { uz: 'Ochiq eshiklar kunlari', ru: 'Дни открытых дверей', en: 'Open Days', zh: '开放日' }, url: '/ochiq-eshiklar-kunlari' },
    ],
  },
  {
    id: 'applicants',
    t: { uz: 'Abituriyentlar', ru: 'Абитуриентам', en: 'Admissions', zh: '招生' },
    overview: '/qabul-20262027',
    d: { uz: 'Qabul, yönalişlar, kontrakt va grantlar — kerakli hamma narsa.', ru: 'Приём, направления, стоимость и гранты — всё необходимое.', en: 'Admission, programmes, tuition and grants — everything you need.', zh: '招生、专业、学费与奖学金——所需一切。' },
    links: [
      { t: { uz: 'Qo‘shma ta’lim dasturlari', ru: 'Совместные образовательные программы', en: 'Joint Programmes', zh: '合作办学项目' }, url: '/qoshma-talim-dasturlari' },
      { t: { uz: 'Nima uchun bu universitet', ru: 'Почему наш университет', en: 'Why UzSWLU', zh: '为什么选择我们' }, url: '/nima-uchun-bu-universitet' },
      { t: { uz: 'To‘lov-kontrakt shartnomalari', ru: 'Договоры на платное обучение', en: 'Tuition Contracts', zh: '学费合同' }, url: '/tolov-kontrakt-shartnomalari' },
      { t: { uz: 'Talabalarga eslatma', ru: 'Памятка студентам', en: 'Student Guide', zh: '学生须知' }, url: '/talabalarga-eslatma' },
      { t: { uz: 'Bitiruvchilar klubi', ru: 'Клуб выпускников', en: 'Alumni Club', zh: '校友会' }, url: '/bitiruvchilar-klubi' },
      { t: { uz: 'To‘lov-kontrakt miqdori', ru: 'Стоимость обучения', en: 'Tuition Fees', zh: '学费标准' }, url: '/tolov-kontrakt-miqdori' },
      { t: { uz: 'Stipendiyalar', ru: 'Стипендии', en: 'Scholarships', zh: '奖学金' }, url: '/stipendiyalar' },
      { t: { uz: 'Xalqaro talabalar va o‘qituvchilar uchun', ru: 'Иностранным студентам и преподавателям', en: 'International Students and Faculty', zh: '国际学生与教师' }, url: '/xalqaro-talabalar-va-oqituvchilar-uchun' },
      { t: { uz: 'Rektor tabrigi', ru: 'Приветствие ректора', en: 'Rector’s Welcome', zh: '校长致辞' }, url: '/rektor-tabrigi' },
      { t: { uz: 'Hamkorlarimiz', ru: 'Наши партнёры', en: 'Our Partners', zh: '合作伙伴' }, url: '/hamkorlarimiz' },
      { t: { uz: 'Qabul – 2026/2027', ru: 'Приём – 2026/2027', en: 'Admission 2026/2027', zh: '2026/2027招生' }, url: '/qabul-20262027', highlight: true },
      { t: { uz: 'Magistrlik dasturlari', ru: 'Программы магистратуры', en: 'Master’s Programmes', zh: '硕士项目' }, url: '/magistrlik-dasturlari' },
      { t: { uz: 'PhD dasturlari', ru: 'Программы PhD', en: 'PhD Programmes', zh: '博士项目' }, url: '/phd-dasturlari' },
      { t: { uz: 'Sharoitlar', ru: 'Условия', en: 'Conditions', zh: '办学条件' }, url: `${OLD}/backend/web/uploads/pagepdf/icon/17437679069420.pdf`, file: 'pdf' },
      { t: { uz: 'Vakansiya', ru: 'Вакантные места', en: 'Vacant Places', zh: '空缺名额' }, url: '/vakansiya' },
      { t: { uz: 'Ta’lim grantlar soni', ru: 'Количество грантов', en: 'Number of Grants', zh: '奖学金名额' }, url: '/talim-grantlar-soni' },
    ],
  },
  {
    id: 'activity',
    t: { uz: 'Faoliyat', ru: 'Деятельность', en: 'Activities', zh: '学校工作' },
    overview: '/ilmiy-faoliyat',
    d: { uz: 'Ilm-fan, xalqaro hamkorlik, hujjatlar va universitet hayoti.', ru: 'Наука, международное сотрудничество, документы и жизнь университета.', en: 'Research, international cooperation, documents and university life.', zh: '科研、国际合作、文件与校园生活。' },
    links: [
      { t: { uz: 'Korrupsiyaga qarshi kurashish', ru: 'Противодействие коррупции', en: 'Anti-Corruption', zh: '反腐败' }, url: '/korrupsiyaga-qarshi-kurashish' },
      { t: { uz: 'Yashil universitet', ru: 'Зелёный университет', en: 'Green University', zh: '绿色大学' }, url: '/yashil-universitet' },
      { t: { uz: 'Madaniy-ma’rifiy faoliyat', ru: 'Культурно-просветительская деятельность', en: 'Cultural Activities', zh: '文化教育活动' }, url: '/madaniy-marifiy-faoliyat' },
      { t: { uz: 'Universitet bitiruvchilari haqida', ru: 'О выпускниках университета', en: 'About Our Graduates', zh: '毕业生情况' }, url: '/universitet-bitiruvchilari-haqida' },
      { t: { uz: 'Xalqaro aloqalar', ru: 'Международные связи', en: 'International Relations', zh: '国际交流' }, url: '/xalqaro-aloqalar' },
      { t: { uz: 'Moliyaviy faoliyat', ru: 'Финансовая деятельность', en: 'Financial Activities', zh: '财务工作' }, url: '/moliyaviy-faoliyat' },
      { t: { uz: 'Ilmiy faoliyat', ru: 'Научная деятельность', en: 'Research', zh: '科学研究' }, url: '/ilmiy-faoliyat' },
      { t: { uz: 'O‘quv-uslubiy hujjatlar', ru: 'Учебно-методические документы', en: 'Teaching Materials', zh: '教学文件' }, url: '/oquv-uslubiy-hujjatlar' },
      { t: { uz: 'Me’yoriy hujjatlar', ru: 'Нормативные документы', en: 'Regulations', zh: '规章制度' }, url: '/meyoriy-hujjatlar' },
      { t: { uz: 'Xalqaro akkreditatsiya', ru: 'Международная аккредитация', en: 'International Accreditation', zh: '国际认证' }, url: '/xalqaro-akkreditatsiya' },
      { t: { uz: '“Kelajakka qadam” markazi', ru: 'Центр «Шаг в будущее»', en: '“Step into the Future” Centre', zh: '“迈向未来”中心' }, url: '/kelajakka-qadam-markazi' },
    ],
  },
  {
    id: 'news',
    t: { uz: 'Yangiliklar', ru: 'Новости', en: 'News', zh: '新闻' },
    url: '/yangiliklar',
    links: [],
  },
  {
    id: 'sdg',
    t: { uz: 'BRM', ru: 'ЦУР', en: 'SDGs', zh: '可持续发展' },
    overview: '/brm',
    d: { uz: 'Barqaror rivojlaniş maqsadlari: universitetning 17 ta BMT maqsadi böyiça işlari.', ru: 'Цели устойчивого развития: работа университета по 17 целям ООН.', en: 'Sustainable Development Goals: the university’s work on the 17 UN goals.', zh: '可持续发展目标：大学围绕联合国17项目标开展的工作。' },
    links: [
      { sdg: 1, url: '/brm-1-ota-qashshoqlikka-barham-berish', t: { uz: 'O‘ta qashshoqlikka barham berish', ru: 'Ликвидация нищеты', en: 'No Poverty', zh: '无贫穷' } },
      { sdg: 2, url: '/brm-2-ochlikka-barham-berish', t: { uz: 'Ochlikka barham berish', ru: 'Ликвидация голода', en: 'Zero Hunger', zh: '零饥饿' } },
      { sdg: 3, url: '/brm-3-soglik-va-farovonlik', t: { uz: 'Sog‘lik va farovonlik', ru: 'Здоровье и благополучие', en: 'Good Health and Well-being', zh: '良好健康与福祉' } },
      { sdg: 4, url: '/brm-4-sifatli-talim', t: { uz: 'Sifatli ta’lim', ru: 'Качественное образование', en: 'Quality Education', zh: '优质教育' } },
      { sdg: 5, url: '/brm-5-gender-tengligi', t: { uz: 'Gender tengligi', ru: 'Гендерное равенство', en: 'Gender Equality', zh: '性别平等' } },
      { sdg: 6, url: '/brm-6-toza-suv-va-sanitariya', t: { uz: 'Toza suv va sanitariya', ru: 'Чистая вода и санитария', en: 'Clean Water and Sanitation', zh: '清洁饮水和卫生设施' } },
      { sdg: 7, url: '/brm-7-arzon-va-toza-energiya', t: { uz: 'Arzon va toza energiya', ru: 'Недорогая и чистая энергия', en: 'Affordable and Clean Energy', zh: '经济适用的清洁能源' } },
      { sdg: 8, url: '/brm-8-munosib-ish-orinlari-va-iqtisodiy-osish', t: { uz: 'Munosib ish o‘rinlari va iqtisodiy o‘sish', ru: 'Достойная работа и экономический рост', en: 'Decent Work and Economic Growth', zh: '体面工作和经济增长' } },
      { sdg: 9, url: '/brm-9', t: { uz: 'Sanoat, innovatsiya va infratuzilma', ru: 'Индустриализация, инновации и инфраструктура', en: 'Industry, Innovation and Infrastructure', zh: '产业、创新和基础设施' } },
      { sdg: 10, url: '/brm-10-tengsizlikni-kamaytirish', t: { uz: 'Tengsizlikni kamaytirish', ru: 'Уменьшение неравенства', en: 'Reduced Inequalities', zh: '减少不平等' } },
      { sdg: 11, url: '/brm-11-barqaror-shahrlar-va-aholi-yahash-joylari', t: { uz: 'Barqaror shaharlar va aholi yashash joylari', ru: 'Устойчивые города и населённые пункты', en: 'Sustainable Cities and Communities', zh: '可持续城市和社区' } },
      { sdg: 12, url: '/brm-12-masuliyatli-istemol-va-ishlab-chiqarish', t: { uz: 'Mas’uliyatli iste’mol va ishlab chiqarish', ru: 'Ответственное потребление и производство', en: 'Responsible Consumption and Production', zh: '负责任消费和生产' } },
      { sdg: 13, url: '/brm-13-iqlim-ozgarishga-qarshi-kurashish', t: { uz: 'Iqlim o‘zgarishiga qarshi kurashish', ru: 'Борьба с изменением климата', en: 'Climate Action', zh: '气候行动' } },
      { sdg: 14, url: '/brm-14-dengiz-ekotizimlarini-asrash', t: { uz: 'Dengiz ekotizimlarini asrash', ru: 'Сохранение морских экосистем', en: 'Life Below Water', zh: '水下生物' } },
      { sdg: 15, url: '/brm-15-quruqlikdagi-ekotizimlarni-asrash', t: { uz: 'Quruqlikdagi ekotizimlarni asrash', ru: 'Сохранение экосистем суши', en: 'Life on Land', zh: '陆地生物' } },
      { sdg: 16, url: '/brm-16-tinchlik-adolat-va-samarali-boshqaruv', t: { uz: 'Tinchlik, adolat va samarali boshqaruv', ru: 'Мир, правосудие и эффективные институты', en: 'Peace, Justice and Strong Institutions', zh: '和平、正义与强大机构' } },
      { sdg: 17, url: '/brm-17-barqaror-rivojlanish-yolida-hamkorlik', t: { uz: 'Barqaror rivojlanish yo‘lida hamkorlik', ru: 'Партнёрство во имя устойчивого развития', en: 'Partnerships for the Goals', zh: '促进目标实现的伙伴关系' } },
      { url: '/greenmetrics', t: { uz: 'Greenmetrics', ru: 'GreenMetric', en: 'GreenMetric', zh: 'GreenMetric' } },
      { url: '/sdg-report', t: { uz: 'SDG report', ru: 'Отчёт по ЦУР', en: 'SDG Report', zh: 'SDG报告' } },
      { url: '/talim-va-barqarorlik', t: { uz: 'Ta’lim va barqarorlik', ru: 'Образование и устойчивость', en: 'Education and Sustainability', zh: '教育与可持续发展' } },
      { url: '/greenmetrics-2025', t: { uz: 'Greenmetrics 2025', ru: 'GreenMetric 2025', en: 'GreenMetric 2025', zh: 'GreenMetric 2025' } },
    ],
  },
  {
    id: 'programs',
    t: { uz: 'Ta’lim yo‘nalishlari', ru: 'Направления обучения', en: 'Programmes', zh: '专业设置' },
    overview: '/bakalavriat',
    d: { uz: 'Bakalavriat va magistratura yönalişlari.', ru: 'Направления бакалавриата и магистратуры.', en: 'Bachelor’s and master’s programmes.', zh: '本科与硕士专业。' },
    links: [
      { t: { uz: 'Bakalavriat', ru: 'Бакалавриат', en: 'Bachelor’s', zh: '本科' }, url: '/bakalavriat' },
      { t: { uz: 'Magistratura', ru: 'Магистратура', en: 'Master’s', zh: '硕士' }, url: '/magistratura' },
    ],
  },
  {
    id: 'video',
    t: { uz: 'Video', ru: 'Видео', en: 'Video', zh: '视频' },
    overview: '/video-darsliklar',
    d: { uz: 'Onlayn translatsiyalar va video darsliklar.', ru: 'Онлайн-трансляции и видеоуроки.', en: 'Live streams and video lessons.', zh: '在线直播与视频课程。' },
    links: [
      { t: { uz: 'Online translatsiya', ru: 'Онлайн-трансляция', en: 'Live Stream', zh: '在线直播' }, url: '/online-translatsiya' },
      { t: { uz: 'Video darsliklar', ru: 'Видеоуроки', en: 'Video Lessons', zh: '视频课程' }, url: '/video-darsliklar' },
    ],
  },
  {
    id: 'contact',
    t: { uz: 'Aloqa', ru: 'Контакты', en: 'Contact', zh: '联系我们' },
    url: '/aloqa',
    links: [],
  },
]

export function getMockMenu(lang: Locale): MenuGroup[] {
  return menu.map(g => ({
    id: g.id,
    title: g.t[lang],
    description: g.d?.[lang] ?? null,
    url: g.url ?? null,
    overview: g.overview ?? null,
    links: g.links.map((l): MenuLink => ({
      title: l.t[lang],
      url: l.url,
      file: l.file ?? null,
      highlight: l.highlight ?? false,
      sdg: l.sdg ?? null,
    })),
  }))
}
