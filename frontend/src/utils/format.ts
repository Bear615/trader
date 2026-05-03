export function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function currencySymbol(currency?: string): string {
  return currency?.toUpperCase() === 'GBP' ? '\u00a3' : '$'
}

export function currencyCode(settingsCurrency: unknown, fallback?: string): string {
  return String(settingsCurrency || fallback || 'USD').toUpperCase()
}
