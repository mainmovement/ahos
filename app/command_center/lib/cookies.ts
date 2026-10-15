export function getCookie(name: string): string | undefined {
  if (typeof document === 'undefined') return undefined

  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [cookieName, value] = cookie.trim().split('=')
    if (cookieName === name) {
      return decodeURIComponent(value)
    }
  }
  return undefined
}

export function setCookie(name: string, value: string, days: number = 365): void {
  if (typeof document === 'undefined') return

  const expires = new Date()
  expires.setDate(expires.getDate() + days)

  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires.toUTCString()}; path=/`
}