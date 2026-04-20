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
