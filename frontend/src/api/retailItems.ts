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
  on_hand: number
}

export interface StockMovement {
  id: string
  kind: 'receive' | 'sell' | 'adjust' | 'return'
  quantity: number
  unit_cost: string | null
  note: string | null
  created_at: string
}

export interface ItemStock {
  on_hand: number
  movements: StockMovement[]
}

export function getItemStock(id: string): Promise<ItemStock> {
  return api.get<ItemStock>(`/retail-items/${id}/stock`)
}

export function receiveStock(id: string, body: { quantity: number; unit_cost?: string | null; note?: string | null }): Promise<ItemStock> {
  return api.post<ItemStock>(`/retail-items/${id}/stock/receive`, body)
}

export function adjustStock(id: string, body: { counted: number; note: string }): Promise<ItemStock> {
  return api.post<ItemStock>(`/retail-items/${id}/stock/adjust`, body)
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
