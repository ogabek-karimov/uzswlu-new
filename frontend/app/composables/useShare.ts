// Sahifa havolasini ulashish: telefon/brauzer ulashish oynasi bo'lsa — o'sha, bo'lmasa nusxalash.
export function useShare() {
  const copied = ref(false)
  let timer: ReturnType<typeof setTimeout> | undefined

  async function copy(url = window.location.href) {
    try {
      await navigator.clipboard.writeText(url)
      copied.value = true
      clearTimeout(timer)
      timer = setTimeout(() => (copied.value = false), 2000)
    }
    catch {
      window.prompt('', url)
    }
  }

  async function share(title: string, url = window.location.href) {
    if (navigator.share) {
      try {
        await navigator.share({ title, url })
        return
      }
      catch (error) {
        if ((error as DOMException).name === 'AbortError') return
      }
    }
    await copy(url)
  }

  return { copied, copy, share }
}
