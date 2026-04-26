import { api } from './client'

export const PAYMENT_TYPES = ['cash', 'debit', 'visa', 'mastercard', 'amex', 'e_transfer'] as const
export type PaymentType = typeof PAYMENT_TYPES[number]

export const PAYMENT_LABEL: Record<PaymentType, string> = {
  cash: 'Cash',
  debit: 'Debit',
  visa: 'Visa',
  mastercard: 'Mastercard',
  amex: 'AMEX',
  e_transfer: 'E-Transfer',
}

export interface SaleItem {
  id: string
  description: string
  provider_id: string
  sequence: number
  unit_price: string
  discount_amount: string
  line_total: string
}

export interface SalePayment {
  id: string
  payment_type: PaymentType
  amount: string
}

export interface Sale {
  id: string
  appointment_id: string
  client_id: string
  subtotal: string
  discount_total: string
  gst_amount: string
  pst_amount: string
  tip_amount: string
  total: string
  status: 'pending' | 'completed'
  completed_at: string | null
  notes: string | null
  items: SaleItem[]
  payments: SalePayment[]
}

export interface SaleItemIn {
  appointment_item_id: string
  unit_price: string
  discount_amount: string
}

export interface SalePaymentIn {
  payment_type: PaymentType
  amount: string
}

export interface SaleIn {
  appointment_id: string
  tip_amount: string
  notes?: string | null
  items: SaleItemIn[]
  payments: SalePaymentIn[]
}

export function createSale(body: SaleIn): Promise<Sale> {
  return api.post<Sale>('/sales', body)
}

export function getSaleByAppointment(appointmentId: string): Promise<Sale> {
  return api.get<Sale>(`/sales/by-appointment/${appointmentId}`)
}
