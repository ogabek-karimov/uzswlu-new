// Haqiqiy Excel fayli (.xlsx) — tashqi kutubxonasiz. XLSX — bir nechta XML fayldan iborat ZIP arxiv;
// bu yerda siqilmagan ("stored") ZIP yoziladi: Excel, LibreOffice va Google Sheets bemalol ochadi.

type Cell = string | number | null | undefined

const enc = new TextEncoder()
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  // XML'da ruxsat etilmagan boshqaruv belgilari
  .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')

/** Ustun harfi: 0 → A, 26 → AA */
function col(i: number) {
  let s = ''
  for (let n = i + 1; n > 0; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + ((n - 1) % 26)) + s
  return s
}

const CRC_TABLE = (() => {
  const t = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1
    t[n] = c >>> 0
  }
  return t
})()

function crc32(data: Uint8Array) {
  let c = 0xFFFFFFFF
  for (let i = 0; i < data.length; i++) c = CRC_TABLE[(c ^ data[i]!) & 0xFF]! ^ (c >>> 8)
  return (c ^ 0xFFFFFFFF) >>> 0
}

/** Siqilmagan ZIP arxiv */
function zip(files: { name: string; data: Uint8Array }[]): Blob {
  const parts: Uint8Array[] = []
  const central: Uint8Array[] = []
  let offset = 0
  for (const f of files) {
    const name = enc.encode(f.name)
    const crc = crc32(f.data)
    const local = new DataView(new ArrayBuffer(30))
    local.setUint32(0, 0x04034B50, true)
    local.setUint16(4, 20, true)
    local.setUint16(6, 0x0800, true) // UTF-8 nomlar
    local.setUint32(14, crc, true)
    local.setUint32(18, f.data.length, true)
    local.setUint32(22, f.data.length, true)
    local.setUint16(26, name.length, true)
    parts.push(new Uint8Array(local.buffer), name, f.data)

    const c = new DataView(new ArrayBuffer(46))
    c.setUint32(0, 0x02014B50, true)
    c.setUint16(4, 20, true)
    c.setUint16(6, 20, true)
    c.setUint16(8, 0x0800, true)
    c.setUint32(16, crc, true)
    c.setUint32(20, f.data.length, true)
    c.setUint32(24, f.data.length, true)
    c.setUint16(28, name.length, true)
    c.setUint32(42, offset, true)
    central.push(new Uint8Array(c.buffer), name)
    offset += 30 + name.length + f.data.length
  }
  const size = central.reduce((s, p) => s + p.length, 0)
  const end = new DataView(new ArrayBuffer(22))
  end.setUint32(0, 0x06054B50, true)
  end.setUint16(8, files.length, true)
  end.setUint16(10, files.length, true)
  end.setUint32(12, size, true)
  end.setUint32(16, offset, true)
  return new Blob([...parts, ...central, new Uint8Array(end.buffer)] as BlobPart[], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
}

/**
 * Jadvalni .xlsx qilib yuklab berish. Birinchi qator — sarlavha (qalin, filtr bilan, qotirilgan).
 * widths — ustunlar kengligi (belgilar soni); berilmasa matn uzunligidan hisoblanadi.
 */
export function downloadXlsx(filename: string, sheet: string, header: string[], rows: Cell[][], widths?: number[]) {
  const all = [header, ...rows]
  const w = widths ?? header.map((_, i) => Math.min(60, Math.max(8, ...all.map(r => String(r[i] ?? '').length + 2))))
  const last = `${col(header.length - 1)}${all.length}`
  const sheetRows = all.map((r, ri) => `<row r="${ri + 1}">${r.map((v, ci) => {
    const ref = `${col(ci)}${ri + 1}`
    const style = ri === 0 ? ' s="1"' : ''
    if (typeof v === 'number' && Number.isFinite(v)) return `<c r="${ref}"${style}><v>${v}</v></c>`
    if (v === null || v === undefined || v === '') return ''
    return `<c r="${ref}" t="inlineStr"${style}><is><t xml:space="preserve">${esc(String(v))}</t></is></c>`
  }).join('')}</row>`).join('')

  const xml = (s: string) => enc.encode(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n${s}`)
  const NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
  const files = [
    { name: '[Content_Types].xml', data: xml('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>') },
    { name: '_rels/.rels', data: xml('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>') },
    { name: 'xl/workbook.xml', data: xml(`<workbook ${NS}><sheets><sheet name="${esc(sheet.slice(0, 31))}" sheetId="1" r:id="rId1"/></sheets><definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">'${esc(sheet.slice(0, 31))}'!$A$1:$${col(header.length - 1)}$${all.length}</definedName></definedNames></workbook>`) },
    { name: 'xl/_rels/workbook.xml.rels', data: xml('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>') },
    { name: 'xl/styles.xml', data: xml(`<styleSheet ${NS}><fonts count="2"><font><sz val="11"/><name val="Calibri"/><family val="2"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF2A2066"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>`) },
    { name: 'xl/worksheets/sheet1.xml', data: xml(`<worksheet ${NS}><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>${w.map((x, i) => `<col min="${i + 1}" max="${i + 1}" width="${x}" customWidth="1"/>`).join('')}</cols><sheetData>${sheetRows}</sheetData><autoFilter ref="A1:${last}"/></worksheet>`) },
  ]

  const a = document.createElement('a')
  a.href = URL.createObjectURL(zip(files))
  a.download = filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}
