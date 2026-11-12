import type { SocialLink } from '#shared/types/api'

type Network = SocialLink['network']

/** Chap paneldagi tartib — eski saytdagidek */
const ORDER: Network[] = ['facebook', 'x', 'instagram', 'telegram', 'youtube']

/** Universitetning ijtimoiy tarmoqlari: ikonka, brend rangi (ink — ikonka, fill — hover'dagi fon) */
export const siteNetworks: Record<Network, { label: string; icon: string; ink: string; fill: string }> = {
  facebook: { label: 'Facebook', icon: 'simple-icons:facebook', ink: 'text-[#1877f2]', fill: 'bg-[#1877f2]' },
  x: { label: 'X', icon: 'simple-icons:x', ink: 'text-black', fill: 'bg-black' },
  instagram: { label: 'Instagram', icon: 'simple-icons:instagram', ink: 'text-[#e1306c]', fill: 'bg-[linear-gradient(45deg,#f9a03f,#d6249f,#5851db)]' },
  telegram: { label: 'Telegram', icon: 'simple-icons:telegram', ink: 'text-[#229ed9]', fill: 'bg-[#229ed9]' },
  youtube: { label: 'YouTube', icon: 'simple-icons:youtube', ink: 'text-[#ff0000]', fill: 'bg-[#ff0000]' },
}

/** Admin panelda kiritilgan havolalar (GET /site → socials), eski saytdagi tartibda */
export const sortSocials = (list: SocialLink[]) =>
  list.filter(s => siteNetworks[s.network]).sort((a, b) => ORDER.indexOf(a.network) - ORDER.indexOf(b.network))

/** «Filologiya masalalari» — universitetning ilmiy jurnali (sarlavhada logotip) */
export const JOURNAL = { url: 'https://philmatt.uzswlu.uz/', logo: '/images/journal-fm.webp' }
