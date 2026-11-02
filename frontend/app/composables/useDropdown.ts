// Ochiladigan menyu: tashqariga bosilganda, Esc'da yoki sahifa o'zgarganda yopiladi.
// Komponentda: const { open, root } = useDropdown()  →  <div ref="root">
export function useDropdown() {
  const open = ref(false)
  const root = ref<HTMLElement>()
  const route = useRoute()

  function onDocumentClick(e: MouseEvent) {
    if (root.value && !root.value.contains(e.target as Node)) open.value = false
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') open.value = false
  }

  onMounted(() => {
    document.addEventListener('click', onDocumentClick)
    document.addEventListener('keydown', onKeydown)
  })

  onBeforeUnmount(() => {
    document.removeEventListener('click', onDocumentClick)
    document.removeEventListener('keydown', onKeydown)
  })

  watch(() => route.fullPath, () => (open.value = false))

  return { open, root }
}
