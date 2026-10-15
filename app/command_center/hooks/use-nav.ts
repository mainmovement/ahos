import { usePathname } from 'next/navigation'

export function useNav() {
  const pathname = usePathname()

  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(`${path}/`)
  }

  const openPaths = ['/', '/discovery', '/opportunities', '/market-intelligence']

  return {
    isActive,
    isOpen: openPaths.includes(pathname),
  }
}