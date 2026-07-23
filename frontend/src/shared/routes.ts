export const ROUTES = {
  chat: '/',
} as const

export interface NavItem {
  label: string
  to: string
  inSidebar: boolean
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Chat', to: ROUTES.chat, inSidebar: true },
]
