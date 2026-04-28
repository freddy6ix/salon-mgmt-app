import { api } from './client'

export type PromotionKind = 'percent' | 'amount'

export interface Promotion {
  id: string
  code: string
  label: string
  kind: PromotionKind
  value: string   // numeric string
  is_active: boolean
  sort_order: number
}

export function listPromotions(activeOnly = false): Promise<Promotion[]> {
  return api.get<Promotion[]>(`/promotions${activeOnly ? '?active_only=true' : ''}`)
}

export function createPromotion(body: {
  code: string; label: string; kind: PromotionKind; value: string; sort_order?: number
}): Promise<Promotion> {
  return api.post<Promotion>('/promotions', body)
}

export function updatePromotion(id: string, body: Partial<{
  code: string; label: string; kind: PromotionKind; value: string; is_active: boolean; sort_order: number
}>): Promise<Promotion> {
  return api.patch<Promotion>(`/promotions/${id}`, body)
}

/** Compute the discount amount for a given promotion and unit price (client-side). */
export function applyPromotion(promo: Promotion, unitPrice: number): number {
  const v = parseFloat(promo.value)
  if (!Number.isFinite(v)) return 0
  if (promo.kind === 'percent') {
    return Math.round(unitPrice * (v / 100) * 100) / 100
  }
  return Math.min(v, unitPrice)
}
