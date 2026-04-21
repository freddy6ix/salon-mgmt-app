import { api } from './client'

export interface Client {
  id: string
  first_name: string
  last_name: string
  cell_phone: string | null
  email: string | null
  special_instructions: string | null
}

export function searchClients(q: string): Promise<Client[]> {
  return api.get<Client[]>(`/clients?q=${encodeURIComponent(q)}&limit=20`)
}

export function createClient(data: {
  first_name: string
  last_name: string
  cell_phone?: string
  email?: string
}): Promise<Client> {
  return api.post<Client>('/clients', data)
}

export function updateClientNotes(clientId: string, notes: string | null): Promise<Client> {
  return api.patch<Client>(`/clients/${clientId}/notes`, { special_instructions: notes })
}

export interface VisitItem {
  service_name: string
  provider_name: string
  price: number
}

export interface Visit {
  appointment_id: string
  date: string
  status: string
  items: VisitItem[]
}

export function getClientHistory(clientId: string): Promise<Visit[]> {
  return api.get<Visit[]>(`/clients/${clientId}/history`)
}
