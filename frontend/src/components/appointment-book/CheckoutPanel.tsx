import { useState, useEffect, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Appointment } from '@/api/appointments'
import { createSale, PAYMENT_TYPES, PAYMENT_LABEL, type PaymentType } from '@/api/sales'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

interface Props {
  appointment: Appointment
  date: string
  onClose: () => void
  onCompleted: () => void
}

interface ItemDraft {
  appointment_item_id: string
  description: string
  providerName: string
  unitPrice: string
  discount: string
}

interface PaymentDraft {
  payment_type: PaymentType
  amount: string
}

const GST_RATE = 0.05
const PST_RATE = 0.08

function toMoney(s: string): number {
  const n = parseFloat(s)
  return Number.isFinite(n) ? n : 0
}

function fmt(n: number): string {
  return n.toFixed(2)
}

export default function CheckoutPanel({ appointment, onClose, onCompleted }: Props) {
  const qc = useQueryClient()

  const [items, setItems] = useState<ItemDraft[]>(() =>
    appointment.items.map(it => ({
      appointment_item_id: it.id,
      description: it.service.name,
      providerName: it.provider.display_name,
      unitPrice: it.price.toFixed(2),
      discount: '0.00',
    }))
  )
  const [tip, setTip] = useState('0.00')
  const [notes, setNotes] = useState('')
  const [payments, setPayments] = useState<PaymentDraft[]>([
    { payment_type: 'cash', amount: '0.00' },
  ])
  const [error, setError] = useState<string | null>(null)

  // Compute totals
  const totals = useMemo(() => {
    const subtotal = items.reduce(
      (sum, i) => sum + Math.max(0, toMoney(i.unitPrice) - toMoney(i.discount)),
      0,
    )
    const discountTotal = items.reduce((sum, i) => sum + toMoney(i.discount), 0)
    const gst = Math.round(subtotal * GST_RATE * 100) / 100
    const pst = Math.round(subtotal * PST_RATE * 100) / 100
    const tipAmt = toMoney(tip)
    const total = Math.round((subtotal + gst + pst + tipAmt) * 100) / 100
    const paid = payments.reduce((sum, p) => sum + toMoney(p.amount), 0)
    const remaining = Math.round((total - paid) * 100) / 100
    return { subtotal, discountTotal, gst, pst, tip: tipAmt, total, remaining }
  }, [items, tip, payments])

  // When the total changes (and there's only one payment row at default), update it
  useEffect(() => {
    if (payments.length === 1 && payments[0].amount === '0.00') {
      setPayments([{ ...payments[0], amount: fmt(totals.total) }])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totals.total])

  function updateItem(idx: number, patch: Partial<ItemDraft>) {
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, ...patch } : it))
  }

  function updatePayment(idx: number, patch: Partial<PaymentDraft>) {
    setPayments(prev => prev.map((p, i) => i === idx ? { ...p, ...patch } : p))
  }

  function addPaymentRow() {
    setPayments(prev => [...prev, { payment_type: 'cash', amount: fmt(Math.max(0, totals.remaining)) }])
  }

  function removePaymentRow(idx: number) {
    setPayments(prev => prev.filter((_, i) => i !== idx))
  }

  const mutation = useMutation({
    mutationFn: () => createSale({
      appointment_id: appointment.id,
      tip_amount: fmt(totals.tip),
      notes: notes.trim() || null,
      items: items.map(i => ({
        appointment_item_id: i.appointment_item_id,
        unit_price: fmt(toMoney(i.unitPrice)),
        discount_amount: fmt(toMoney(i.discount)),
      })),
      payments: payments.map(p => ({ payment_type: p.payment_type, amount: fmt(toMoney(p.amount)) })),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointments'] })
      onCompleted()
    },
    onError: (err: unknown) => setError((err as Error).message ?? 'Checkout failed'),
  })

  function handleSubmit() {
    setError(null)
    if (totals.remaining !== 0) {
      setError(`Payments must equal total. Remaining: $${fmt(totals.remaining)}`)
      return
    }
    mutation.mutate()
  }

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[440px] bg-white shadow-2xl flex flex-col border-l">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b flex-shrink-0">
        <div>
          <h2 className="text-base font-semibold">Checkout</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {appointment.client.first_name} {appointment.client.last_name}
          </p>
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl leading-none ml-3">×</button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">

        {/* Items */}
        <div className="space-y-2">
          <Label>Items</Label>
          {items.map((it, idx) => {
            const lineTotal = Math.max(0, toMoney(it.unitPrice) - toMoney(it.discount))
            const overDiscount = toMoney(it.discount) > toMoney(it.unitPrice)
            return (
              <div key={it.appointment_item_id} className="rounded-md border p-3 space-y-2">
                <p className="text-sm font-medium">{it.description}</p>
                <p className="text-xs text-muted-foreground">{it.providerName}</p>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-xs text-muted-foreground">Price ($)</label>
                    <input
                      type="text"
                      inputMode="decimal"
                      value={it.unitPrice}
                      onChange={e => updateItem(idx, { unitPrice: e.target.value })}
                      className="w-full border border-input rounded-md px-2 py-1.5 text-sm bg-background mt-0.5"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Discount ($)</label>
                    <input
                      type="text"
                      inputMode="decimal"
                      value={it.discount}
                      onChange={e => updateItem(idx, { discount: e.target.value })}
                      className={`w-full border rounded-md px-2 py-1.5 text-sm bg-background mt-0.5 ${
                        overDiscount ? 'border-destructive' : 'border-input'
                      }`}
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Line</label>
                    <div className="px-2 py-1.5 text-sm mt-0.5 font-medium">${fmt(lineTotal)}</div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Tip */}
        <div className="space-y-1.5">
          <Label htmlFor="tip">Tip ($)</Label>
          <input
            id="tip"
            type="text"
            inputMode="decimal"
            value={tip}
            onChange={e => setTip(e.target.value)}
            className="w-32 border border-input rounded-md px-2 py-1.5 text-sm bg-background"
          />
        </div>

        {/* Totals */}
        <div className="rounded-md bg-muted/40 p-3 space-y-1 text-sm">
          <div className="flex justify-between"><span>Subtotal</span><span>${fmt(totals.subtotal)}</span></div>
          {totals.discountTotal > 0 && (
            <div className="flex justify-between text-muted-foreground">
              <span>Discount</span><span>−${fmt(totals.discountTotal)}</span>
            </div>
          )}
          <div className="flex justify-between"><span>GST (5%)</span><span>${fmt(totals.gst)}</span></div>
          <div className="flex justify-between"><span>PST (8%)</span><span>${fmt(totals.pst)}</span></div>
          {totals.tip > 0 && (
            <div className="flex justify-between"><span>Tip</span><span>${fmt(totals.tip)}</span></div>
          )}
          <div className="flex justify-between font-semibold border-t pt-1 mt-1">
            <span>Total</span><span>${fmt(totals.total)}</span>
          </div>
        </div>

        {/* Payments */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Payment</Label>
            <button
              type="button"
              onClick={addPaymentRow}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              + Split
            </button>
          </div>
          {payments.map((p, idx) => (
            <div key={idx} className="flex gap-2 items-center">
              <select
                value={p.payment_type}
                onChange={e => updatePayment(idx, { payment_type: e.target.value as PaymentType })}
                className="border border-input rounded-md px-2 py-1.5 text-sm bg-background flex-1"
              >
                {PAYMENT_TYPES.map(t => (
                  <option key={t} value={t}>{PAYMENT_LABEL[t]}</option>
                ))}
              </select>
              <input
                type="text"
                inputMode="decimal"
                value={p.amount}
                onChange={e => updatePayment(idx, { amount: e.target.value })}
                className="w-28 border border-input rounded-md px-2 py-1.5 text-sm bg-background"
              />
              {payments.length > 1 && (
                <button
                  type="button"
                  onClick={() => removePaymentRow(idx)}
                  className="text-muted-foreground hover:text-destructive text-lg leading-none px-1"
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <p className={`text-xs ${totals.remaining === 0 ? 'text-green-600' : 'text-destructive'}`}>
            {totals.remaining === 0
              ? 'Payments balanced'
              : totals.remaining > 0
                ? `Remaining: $${fmt(totals.remaining)}`
                : `Over by: $${fmt(-totals.remaining)}`}
          </p>
        </div>

        {/* Notes */}
        <div className="space-y-1.5">
          <Label htmlFor="notes">Notes</Label>
          <textarea
            id="notes"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            rows={2}
            placeholder="Optional…"
            className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background resize-none"
          />
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {/* Footer */}
      <div className="border-t px-5 py-4 flex gap-2 flex-shrink-0">
        <Button variant="outline" onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          disabled={mutation.isPending || totals.remaining !== 0}
          className="flex-1"
        >
          {mutation.isPending ? 'Processing…' : `Complete checkout · $${fmt(totals.total)}`}
        </Button>
      </div>
    </div>
  )
}
