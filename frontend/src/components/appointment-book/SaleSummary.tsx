import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSaleByAppointment, editSalePayments } from '@/api/sales'
import { listPaymentMethods } from '@/api/paymentMethods'
import { Button } from '@/components/ui/button'

interface Props {
  appointmentId: string
}

function fmt(s: string): string {
  const n = parseFloat(s)
  return Number.isFinite(n) ? n.toFixed(2) : '0.00'
}

interface PaymentRow {
  payment_method_id: string
  amount: string
  cashback_amount: string
}

function EditPaymentsDialog({
  saleId,
  saleTotal,
  initialPayments,
  onDone,
}: {
  saleId: string
  saleTotal: string
  initialPayments: PaymentRow[]
  onDone: () => void
}) {
  const qc = useQueryClient()
  const { data: methods = [] } = useQuery({
    queryKey: ['payment-methods', 'active'],
    queryFn: () => listPaymentMethods(true),
  })

  const [rows, setRows] = useState<PaymentRow[]>(initialPayments.map(p => ({ ...p })))
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => editSalePayments(saleId, rows),
    onSuccess: (updated) => {
      qc.setQueryData(['sale', 'by-appointment', updated.appointment_id], updated)
      onDone()
    },
    onError: (e: Error) => setError(e.message),
  })

  function updateRow(idx: number, patch: Partial<PaymentRow>) {
    setRows(rs => rs.map((r, i) => i === idx ? { ...r, ...patch } : r))
  }

  function addRow() {
    const firstMethod = methods[0]
    if (!firstMethod) return
    setRows(rs => [...rs, { payment_method_id: firstMethod.id, amount: '0.00', cashback_amount: '0.00' }])
  }

  function removeRow(idx: number) {
    setRows(rs => rs.filter((_, i) => i !== idx))
  }

  const total = parseFloat(saleTotal)
  const applied = rows.reduce((sum, r) => {
    const amt = parseFloat(r.amount) || 0
    const cb = parseFloat(r.cashback_amount) || 0
    return sum + (amt - cb)
  }, 0)
  const remaining = Math.round((total - applied) * 100) / 100
  const balanced = Math.abs(remaining) < 0.005

  return (
    <div className="mt-2 border rounded-md bg-white p-3 space-y-3">
      <p className="text-xs font-medium">Edit payments</p>

      <div className="space-y-2">
        {rows.map((row, idx) => (
          <div key={idx} className="flex items-center gap-1.5">
            <select
              value={row.payment_method_id}
              onChange={e => updateRow(idx, { payment_method_id: e.target.value })}
              className="flex-1 border border-input rounded px-2 py-1 text-xs bg-background"
            >
              {methods.map(m => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
            <input
              type="number"
              step="0.01"
              min="0"
              value={row.amount}
              onChange={e => updateRow(idx, { amount: e.target.value })}
              className="w-20 border border-input rounded px-2 py-1 text-xs text-right bg-background"
              placeholder="Amount"
            />
            {parseFloat(row.cashback_amount) > 0 && (
              <input
                type="number"
                step="0.01"
                min="0"
                value={row.cashback_amount}
                onChange={e => updateRow(idx, { cashback_amount: e.target.value })}
                className="w-20 border border-input rounded px-2 py-1 text-xs text-right bg-background"
                placeholder="Cashback"
              />
            )}
            {rows.length > 1 && (
              <button
                onClick={() => removeRow(idx)}
                className="text-muted-foreground hover:text-destructive text-xs px-1"
              >✕</button>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={addRow}
        className="text-xs text-muted-foreground hover:text-foreground underline"
      >
        + Add payment line
      </button>

      <div className={`text-xs flex justify-between font-medium ${balanced ? 'text-green-600' : 'text-destructive'}`}>
        <span>{balanced ? 'Balanced' : `${remaining > 0 ? 'Short' : 'Over'} by $${Math.abs(remaining).toFixed(2)}`}</span>
        <span>Total: ${fmt(saleTotal)}</span>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={!balanced || mutation.isPending}
          onClick={() => { setError(null); mutation.mutate() }}
        >
          {mutation.isPending ? 'Saving…' : 'Save'}
        </Button>
        <Button size="sm" variant="outline" onClick={onDone}>Cancel</Button>
      </div>
    </div>
  )
}

export default function SaleSummary({ appointmentId }: Props) {
  const { data: sale, isLoading, error } = useQuery({
    queryKey: ['sale', 'by-appointment', appointmentId],
    queryFn: () => getSaleByAppointment(appointmentId),
    retry: false,
  })
  const [editing, setEditing] = useState(false)

  if (isLoading) {
    return <p className="text-xs text-muted-foreground text-center pt-2">Loading sale…</p>
  }

  if (error || !sale) return null

  const discount = parseFloat(sale.discount_total)
  const showDiscount = Number.isFinite(discount) && discount > 0

  return (
    <div className="rounded-md border bg-muted/30 px-3 py-2 mt-2 space-y-1 text-xs">
      <div className="flex justify-between">
        <span className="text-muted-foreground">Subtotal</span>
        <span>${fmt(sale.subtotal)}</span>
      </div>
      {showDiscount && (
        <div className="flex justify-between text-muted-foreground">
          <span>Discount</span>
          <span>−${fmt(sale.discount_total)}</span>
        </div>
      )}
      <div className="flex justify-between text-muted-foreground">
        <span>GST</span>
        <span>${fmt(sale.gst_amount)}</span>
      </div>
      <div className="flex justify-between text-muted-foreground">
        <span>PST</span>
        <span>${fmt(sale.pst_amount)}</span>
      </div>
      <div className="flex justify-between font-semibold border-t pt-1 mt-1">
        <span>Total</span>
        <span>${fmt(sale.total)}</span>
      </div>

      {sale.payments.length > 0 && (
        <div className="pt-1.5 mt-1.5 border-t space-y-0.5">
          {sale.payments.map(p => {
            const cb = parseFloat(p.cashback_amount)
            return (
              <div key={p.id} className="flex justify-between text-muted-foreground">
                <span>{p.payment_method_label}</span>
                <span>
                  ${fmt(p.amount)}
                  {Number.isFinite(cb) && cb > 0 && (
                    <span className="ml-1 text-[10px]">(−${fmt(p.cashback_amount)} cashback)</span>
                  )}
                </span>
              </div>
            )
          })}
          {sale.is_editable && !editing && (
            <button
              onClick={() => setEditing(true)}
              className="text-[10px] text-muted-foreground hover:text-foreground underline pt-0.5"
            >
              Edit payments
            </button>
          )}
        </div>
      )}

      {editing && (
        <EditPaymentsDialog
          saleId={sale.id}
          saleTotal={sale.total}
          initialPayments={sale.payments.map(p => ({
            payment_method_id: p.payment_method_id,
            amount: p.amount,
            cashback_amount: p.cashback_amount,
          }))}
          onDone={() => setEditing(false)}
        />
      )}
    </div>
  )
}
