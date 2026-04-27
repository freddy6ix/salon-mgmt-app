import { api } from './client'

export const SLOT_OPTIONS = [5, 10, 15, 20, 30] as const
export type SlotMinutes = typeof SLOT_OPTIONS[number]

export interface BrandingSettings {
  salon_name: string
  logo_url: string | null
  brand_color: string | null
  slot_minutes: SlotMinutes
}

export function getBranding(): Promise<BrandingSettings> {
  return api.get<BrandingSettings>('/settings/branding')
}

export function updateBranding(
  patch: Partial<Pick<BrandingSettings, 'logo_url' | 'brand_color' | 'slot_minutes'>>,
): Promise<BrandingSettings> {
  return api.patch<BrandingSettings>('/settings/branding', patch)
}

export interface OperatingHoursDay {
  day_of_week: number  // 0=Mon … 6=Sun
  is_open: boolean
  open_time: string | null  // "HH:MM"
  close_time: string | null
}

export function getOperatingHours(): Promise<OperatingHoursDay[]> {
  return api.get<OperatingHoursDay[]>('/settings/operating-hours')
}

export function updateOperatingHours(days: OperatingHoursDay[]): Promise<OperatingHoursDay[]> {
  return api.put<OperatingHoursDay[]>('/settings/operating-hours', { days })
}

export interface RequestNotifications {
  enabled: boolean
  recipients: string[]
}

export function getRequestNotifications(): Promise<RequestNotifications> {
  return api.get<RequestNotifications>('/settings/notifications')
}

export function updateRequestNotifications(
  patch: { enabled?: boolean; recipients?: string[] },
): Promise<RequestNotifications> {
  return api.patch<RequestNotifications>('/settings/notifications', patch)
}
