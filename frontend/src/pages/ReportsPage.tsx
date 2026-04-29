import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, addMonths, subMonths } from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { getMonthlyReport } from '@/api/reports'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

function fmt(s: string): string {
  const n = parseFloat(s)
  return Number.isFinite(n) ? n.toFixed(2) : '0.00'
}

function SummaryCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white border rounded-lg px-4 py-3 space-y-0.5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-xl font-semibold tabular-nums">${value}</p>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b bg-muted/30">
        <h2 className="text-sm font-medium">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function TableRow({ label, value, sub, bold }: { label: string; value: string; sub?: string; bold?: boolean }) {
  return (
    <div className={`flex justify-between items-baseline px-4 py-2 border-b last:border-0 text-sm ${bold ? 'font-semibold' : ''}`}>
      <span className={bold ? '' : 'text-muted-foreground'}>{label}{sub && <span className="ml-2 text-xs font-normal text-muted-foreground">{sub}</span>}</span>
      <span className="tabular-nums">${value}</span>
    </div>
  )
}

export default function ReportsPage() {
  const now = new Date()
  const [cursor, setCursor] = useState(new Date(now.getFullYear(), now.getMonth(), 1))

  const year = cursor.getFullYear()
  const month = cursor.getMonth() + 1

  const { data: report, isLoading } = useQuery({
    queryKey: ['monthly-report', year, month],
    queryFn: () => getMonthlyReport(year, month),
  })

  const isCurrentMonth = year === now.getFullYear() && month === now.getMonth() + 1

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">

        {/* Header + month nav */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Sales report</h1>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => setCursor(subMonths(cursor, 1))}>
              <ChevronLeft size={16} />
            </Button>
            <span className="text-sm font-medium w-32 text-center">
              {format(cursor, 'MMMM yyyy')}
            </span>
            <Button variant="outline" size="icon" onClick={() => setCursor(addMonths(cursor, 1))} disabled={isCurrentMonth}>
              <ChevronRight size={16} />
            </Button>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)}
            </div>
            <Skeleton className="h-40 rounded-lg" />
            <Skeleton className="h-40 rounded-lg" />
          </div>
        ) : !report ? null : report.sale_count === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-16">No completed sales in {format(cursor, 'MMMM yyyy')}.</p>
        ) : (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <SummaryCard label="Revenue" value={fmt(report.total)} />
              <div className="bg-white border rounded-lg px-4 py-3 space-y-0.5">
                <p className="text-xs text-muted-foreground">Sales</p>
                <p className="text-xl font-semibold tabular-nums">{report.sale_count}</p>
              </div>
              <SummaryCard label="Tax collected" value={fmt(String(parseFloat(report.gst_amount) + parseFloat(report.pst_amount)))} sub="GST + PST" />
              <SummaryCard label="Avg. sale" value={fmt(String(parseFloat(report.total) / report.sale_count))} />
            </div>

            {/* Revenue breakdown */}
            <Section title="Revenue breakdown">
              <TableRow label="Services" value={fmt(report.service_total)} />
              <TableRow label="Retail" value={fmt(report.retail_total)} />
              {parseFloat(report.discount_total) > 0 && (
                <div className="flex justify-between px-4 py-2 border-b text-sm text-muted-foreground">
                  <span>Discounts</span>
                  <span className="tabular-nums">−${fmt(report.discount_total)}</span>
                </div>
              )}
              <TableRow label="Subtotal" value={fmt(report.subtotal)} />
              <TableRow label="GST (5%)" value={fmt(report.gst_amount)} />
              <TableRow label="PST (8%)" value={fmt(report.pst_amount)} />
              <TableRow label="Total" value={fmt(report.total)} bold />
            </Section>

            {/* By provider */}
            {report.by_provider.length > 0 && (
              <Section title="By provider (services)">
                {report.by_provider.map(r => (
                  <TableRow key={r.provider_name} label={r.provider_name} value={fmt(r.total)} sub={`${r.sale_count} ${r.sale_count === 1 ? 'sale' : 'sales'}`} />
                ))}
              </Section>
            )}

            {/* By payment method */}
            {report.by_payment_method.length > 0 && (
              <Section title="By payment method">
                {report.by_payment_method.map(r => {
                  const hasCashback = parseFloat(r.cashback) > 0
                  return (
                    <div key={r.label} className="flex justify-between items-baseline px-4 py-2 border-b last:border-0 text-sm">
                      <span className="text-muted-foreground">{r.label}</span>
                      <span className="tabular-nums text-right">
                        ${fmt(r.gross)}
                        {hasCashback && (
                          <span className="ml-2 text-xs text-muted-foreground">
                            −${fmt(r.cashback)} cashback · net ${fmt(r.net)}
                          </span>
                        )}
                      </span>
                    </div>
                  )
                })}
              </Section>
            )}

            {/* Daily breakdown */}
            <Section title="Daily totals">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-xs text-muted-foreground">
                      <th className="px-4 py-2 text-left font-medium">Date</th>
                      <th className="px-4 py-2 text-right font-medium">Sales</th>
                      <th className="px-4 py-2 text-right font-medium">Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.by_day.map(r => (
                      <tr key={r.date} className="border-b last:border-0 hover:bg-muted/20">
                        <td className="px-4 py-2">
                          {format(new Date(r.date + 'T12:00:00'), 'EEE, MMM d')}
                        </td>
                        <td className="px-4 py-2 text-right text-muted-foreground">{r.sale_count}</td>
                        <td className="px-4 py-2 text-right tabular-nums">${fmt(r.total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </>
        )}
      </div>
    </div>
  )
}
