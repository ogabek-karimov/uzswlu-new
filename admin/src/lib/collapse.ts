import { reactive } from 'vue'

// «Hammasini yig'ish / yoyish»: har bir Collapsible `tick` o'zgarganini kuzatadi va `open` holatini oladi
export const collapseBus = reactive({ tick: 0, open: true })

export function setAllCollapsed(collapsed: boolean) {
  collapseBus.open = !collapsed
  collapseBus.tick++
}
