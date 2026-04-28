import { api } from './client'

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
  payment_method_id: string
  payment_method_code: string
  payment_method_label: string
  amount: string
  cashback_amount: string
}

export interface Sale {
  id: string
  appointment_id: string
  client_id: string
  subtotal: string
  discount_total: string
  gst_amount: string
  pst_amount: string
  total: string
  status: 'pending' | 'completed'
  completed_at: string | null
  notes: string | null
  items: SaleItem[]
  payments: SalePayment[]
}

export interface SaleItemIn {
  appointment_item_id?: string | null
  retail_item_id?: string | null
  unit_price: string
  discount_amount: string
  promotion_id?: string | null
  is_gst_exempt?: boolean
  is_pst_exempt?: boolean
}

export interface SalePaymentIn {
  payment_method_id: string
  amount: string
  cashback_amount: string
}

export interface SaleIn {
  appointment_id: string
  notes?: string | null
  items: SaleItemIn[]
  payments: SalePaymentIn[]
}

export function createSale(body: SaleIn): Promise<Sale> {
  return api.post<Sale>('/sales', body)
}

export function sendReceipt(saleId: string, to: string): Promise<void> {
  return api.post<void>(`/sales/${saleId}/send-receipt`, { to })
}

export function getSaleByAppointment(appointmentId: string): Promise<Sale> {
  return api.get<Sale>(`/sales/by-appointment/${appointmentId}`)
}
