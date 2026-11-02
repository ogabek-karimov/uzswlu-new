import type { PayloadRequest } from 'payload'

/** Mijozning IP manzili (nginx / Vite proxy orqali kelganda X-Forwarded-For'dan) */
export function clientIp(req: PayloadRequest): string {
  const h = req.headers
  const forwarded = h.get('x-forwarded-for')?.split(',')[0]?.trim()
  const ip = (forwarded || h.get('x-real-ip') || '').replace(/^::ffff:/, '')
  if (!ip) return 'nomaʼlum'
  if (ip === '::1' || ip === '127.0.0.1') return '127.0.0.1'
  return ip
}

/** Tarmoq turi: içki (universitet), localhost yoki taşqi */
export function networkOf(ip: string): string {
  if (ip === '127.0.0.1') return 'localhost'
  if (/^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(ip)) return 'Içki tarmoq'
  return 'Internet'
}

/** User-Agent'dan brauzer, operatsion tizim va qurilma (kutubxonasiz, oddiy) */
export function parseUserAgent(ua: string) {
  const browser
    = /Edg\/(\d+)/.exec(ua)?.[1] ? `Edge ${/Edg\/(\d+)/.exec(ua)![1]}`
      : /OPR\/(\d+)/.exec(ua)?.[1] ? `Opera ${/OPR\/(\d+)/.exec(ua)![1]}`
        : /Firefox\/(\d+)/.exec(ua)?.[1] ? `Firefox ${/Firefox\/(\d+)/.exec(ua)![1]}`
          : /Chrome\/(\d+)/.exec(ua)?.[1] ? `Chrome ${/Chrome\/(\d+)/.exec(ua)![1]}`
            : /Version\/(\d+).*Safari/.exec(ua)?.[1] ? `Safari ${/Version\/(\d+).*Safari/.exec(ua)![1]}`
              : /^([\w-]+)\/[\d.]+/.exec(ua)?.[1] ?? 'Nomaʼlum'
  const os
    = /Windows NT 10/.test(ua) ? 'Windows 10/11'
      : /Windows/.test(ua) ? 'Windows'
        : /iPhone|iPad/.test(ua) ? 'iOS'
          : /Android (\d+)/.exec(ua)?.[1] ? `Android ${/Android (\d+)/.exec(ua)![1]}`
            : /Mac OS X/.test(ua) ? 'macOS'
              : /Linux/.test(ua) ? 'Linux'
                : 'Nomaʼlum'
  const device = /iPad|Tablet/.test(ua) ? 'Planşet' : /Mobile|iPhone|Android/.test(ua) ? 'Telefon' : 'Kompyuter'
  return { browser, os, device }
}

export function requestInfo(req: PayloadRequest) {
  const ip = clientIp(req)
  const userAgent = (req.headers.get('user-agent') ?? '').slice(0, 400)
  return { ip, network: networkOf(ip), userAgent, ...parseUserAgent(userAgent) }
}
