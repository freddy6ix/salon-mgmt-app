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
