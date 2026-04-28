import { api } from './client'

export interface RetailItem {
  id: string
  sku: string | null
  name: string
  description: string | null
  default_price: string
  default_cost: string | null
  is_gst_exempt: boolean
  is_pst_exempt: boolean
  is_active: boolean
}

export function listRetailItems(activeOnly = false): Promise<RetailItem[]> {
  return api.get<RetailItem[]>(`/retail-items${activeOnly ? '?active_only=true' : ''}`)
}

export function createRetailItem(body: {
  sku?: string | null
  name: string
  description?: string | null
  default_price: string
  default_cost?: string | null
  is_gst_exempt?: boolean
  is_pst_exempt?: boolean
}): Promise<RetailItem> {
  return api.post<RetailItem>('/retail-items', body)
}

export function updateRetailItem(id: string, body: Partial<{
  sku: string | null
  name: string
  description: string | null
  default_price: string
  default_cost: string | null
  is_gst_exempt: boolean
  is_pst_exempt: boolean
  is_active: boolean
}>): Promise<RetailItem> {
  return api.patch<RetailItem>(`/retail-items/${id}`, body)
}
