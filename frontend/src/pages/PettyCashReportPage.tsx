import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, addMonths, subMonths } from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { getPettyCashReport } from '@/api/reports'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

function fmt(s: string): string {
  const n = parseFloat(s)
  return Number.isFinite(n) ? n.toFixed(2) : '0.00'
}

export default function PettyCashReportPage() {
  const now = new Date()
  const [cursor, setCursor] = useState(new Date(now.getFullYear(), now.getMonth(), 1))

  const year = cursor.getFullYear()
  const month = cursor.getMonth() + 1
  const isCurrentMonth = year === now.getFullYear() && month === now.getMonth() + 1

  const { data: report, isLoading } = useQuery({
    queryKey: ['petty-cash-report', year, month],
    queryFn: () => getPettyCashReport(year, month),
  })

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">

        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Petty cash report</h1>
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
            <Skeleton className="h-10 rounded-lg" />
            <Skeleton className="h-48 rounded-lg" />
          </div>
        ) : !report || report.entries.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-16">
            No petty cash entries in {format(cursor, 'MMMM yyyy')}.
          </p>
        ) : (
          <>
            {/* Total card */}
            <div className="bg-white border rounded-lg px-4 py-3 inline-flex flex-col gap-0.5">
              <p className="text-xs text-muted-foreground">Total disbursed</p>
              <p className="text-xl font-semibold tabular-nums">${fmt(report.total)}</p>
            </div>

            {/* Entries table */}
            <div className="bg-white border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b bg-muted/30">
                <h2 className="text-sm font-medium">Entries</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-xs text-muted-foreground">
                      <th className="px-4 py-2 text-left font-medium">Date</th>
                      <th className="px-4 py-2 text-left font-medium">Description</th>
                      <th className="px-4 py-2 text-right font-medium">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.entries.map((e, i) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-muted/20">
                        <td className="px-4 py-2 whitespace-nowrap text-muted-foreground">
                          {format(new Date(e.date + 'T12:00:00'), 'EEE, MMM d')}
                        </td>
                        <td className="px-4 py-2">{e.description}</td>
                        <td className="px-4 py-2 text-right tabular-nums">${fmt(e.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t bg-muted/20">
                      <td className="px-4 py-2 font-semibold" colSpan={2}>Total</td>
                      <td className="px-4 py-2 text-right tabular-nums font-semibold">${fmt(report.total)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
