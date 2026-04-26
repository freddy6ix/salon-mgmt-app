import { api } from './client'

export interface ProviderServicePrice {
  id: string
  provider_id: string
  provider_name: string
  service_id: string
  service_name: string
  price: string
  duration_minutes: number | null
  processing_offset_minutes: number | null
  processing_duration_minutes: number | null
  cost: string | null
  cost_is_percentage: boolean
  effective_from: string
  effective_to: string | null
  is_active: boolean
}

export interface PSPIn {
  provider_id: string
  service_id: string
  price: number
  duration_minutes?: number | null
  processing_offset_minutes?: number | null
  processing_duration_minutes?: number | null
  cost?: number | null
  cost_is_percentage?: boolean
  effective_from?: string | null
  effective_to?: string | null
  is_active?: boolean
}

export type PSPPatch = Partial<Omit<PSPIn, 'provider_id' | 'service_id'>>

export function listProviderServicePrices(params: { service_id?: string; provider_id?: string } = {}): Promise<ProviderServicePrice[]> {
  const qs = new URLSearchParams()
  if (params.service_id) qs.set('service_id', params.service_id)
  if (params.provider_id) qs.set('provider_id', params.provider_id)
  const tail = qs.toString() ? `?${qs}` : ''
  return api.get<ProviderServicePrice[]>(`/provider-service-prices${tail}`)
}

export function createProviderServicePrice(body: PSPIn): Promise<ProviderServicePrice> {
  return api.post<ProviderServicePrice>('/provider-service-prices', body)
}

export function updateProviderServicePrice(id: string, body: PSPPatch): Promise<ProviderServicePrice> {
  return api.patch<ProviderServicePrice>(`/provider-service-prices/${id}`, body)
}

export function deleteProviderServicePrice(id: string): Promise<void> {
  return api.delete<void>(`/provider-service-prices/${id}`)
}
