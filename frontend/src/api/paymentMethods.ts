import { api } from './client'

export type PaymentMethodKind = 'cash' | 'card' | 'transfer' | 'other'

export const KIND_OPTIONS: { value: PaymentMethodKind; label: string }[] = [
  { value: 'cash', label: 'Cash' },
  { value: 'card', label: 'Card' },
  { value: 'transfer', label: 'Transfer' },
  { value: 'other', label: 'Other' },
]

export interface PaymentMethod {
  id: string
  code: string
  label: string
  kind: PaymentMethodKind
  is_active: boolean
  sort_order: number
}

export interface PaymentMethodIn {
  code: string
  label: string
  kind: PaymentMethodKind
  is_active?: boolean
  sort_order?: number
}

export interface PaymentMethodPatch {
  code?: string
  label?: string
  kind?: PaymentMethodKind
  is_active?: boolean
  sort_order?: number
}

export function listPaymentMethods(activeOnly = false): Promise<PaymentMethod[]> {
  const qs = activeOnly ? '?active_only=true' : ''
  return api.get<PaymentMethod[]>(`/payment-methods${qs}`)
}

export function createPaymentMethod(body: PaymentMethodIn): Promise<PaymentMethod> {
  return api.post<PaymentMethod>('/payment-methods', body)
}

export function updatePaymentMethod(id: string, body: PaymentMethodPatch): Promise<PaymentMethod> {
  return api.patch<PaymentMethod>(`/payment-methods/${id}`, body)
}
