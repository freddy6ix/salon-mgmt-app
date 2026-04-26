import { api } from './client'

export type HaircutType = 'type_1' | 'type_2' | 'type_2_plus'
export type PricingType = 'fixed' | 'hourly'

export interface Service {
  id: string
  service_code: string
  name: string
  category_name: string
  duration_minutes: number
  default_price: number | null
  is_addon: boolean
  pricing_type: string
}

export interface ServiceDetail {
  id: string
  category_id: string
  category_name: string
  service_code: string
  name: string
  description: string | null
  haircut_type: HaircutType | null
  pricing_type: PricingType
  default_price: string | null
  default_cost: string | null
  duration_minutes: number
  processing_offset_minutes: number
  processing_duration_minutes: number
  is_addon: boolean
  requires_prior_consultation: boolean
  is_gst_exempt: boolean
  is_pst_exempt: boolean
  suggestions: string | null
  is_active: boolean
  display_order: number
}

export interface ServiceIn {
  category_id: string
  service_code?: string | null
  name: string
  description?: string | null
  haircut_type?: HaircutType | null
  pricing_type?: PricingType
  default_price?: number | null
  default_cost?: number | null
  duration_minutes?: number
  processing_offset_minutes?: number
  processing_duration_minutes?: number
  is_addon?: boolean
  requires_prior_consultation?: boolean
  is_gst_exempt?: boolean
  is_pst_exempt?: boolean
  suggestions?: string | null
  is_active?: boolean
  display_order?: number
}

export type ServicePatch = Partial<ServiceIn>

export function listServices(): Promise<Service[]> {
  return api.get<Service[]>('/services')
}

export function listServicesFull(): Promise<ServiceDetail[]> {
  return api.get<ServiceDetail[]>('/services/all')
}

export function getService(id: string): Promise<ServiceDetail> {
  return api.get<ServiceDetail>(`/services/${id}`)
}

export function createService(body: ServiceIn): Promise<ServiceDetail> {
  return api.post<ServiceDetail>('/services', body)
}

export function updateService(id: string, body: ServicePatch): Promise<ServiceDetail> {
  return api.patch<ServiceDetail>(`/services/${id}`, body)
}

export function deactivateService(id: string): Promise<void> {
  return api.delete<void>(`/services/${id}`)
}
