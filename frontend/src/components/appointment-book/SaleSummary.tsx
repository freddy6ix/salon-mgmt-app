import { useQuery } from '@tanstack/react-query'
import { getSaleByAppointment } from '@/api/sales'

interface Props {
  appointmentId: string
}

function fmt(s: string): string {
  const n = parseFloat(s)
  return Number.isFinite(n) ? n.toFixed(2) : '0.00'
}

export default function SaleSummary({ appointmentId }: Props) {
  const { data: sale, isLoading, error } = useQuery({
    queryKey: ['sale', 'by-appointment', appointmentId],
    queryFn: () => getSaleByAppointment(appointmentId),
    retry: false,
  })

  if (isLoading) {
    return <p className="text-xs text-muted-foreground text-center pt-2">Loading sale…</p>
  }

  // 404 (no sale recorded) — silently render nothing rather than an error
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
        </div>
      )}
    </div>
  )
}
