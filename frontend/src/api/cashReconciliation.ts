import { api } from './client'

export interface PettyCashEntry {
  id: string
  amount: string
  description: string
  created_at: string
}

export interface CashReconciliation {
  id: string
  business_date: string      // YYYY-MM-DD
  opening_balance: string
  cash_in: string
  petty_cash_net: string
  expected_balance: string
  counted_balance: string | null
  deposit_amount: string
  closing_balance: string | null
  variance: string | null
  variance_note: string | null
  status: 'open' | 'closed'
  closed_at: string | null
  petty_cash_entries: PettyCashEntry[]
}

export function getCurrentReconciliation(): Promise<CashReconciliation> {
  return api.get<CashReconciliation>('/cash-reconciliation/current')
}

export function listReconciliations(): Promise<CashReconciliation[]> {
  return api.get<CashReconciliation[]>('/cash-reconciliation')
}

export function getReconciliation(date: string): Promise<CashReconciliation> {
  return api.get<CashReconciliation>(`/cash-reconciliation/${date}`)
}

export function openPeriod(businessDate: string, openingBalance?: string): Promise<CashReconciliation> {
  return api.post<CashReconciliation>('/cash-reconciliation', {
    business_date: businessDate,
    ...(openingBalance !== undefined ? { opening_balance: openingBalance } : {}),
  })
}

export function closePeriod(
  date: string,
  body: { counted_balance: string; deposit_amount: string; variance_note: string },
): Promise<CashReconciliation> {
  return api.post<CashReconciliation>(`/cash-reconciliation/${date}/close`, body)
}

export function addPettyCash(
  date: string,
  body: { amount: string; description: string },
): Promise<CashReconciliation> {
  return api.post<CashReconciliation>(`/cash-reconciliation/${date}/petty-cash`, body)
}

export function deletePettyCash(date: string, entryId: string): Promise<CashReconciliation> {
  return api.delete<CashReconciliation>(`/cash-reconciliation/${date}/petty-cash/${entryId}`)
}
