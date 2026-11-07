/**
 * «Oxirgi yaxshi javob» keshi (stale-if-error).
 *
 * Backend o'chib qolsa yoki javob bermasa, sayt oxirgi muvaffaqiyatli javobni (ko'pi bilan
 * `maxStaleMs` — odatda 3 soat) ko'rsatib turadi. Backend qaytganda yangi javoblar o'zi olinadi.
 *
 * Qoidalar:
 *  - Faqat «backend ishlamayapti» xatolari (tarmoq, timeout, 5xx, 429) eskisini qaytaradi.
 *    404/422 kabi 4xx — haqiqiy javob, shuning uchun o'z holicha yuqoriga uzatiladi.
 *  - Xato bo'lgach `cooldownMs` davomida backendga bormaydi: har so'rov 8 soniya kutib qotmaydi
 *    va o'lik backend ortiqcha yuk olmaydi. Keyin bitta so'rov «tekshiruv» sifatida boradi.
 *  - Xotira cheklangan (`maxEntries`, eng eskisi chiqariladi).
 *
 * Bu fayl Nuxt/Nitro'ga bog'liq emas — alohida sinash mumkin.
 */

export interface LastGoodOptions {
  /** Eski javob qancha vaqtgacha yaroqli (ms) */
  maxStaleMs: number
  /** Xatodan keyin backendga necha ms bormaslik */
  cooldownMs: number
  /** Eng ko'p saqlanadigan javoblar soni */
  maxEntries: number
  /** Sinov uchun vaqt manbai */
  now?: () => number
}

export interface LastGoodResult<T> {
  value: T
  /** Eski javob bo'lsa — uning yoshi (ms) */
  staleAgeMs?: number
}

interface Entry { value: unknown, at: number }

/** Backend ishlamayotganini bildiruvchi xato: tarmoq/timeout (status yo'q), 5xx yoki 429 */
export function isBackendFailure(error: unknown): boolean {
  const e = error as { status?: number, statusCode?: number, response?: { status?: number } } | null
  const status = e?.status ?? e?.statusCode ?? e?.response?.status
  if (typeof status !== 'number' || status === 0) return true
  return status >= 500 || status === 429
}

export function createLastGood(options: LastGoodOptions) {
  const now = options.now ?? Date.now
  const store = new Map<string, Entry>()
  let downUntil = 0
  let lastWarn = 0

  function usable(entry: Entry | undefined): entry is Entry {
    return !!entry && now() - entry.at <= options.maxStaleMs
  }

  function remember(key: string, value: unknown) {
    store.delete(key) // tartibni yangilash (eng yangisi oxirida)
    store.set(key, { value, at: now() })
    while (store.size > options.maxEntries) {
      const oldest = store.keys().next().value
      if (oldest === undefined) break
      store.delete(oldest)
    }
  }

  /**
   * @param key      so'rovning barqaror kaliti
   * @param fetcher  haqiqiy backend so'rovi
   * @param keep     false bo'lsa natija saqlanmaydi va eskisi ham ishlatilmaydi (qidiruv kabi cheksiz kalitlar uchun)
   * @param onWarn   backend yiqilganda (cooldown ichida bir marta) chaqiriladi
   */
  async function run<T>(
    key: string,
    fetcher: () => Promise<T>,
    keep = true,
    onWarn?: (error: unknown) => void,
  ): Promise<LastGoodResult<T>> {
    const entry = keep ? store.get(key) : undefined

    // Backend yaqinda yiqilgan va eski javob bor — tarmoqqa bormay, darhol eskisini beramiz
    if (now() < downUntil && usable(entry)) {
      return { value: entry.value as T, staleAgeMs: now() - entry.at }
    }

    try {
      const value = await fetcher()
      downUntil = 0
      if (keep) remember(key, value)
      return { value }
    }
    catch (error) {
      if (!isBackendFailure(error)) throw error
      downUntil = now() + options.cooldownMs
      if (onWarn && now() - lastWarn > options.cooldownMs) {
        lastWarn = now()
        onWarn(error)
      }
      if (usable(entry)) return { value: entry.value as T, staleAgeMs: now() - entry.at }
      throw error
    }
  }

  return {
    run,
    /** Sinov va diagnostika uchun */
    get size() { return store.size },
    clear() { store.clear(); downUntil = 0 },
  }
}
