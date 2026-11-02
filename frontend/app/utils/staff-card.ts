import { encode } from 'uqr'
import { initials } from './staff'

// Xodim vizitkasi va QR kodni brauzerning o'zida PNG qilib chizish (server kerak emas).
// Ko'rinishi profil sahifasidagi "Ulashish" oynasidagi vizitka bilan bir xil (oldingi saytdagi bejik):
// ism-familiya va sharif alohida qatorda bir xil kattalikda, bo'limlar bitta qatorda ("…" bilan).

export interface StaffCardInput {
  nameMain: string
  nameSharif?: string
  position: string
  department: string
  university: string
  /** QR ichidagi havola */
  url: string
  photo?: string | null
  /** O'z surati ochilmasa — HEMIS surati */
  photoFallback?: string | null
}

const MINT = '#00FCB4'
const FONT = 'Onest, sans-serif'

function drawQr(ctx: CanvasRenderingContext2D, url: string, x: number, y: number, size: number) {
  const data = encode(url, { border: 0 }).data
  const cell = size / data.length
  ctx.fillStyle = '#13112F'
  data.forEach((row, r) => row.forEach((on, c) => {
    // Qo'shni modullar orasida ingichka chiziq qolmasligi uchun 0.5px kattaroq
    if (on) ctx.fillRect(x + c * cell, y + r * cell, cell + 0.5, cell + 0.5)
  }))
}

/** Matn kenglikka sig'guncha shriftni kichraytiradi (eng kichigi — min) */
function fitSize(ctx: CanvasRenderingContext2D, text: string, weight: number, size: number, min: number, maxWidth: number) {
  let s = size
  ctx.font = `${weight} ${s}px ${FONT}`
  while (s > min && ctx.measureText(text).width > maxWidth) {
    s -= 1
    ctx.font = `${weight} ${s}px ${FONT}`
  }
  return s
}

/** Bitta qatorga sig'dirish, sig'masa oxiriga "…" */
function ellipsize(ctx: CanvasRenderingContext2D, text: string, maxWidth: number) {
  if (ctx.measureText(text).width <= maxWidth) return text
  let s = text
  while (s.length > 1 && ctx.measureText(`${s}…`).width > maxWidth) s = s.slice(0, -1)
  return `${s.trimEnd()}…`
}

function loadImage(src: string) {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const img = new Image()
    // Boshqa domendagi surat CORS ruxsatisiz bo'lsa canvas "ifloslanadi" — unda bosh harflar chiziladi
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
}

function toBlob(canvas: HTMLCanvasElement) {
  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(blob => (blob ? resolve(blob) : reject(new Error('PNG yaratilmadi'))), 'image/png')
  })
}

export async function renderQrPng(url: string, size = 1024) {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size
  const ctx = canvas.getContext('2d')!
  ctx.fillStyle = '#FFFFFF'
  ctx.fillRect(0, 0, size, size)
  const pad = size * 0.06
  drawQr(ctx, url, pad, pad, size - pad * 2)
  return toBlob(canvas)
}

export async function renderStaffCard(input: StaffCardInput) {
  // 400px oynadagi vizitkaning 2.7 baravar kattasi
  const W = 1000
  const H = 1440
  const MAXW = W - 120
  await Promise.all(['500 32px', '700 52px', '400 38px', '400 30px', '700 80px'].map(f => document.fonts.load(`${f} ${FONT}`).catch(() => [])))

  let photo: HTMLImageElement | null = null
  for (const src of [input.photo, input.photoFallback]) {
    if (!photo && src) photo = await loadImage(src).catch(() => null)
  }
  const mark = await loadImage('/logos/mark.webp').catch(() => null)

  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext('2d')!

  // Fon: indigo gradient + bezak halqa
  const bg = ctx.createLinearGradient(0, 0, W * 0.3, H)
  bg.addColorStop(0, '#2A2066')
  bg.addColorStop(0.6, '#1C1548')
  bg.addColorStop(1, '#110C2E')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, W, H)
  // Universitet belgisi — yarim halqa markazida, xira (oynadagi vizitka bilan bir xil joyda)
  const ox = W - 140
  const oy = 205
  ctx.strokeStyle = 'rgba(0, 252, 180, 0.07)'
  ctx.lineWidth = 70
  ctx.beginPath()
  ctx.arc(ox, oy, 235, 0, Math.PI * 2)
  ctx.stroke()
  if (mark) {
    const mw = 173
    const mh = mw * (mark.naturalHeight / mark.naturalWidth)
    ctx.globalAlpha = 0.2
    ctx.drawImage(mark, ox - mw / 2, oy - mh / 2, mw, mh)
    ctx.globalAlpha = 1
  }

  ctx.textAlign = 'center'
  ctx.textBaseline = 'alphabetic'
  const cx = W / 2

  ctx.font = `500 32px ${FONT}`
  ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
  ctx.fillText(ellipsize(ctx, input.university, MAXW), cx, 110)

  // Surat: gradient halqa, ichida surat yoki bosh harflar
  const R = 140
  const cy = 160 + R
  const ring = ctx.createLinearGradient(cx - R, cy - R, cx + R, cy + R)
  ring.addColorStop(0, MINT)
  ring.addColorStop(1, '#5B4BBE')
  ctx.fillStyle = ring
  ctx.beginPath()
  ctx.arc(cx, cy, R, 0, Math.PI * 2)
  ctx.fill()
  const inner = R - 8
  ctx.save()
  ctx.beginPath()
  ctx.arc(cx, cy, inner, 0, Math.PI * 2)
  ctx.clip()
  if (photo) {
    const s = Math.min(photo.naturalWidth, photo.naturalHeight)
    ctx.drawImage(photo, (photo.naturalWidth - s) / 2, (photo.naturalHeight - s) / 2, s, s, cx - inner, cy - inner, inner * 2, inner * 2)
  }
  else {
    ctx.fillStyle = '#E4E0F8'
    ctx.fillRect(cx - inner, cy - inner, inner * 2, inner * 2)
    ctx.font = `700 80px ${FONT}`
    ctx.fillStyle = '#1C1548'
    ctx.textBaseline = 'middle'
    ctx.fillText(initials(input.nameMain), cx, cy + 4)
    ctx.textBaseline = 'alphabetic'
  }
  ctx.restore()

  // Ism-familiya va sharif: alohida qatorlarda, bir xil kattalikda
  let y = cy + R + 84
  ctx.fillStyle = '#FFFFFF'
  const lines = [input.nameMain, input.nameSharif].filter(Boolean) as string[]
  const nameSize = Math.min(...lines.map(l => fitSize(ctx, l, 700, 52, 34, MAXW)))
  ctx.font = `700 ${nameSize}px ${FONT}`
  for (const line of lines) {
    ctx.fillText(line, cx, y)
    y += Math.round(nameSize * 1.25)
  }

  y += 14
  const posSize = fitSize(ctx, input.position, 400, 38, 26, MAXW)
  ctx.font = `400 ${posSize}px ${FONT}`
  ctx.fillStyle = 'rgba(255, 255, 255, 0.85)'
  ctx.fillText(input.position, cx, y)

  y += 50
  ctx.font = `400 30px ${FONT}`
  ctx.fillStyle = 'rgba(255, 255, 255, 0.65)'
  ctx.fillText(ellipsize(ctx, input.department, MAXW), cx, y)

  // QR oq kartada
  const tile = 540
  const qrY = y + 48
  ctx.fillStyle = '#FFFFFF'
  ctx.beginPath()
  ctx.roundRect((W - tile) / 2, qrY, tile, tile, 44)
  ctx.fill()
  drawQr(ctx, input.url, (W - tile) / 2 + 32, qrY + 32, tile - 64)

  // Havola matni yozilmaydi (oldingi saytda xavfsizlik sababli olib tashlangan) — faqat QR

  // Kontent balandligiga qarab pastki qismni kesamiz
  const used = qrY + tile + 60
  if (used < H) {
    const out = document.createElement('canvas')
    out.width = W
    out.height = used
    out.getContext('2d')!.drawImage(canvas, 0, 0)
    return toBlob(out)
  }
  return toBlob(canvas)
}

/** Faylni yuklab olish (Blob → vaqtinchalik havola) */
export function saveBlob(blob: Blob, filename: string) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(link.href), 1000)
}
