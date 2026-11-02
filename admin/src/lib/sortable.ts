import { type Ref, ref } from 'vue'
import { api } from './api'

// Kartalarni sichqoncha bilan surib tartiblash (HTML5 drag & drop).
// Tashlangandan keyin faqat o'rni o'zgargan yozuvlarning `order` maydoni saqlanadi.
export function useSortable<T extends { id: number; order?: number | null }>(list: Ref<T[]>, collection: string) {
  const dragging = ref<number | null>(null)
  const over = ref<number | null>(null)
  const saving = ref(false)

  function bind(index: number) {
    return {
      draggable: true,
      onDragstart: (e: DragEvent) => {
        dragging.value = index
        e.dataTransfer?.setData('text/plain', String(index))
        if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
      },
      onDragover: (e: DragEvent) => {
        if (dragging.value === null) return
        e.preventDefault()
        over.value = index
      },
      onDragleave: () => { if (over.value === index) over.value = null },
      onDrop: (e: DragEvent) => {
        e.preventDefault()
        const from = dragging.value
        dragging.value = null
        over.value = null
        if (from === null || from === index) return
        move(from, index)
      },
      onDragend: () => { dragging.value = null; over.value = null },
    }
  }

  /** Klaviatura bilan ham: ↑/↓ tugmalari */
  async function move(from: number, to: number) {
    if (to < 0 || to >= list.value.length) return
    const items = [...list.value]
    const [item] = items.splice(from, 1)
    items.splice(to, 0, item!)
    const changed = items.filter((it, i) => it.order !== i + 1)
    items.forEach((it, i) => { it.order = i + 1 })
    list.value = items
    saving.value = true
    try {
      await Promise.all(changed.map(it => api.patch(`/${collection}/${it.id}`, { order: it.order }, { depth: 0 })))
    }
    finally {
      saving.value = false
    }
  }

  return { bind, move, dragging, over, saving }
}
