import type { Attachment, SdgGoal, SdgGoalSummary, SdgOverview } from '#shared/types/api'

// VAQTINCHALIK MA'LUMOT — BRM (barqaror rivojlanish maqsadlari) sahifalari.
// Reytinglar: UI GreenMetric 2026 va THE Impact Rankings 2025 (universitet bannerlaridan).
// BRM 6 bo'limlari va hujjatlari uzswlu.uz/brm-6-toza-suv-va-sanitariya sahifasidan (2026-10-21).

type L = Record<Locale, string>

const OLD = 'https://uzswlu.uz'

// THE Impact Rankings 2025: [o'rin, ball]
const impact: [string | null, string | null][] = [
  ['801–1000', '36.9'], ['801+', '12.6'], ['1001–1500', '30.3'], ['30', '82.4'], ['201–300', '60.0'], ['401–600', '43.5'],
  ['1001+', '24.8'], ['801–1000', '41.0'], ['601–800', '39.5'], ['601–800', '42.3'], ['401–600', '44.5'], ['401–600', '48.1'],
  ['601–800', '33.9'], [null, null], ['301–400', '51.8'], ['1001+', '30.5'], ['1501+', '30.9'],
]

// BMT maqsadlari ta'rifi (rasmiy matn)
const subtitles: L[] = [
  { uz: 'Barça joylarda qaşşoqlikning barça şakllariga barham beriş.', ru: 'Повсеместная ликвидация нищеты во всех её формах.', en: 'End poverty in all its forms everywhere.', zh: '在全世界消除一切形式的贫困。' },
  { uz: 'Oçlikka barham beriş, oziq-ovqat xavfsizligini ta’minlaş, ovqatlanişni yaxşilaş va qişloq xöjaligining barqaror rivojlanişiga kömaklaşiş.', ru: 'Ликвидация голода, обеспечение продовольственной безопасности, улучшение питания и содействие устойчивому развитию сельского хозяйства.', en: 'End hunger, achieve food security and improved nutrition and promote sustainable agriculture.', zh: '消除饥饿，实现粮食安全，改善营养状况和促进可持续农业。' },
  { uz: 'Har qanday yoşdagi barça insonlar uçun soğlom turmuş tarzini ta’minlaş va farovonligiga kömaklaşiş.', ru: 'Обеспечение здорового образа жизни и содействие благополучию для всех в любом возрасте.', en: 'Ensure healthy lives and promote well-being for all at all ages.', zh: '确保健康的生活方式，促进各年龄段人群的福祉。' },
  { uz: 'Inklyuziv va adolatli sifatli ta’limni ta’minlaş hamda hamma uçun umrbod ta’lim oliş imkoniyatlarini rağbatlantiriş.', ru: 'Обеспечение всеохватного и справедливого качественного образования и поощрение возможности обучения на протяжении всей жизни для всех.', en: 'Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all.', zh: '确保包容和公平的优质教育，让全民终身享有学习机会。' },
  { uz: 'Gender tengligini ta’minlaş, barça xotin-qizlarning huquq va imkoniyatlarini kengaytiriş.', ru: 'Обеспечение гендерного равенства и расширение прав и возможностей всех женщин и девочек.', en: 'Achieve gender equality and empower all women and girls.', zh: '实现性别平等，增强所有妇女和女童的权能。' },
  { uz: 'Hamma uçun suv va sanitariya mavjudligi hamda ulardan barqaror foydalanişni ta’minlaş.', ru: 'Обеспечение наличия и рационального использования водных ресурсов и санитарии для всех.', en: 'Ensure availability and sustainable management of water and sanitation for all.', zh: '为所有人提供水和环境卫生并对其进行可持续管理。' },
  { uz: 'Hamma uçun arzon, işonçli, barqaror va zamonaviy energiyadan foydalaniş imkoniyatini ta’minlaş.', ru: 'Обеспечение всеобщего доступа к недорогим, надёжным, устойчивым и современным источникам энергии.', en: 'Ensure access to affordable, reliable, sustainable and modern energy for all.', zh: '确保人人获得负担得起的、可靠和可持续的现代能源。' },
  { uz: 'Barqaror va inklyuziv iqtisodiy ösişga, töliq va samarali bandlikka hamda hamma uçun munosib mehnatga kömaklaşiş.', ru: 'Содействие поступательному, всеохватному и устойчивому экономическому росту, полной и производительной занятости и достойной работе для всех.', en: 'Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all.', zh: '促进持久、包容和可持续的经济增长，促进充分的生产性就业和人人获得体面工作。' },
  { uz: 'Mustahkam infratuzilma yaratiş, inklyuziv va barqaror sanoatlaştiriş hamda innovatsiyalarga kömaklaşiş.', ru: 'Создание стойкой инфраструктуры, содействие всеохватной и устойчивой индустриализации и инновациям.', en: 'Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation.', zh: '建造具备抵御灾害能力的基础设施，促进具有包容性的可持续工业化，推动创新。' },
  { uz: 'Mamlakatlar içida va ular örtasidagi tengsizlikni kamaytiriş.', ru: 'Сокращение неравенства внутри стран и между ними.', en: 'Reduce inequality within and among countries.', zh: '减少国家内部和国家之间的不平等。' },
  { uz: 'Şahar va aholi punktlarini inklyuziv, xavfsiz, mustahkam va barqaror qiliş.', ru: 'Обеспечение открытости, безопасности, жизнестойкости и экологической устойчивости городов и населённых пунктов.', en: 'Make cities and human settlements inclusive, safe, resilient and sustainable.', zh: '建设包容、安全、有抵御灾害能力和可持续的城市和人类住区。' },
  { uz: 'Barqaror iste’mol va işlab çiqariş modellariga ötişni ta’minlaş.', ru: 'Обеспечение перехода к рациональным моделям потребления и производства.', en: 'Ensure sustainable consumption and production patterns.', zh: '采用可持续的消费和生产模式。' },
  { uz: 'Iqlim özgarişi va uning oqibatlariga qarşi kuraşiş böyiça şoşilinç çoralar köriş.', ru: 'Принятие срочных мер по борьбе с изменением климата и его последствиями.', en: 'Take urgent action to combat climate change and its impacts.', zh: '采取紧急行动应对气候变化及其影响。' },
  { uz: 'Barqaror rivojlaniş uçun okeanlar, dengizlar va dengiz resurslarini asraş hamda oqilona foydalaniş.', ru: 'Сохранение и рациональное использование океанов, морей и морских ресурсов в интересах устойчивого развития.', en: 'Conserve and sustainably use the oceans, seas and marine resources for sustainable development.', zh: '保护和可持续利用海洋和海洋资源以促进可持续发展。' },
  { uz: 'Quruqlikdagi ekotizimlarni himoya qiliş, tiklaş va oqilona foydalaniş, örmonlarni boşqariş, çöllanişga qarşi kuraşiş, yer degradatsiyasi va biologik xilma-xillik yöqolişini töxtatiş.', ru: 'Защита, восстановление и рациональное использование экосистем суши, рациональное лесопользование, борьба с опустыниванием, прекращение деградации земель и утраты биоразнообразия.', en: 'Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification, and halt land degradation and biodiversity loss.', zh: '保护、恢复和促进可持续利用陆地生态系统，可持续管理森林，防治荒漠化，制止土地退化，遏制生物多样性的丧失。' },
  { uz: 'Tinç va inklyuziv jamiyat qurişga kömaklaşiş, hamma uçun odil sudlovdan foydalanişni ta’minlaş hamda barça darajalarda samarali va hisobdor institutlarni yaratiş.', ru: 'Содействие построению миролюбивого и открытого общества, обеспечение доступа к правосудию для всех и создание эффективных и подотчётных учреждений на всех уровнях.', en: 'Promote peaceful and inclusive societies, provide access to justice for all and build effective, accountable and inclusive institutions at all levels.', zh: '创建和平、包容的社会，让所有人都能诉诸司法，在各级建立有效、负责和包容的机构。' },
  { uz: 'Amalga oşiriş vositalarini kuçaytiriş va barqaror rivojlaniş yölida global hamkorlikni faollaştiriş.', ru: 'Укрепление средств осуществления и активизация Глобального партнёрства в интересах устойчивого развития.', en: 'Strengthen the means of implementation and revitalize the Global Partnership for Sustainable Development.', zh: '加强执行手段，重振可持续发展全球伙伴关系。' },
]

const SECTION_SAMPLE: L = {
  uz: '<p>Bölim matni, rasmlar va ölçov natijalari admin panelda şu bölim uçun kiritiladi. Hozir namunaviy matn turibdi.</p>',
  ru: '<p>Текст раздела, фотографии и результаты измерений добавляются в админ-панели. Сейчас показан демонстрационный текст.</p>',
  en: '<p>The section text, photos and measurement results are added in the admin panel. Sample text is shown for now.</p>',
  zh: '<p>本栏目的文字、图片和测量结果通过管理后台添加，目前显示的是示例文字。</p>',
}

const OVERVIEW: L = { uz: 'Umumiy ma’lumot', ru: 'Общие сведения', en: 'Overview', zh: '概述' }

// BRM 6 ichki bo'limlari — saytdagi bilan bir xil
const water: [string, L][] = [
  ['measurement', { uz: 'Suvni o‘lchash', ru: 'Измерение воды', en: 'Water measurement', zh: '水量计量' }],
  ['treatment', { uz: 'Suvni tozalash', ru: 'Очистка воды', en: 'Water treatment', zh: '水处理' }],
  ['pollution', { uz: 'Suv ifloslanishi', ru: 'Загрязнение воды', en: 'Water pollution', zh: '水污染' }],
  ['standard', { uz: 'Suv standarti', ru: 'Стандарт воды', en: 'Water standards', zh: '水质标准' }],
  ['protocol', { uz: 'Suv bayonnomasi', ru: 'Водный протокол', en: 'Water protocol', zh: '用水规程' }],
  ['groundwater', { uz: 'Yer osti suvlari', ru: 'Подземные воды', en: 'Groundwater', zh: '地下水' }],
  ['transport', { uz: 'Transport', ru: 'Транспорт', en: 'Transport', zh: '交通' }],
]

function goalsSummary(lang: Locale): SdgGoalSummary[] {
  return getMockMenu(lang).flatMap(g => g.links).filter(l => l.sdg).map((l) => {
    const n = l.sdg!
    const [rank, score] = impact[n - 1]!
    return { n, url: l.url, title: l.title, rank, score }
  })
}

const T = (value: L, lang: Locale) => value[lang]

export function getMockSdgOverview(lang: Locale): SdgOverview {
  const top: L = { uz: 'Özbekistonda #1', ru: '№1 в Узбекистане', en: '#1 in Uzbekistan', zh: '乌兹别克斯坦第1名' }
  const water6 = '/brm-6-toza-suv-va-sanitariya'
  const page = (title: string, url: string, kind: Attachment['kind'] = 'link'): Attachment => ({ title, url, kind, meta: null })

  return {
    greenmetric: {
      year: 2026,
      world: { rank: '#512', change: 57 },
      asia: { rank: '#296', change: 28 },
      country: { rank: '#11', change: 2 },
      highlight: { text: T({ uz: 'Water yönalişi böyiça Özbekistonda #1', ru: 'Water: №1 в Узбекистане', en: 'Water: #1 in Uzbekistan', zh: '水资源类别：乌兹别克斯坦第1名' }, lang), url: water6 },
    },
    categories: [
      { code: 'SI', title: T({ uz: 'Infratuzilma', ru: 'Инфраструктура', en: 'Infrastructure', zh: '基础设施' }, lang), subtitle: 'Setting & Infrastructure', url: '/greenmetrics-2025' },
      { code: 'EC', title: T({ uz: 'Energiya va iqlim', ru: 'Энергия и климат', en: 'Energy and climate', zh: '能源与气候' }, lang), subtitle: 'Energy & Climate Change', url: '/greenmetrics-2025' },
      { code: 'WS', title: T({ uz: 'Çiqindilar', ru: 'Отходы', en: 'Waste', zh: '废弃物' }, lang), subtitle: 'Waste', url: '/greenmetrics-2025' },
      { code: 'WR', title: T({ uz: 'Suv', ru: 'Вода', en: 'Water', zh: '水资源' }, lang), subtitle: 'Water', badge: top[lang], url: water6 },
      { code: 'TR', title: T({ uz: 'Transport', ru: 'Транспорт', en: 'Transport', zh: '交通' }, lang), subtitle: 'Transportation', url: '/greenmetrics-2025' },
      { code: 'ED', title: T({ uz: 'Ta’lim va tadqiqot', ru: 'Образование и исследования', en: 'Education and research', zh: '教育与研究' }, lang), subtitle: 'Education & Research', url: '/greenmetrics-2025' },
    ],
    goals: goalsSummary(lang),
    impactYear: 2025,
    reports: [
      page('SDG Policies', '/sdg-report'),
      page('SDG Report 2023', '/sdg-report'),
      page('SDG policy 2026', '/sdg-report'),
      page('Report 2025–2026', '/sdg-report', 'pdf'),
      page('Greenmetrics', '/greenmetrics'),
      page('Greenmetrics 2025', '/greenmetrics-2025'),
    ],
    education: {
      title: T({ uz: 'Barqarorlik savodxonligini baholash vositasi', ru: 'Инструмент оценки грамотности в области устойчивого развития', en: 'Sustainability Literacy Assessment Tool', zh: '可持续发展素养评估工具' }, lang),
      text: T({
        uz: 'O‘zDJTU talabalar, professor-o‘qituvchilar va xodimlar orasida barqarorlik savodxonligi va bilimlarini oshirish orqali barqarorlik madaniyatini shakllantiradi. Vosita iqlim o‘zgarishi, biologik xilma-xillik, ijtimoiy adolat va BRM mavzularini qamrab oladi.',
        ru: 'УзГУМЯ формирует культуру устойчивого развития, повышая грамотность студентов, преподавателей и сотрудников в этой области. Инструмент охватывает темы изменения климата, биоразнообразия, социальной справедливости и ЦУР.',
        en: 'UzSWLU builds a culture of sustainability by raising sustainability literacy among students, faculty and staff. The tool covers climate change, biodiversity, social justice and the SDGs.',
        zh: '我校通过提升学生、教师和员工的可持续发展素养来培育可持续发展文化。该工具涵盖气候变化、生物多样性、社会公正和可持续发展目标等主题。',
      }, lang),
      tags: ['Eco Lingua', T({ uz: 'Yillik hisobot 2023–2024', ru: 'Годовой отчёт 2023–2024', en: 'Annual report 2023–2024', zh: '2023–2024年度报告' }, lang), 'Environmental Sustainability Courses 2024', 'WUR'],
      url: '/talim-va-barqarorlik',
    },
    news: getMockPostList(lang, { type: 'news', sdg: 13, page: 1, perPage: 3 }).items,
  }
}

export function getMockSdgGoal(lang: Locale, n: number): SdgGoal | null {
  const summary = goalsSummary(lang).find(g => g.n === n)
  if (!summary) return null

  const isWater = n === 6
  const goalPage = `${OLD}${summary.url}`
  const doc = (title: string, meta: string | null): Attachment => ({ title, url: goalPage, kind: 'pdf', meta })
  const docName = T({ uz: `BRM ${n} hujjati`, ru: `Документ ЦУР ${n}`, en: `SDG ${n} document`, zh: `可持续发展目标${n}文件` }, lang)

  return {
    ...summary,
    subtitle: subtitles[n - 1]![lang],
    highlight: isWater ? { label: 'GreenMetric 2026 · Water', value: T({ uz: 'Özbekistonda #1', ru: '№1 в Узбекистане', en: '#1 in Uzbekistan', zh: '乌兹别克斯坦第1名' }, lang) } : null,
    sections: (isWater ? water : [['overview', OVERVIEW] as [string, L]]).map(([id, title]) => ({ id, title: title[lang], body: SECTION_SAMPLE[lang], images: [] })),
    documents: isWater
      ? [
          doc(docName, '22.02.2023'),
          doc(docName, '16.03.2023'),
          doc(docName, '22.05.2023'),
          doc(T({ uz: 'Yer osti suvlari laboratoriya ma’lumotlari', ru: 'Лабораторные данные по подземным водам', en: 'Groundwater laboratory data', zh: '地下水实验室数据' }, lang), null),
          doc('Report on cooperation of Uzbek State University of World Languages with governments on water security', T({ uz: 'inglizça', ru: 'на английском', en: 'in English', zh: '英文' }, lang)),
        ]
      : [doc(docName, null)],
  }
}
