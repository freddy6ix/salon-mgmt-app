import { api } from './client'

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

export function listServices(): Promise<Service[]> {
  return api.get<Service[]>('/services')
}
