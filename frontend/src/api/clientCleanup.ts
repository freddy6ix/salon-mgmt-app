import { api } from './client'

export interface ClientDetail {
  id: string
  first_name: string
  last_name: string
  email: string | null
  cell_phone: string | null
  pronouns: string | null
  special_instructions: string | null
  no_show_count: number
  late_cancellation_count: number
  is_vip: boolean
  appointment_count: number
  household_id: string | null
}

export interface DuplicatePair {
  reason: 'email' | 'phone' | 'name'
  client_a: ClientDetail
  client_b: ClientDetail
  recommended_primary_id: string
}

export interface HouseholdMember {
  id: string
  first_name: string
  last_name: string
  email: string | null
  cell_phone: string | null
}

export interface Household {
  id: string
  members: HouseholdMember[]
}

export const getDuplicatePairs = (): Promise<DuplicatePair[]> =>
  api.get('/clients/duplicate-pairs')

export const mergeClients = (primaryId: string, sourceId: string): Promise<ClientDetail> =>
  api.post(`/clients/${primaryId}/merge`, { source_id: sourceId })

export const setClientHousehold = (clientId: string, householdId: string | null): Promise<ClientDetail> =>
  api.patch(`/clients/${clientId}/household`, { household_id: householdId })

export const listHouseholds = (): Promise<Household[]> =>
  api.get('/households')

export const createHousehold = (memberIds: string[]): Promise<Household> =>
  api.post('/households', { member_ids: memberIds })

export const deleteHousehold = (id: string): Promise<void> =>
  api.delete(`/households/${id}`)
