import { format, parse } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { getBranding, type TimeFormat } from '@/api/settings'

/**
 * Formats a time for display according to the tenant's 12h / 24h preference.
 *
 * Accepts:
 *   - Date object
 *   - ISO datetime string (e.g. "2026-04-29T09:00:00")
 *   - "HH:mm" string (24-hour)
 *
 * Modes:
 *   - 12h: "9:00 AM" (or "9 AM" with hourOnly)
 *   - 24h: "9:00"   (or "9" with hourOnly)
 */
export function formatTime(
  input: Date | string,
  mode: TimeFormat,
  opts: { hourOnly?: boolean } = {},
): string {
  const date = parseTimeInput(input)
  if (mode === '24h') {
    return opts.hourOnly ? format(date, 'H') : format(date, 'H:mm')
  }
  return opts.hourOnly ? format(date, 'h a') : format(date, 'h:mm a')
}

function parseTimeInput(input: Date | string): Date {
  if (input instanceof Date) return input
  // ISO datetime
  if (input.includes('T') || input.length > 8) return new Date(input)
  // "HH:mm" or "HH:mm:ss"
  return parse(input.slice(0, 5), 'HH:mm', new Date())
}

/**
 * Hook returning a formatTime fn pre-bound to the tenant's time_format.
 * Falls back to 12h while branding is loading or unset.
 */
export function useTimeFormat() {
  const { data: branding } = useQuery({ queryKey: ['branding'], queryFn: getBranding })
  const mode: TimeFormat = branding?.time_format ?? '12h'
  return {
    mode,
    formatTime: (input: Date | string, opts?: { hourOnly?: boolean }) =>
      formatTime(input, mode, opts),
  }
}
