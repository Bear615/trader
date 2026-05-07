export function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('en-GB', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function currencySymbol(currency?: string): string {
  const code = currencyCode(currency)
  if (code === 'GBP') return '\u00a3'
  if (code === 'EUR') return '\u20ac'
  return '$'
}

export function currencyCode(settingsCurrency: unknown, fallback?: string): string {
  return String(settingsCurrency || fallback || 'GBP').toUpperCase()
}

export function formatCurrency(
  value: number | null | undefined,
  currency?: string,
  decimals = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: currencyCode(currency),
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatNumber(
  value: number | null | undefined,
  decimals = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return new Intl.NumberFormat('en-GB', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercent(value: number | null | undefined, decimals = 1, signed = false): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  const prefix = signed && value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(decimals)}%`
}
