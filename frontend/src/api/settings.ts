import { api } from './client'

export interface BrandingSettings {
  salon_name: string
  logo_url: string | null
  brand_color: string | null
}

export function getBranding(): Promise<BrandingSettings> {
  return api.get<BrandingSettings>('/settings/branding')
}

export function updateBranding(
  patch: Partial<Pick<BrandingSettings, 'logo_url' | 'brand_color'>>,
): Promise<BrandingSettings> {
  return api.patch<BrandingSettings>('/settings/branding', patch)
}
