import { api } from './client'

export interface Provider {
  id: string
  display_name: string
  provider_type: 'stylist' | 'colourist' | 'dualist'
  booking_order: number
  has_appointments: boolean
}

export function listProviders(): Promise<Provider[]> {
  return api.get<Provider[]>('/providers')
}
