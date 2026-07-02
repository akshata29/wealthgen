export const formatPercent = (value: number, decimals = 2): string => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

export const formatBps = (value: number): string => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${Math.round(value)} bps`
}

/** Mask an account/client id, keeping the last four characters. */
export const maskId = (value: string): string => {
  if (!value || value.length <= 4) return value
  return `${'*'.repeat(value.length - 4)}${value.slice(-4)}`
}
