import { useState } from 'react'
import { format } from 'date-fns'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getCurrentReconciliation,
  listReconciliations,
  openPeriod,
  closePeriod,
  addPettyCash,
  deletePettyCash,
  type CashReconciliation,
} from '@/api/cashReconciliation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const TODAY = format(new Date(), 'yyyy-MM-dd')

function fmt(s: string | null | undefined): string {
  if (!s) return '$0.00'
  const n = parseFloat(s)
  return `$${Number.isFinite(n) ? n.toFixed(2) : '0.00'}`
}

function fmtSigned(s: string | null | undefined): string {
  if (!s) return '$0.00'
  const n = parseFloat(s)
  if (!Number.isFinite(n)) return '$0.00'
  return n >= 0 ? `+$${n.toFixed(2)}` : `-$${Math.abs(n).toFixed(2)}`
}

// ── Petty cash form ───────────────────────────────────────────────────────────

function PettyCashForm({ date }: { date: string }) {
  const qc = useQueryClient()
  const [amount, setAmount] = useState('')
  const [desc, setDesc] = useState('')
  const [sign, setSign] = useState<'out' | 'in'>('out')

  const mutation = useMutation({
    mutationFn: () => addPettyCash(date, {
      amount: sign === 'out' ? `-${Math.abs(parseFloat(amount))}` : `${Math.abs(parseFloat(amount))}`,
      description: desc.trim(),
    }),
    onSuccess: (data) => {
      qc.setQueryData(['till-current'], data)
      setAmount('')
      setDesc('')
    },
  })

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
      className="flex gap-2 flex-wrap items-end"
    >
      <div className="flex rounded-md border border-input overflow-hidden text-sm">
        {(['out', 'in'] as const).map(s => (
          <button
            key={s}
            type="button"
            onClick={() => setSign(s)}
            className={`px-3 py-1.5 transition-colors ${sign === s ? 'bg-foreground text-background' : 'bg-background hover:bg-muted'}`}
          >
            {s === 'out' ? '− Out' : '+ In'}
          </button>
        ))}
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Amount ($)</Label>
        <Input
          type="text"
          inputMode="decimal"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          placeholder="0.00"
          className="w-24"
        />
      </div>
      <div className="space-y-1 flex-1 min-w-[160px]">
        <Label className="text-xs">Description</Label>
        <Input
          value={desc}
          onChange={e => setDesc(e.target.value)}
          placeholder="Coffee, supplies…"
        />
      </div>
      <Button
        type="submit"
        size="sm"
        disabled={!amount || !desc.trim() || mutation.isPending}
      >
        {mutation.isPending ? 'Adding…' : 'Add'}
      </Button>
    </form>
  )
}

// ── Open period view ──────────────────────────────────────────────────────────

function OpenPeriodView({ recon }: { recon: CashReconciliation }) {
  const qc = useQueryClient()
  const [counted, setCounted] = useState('')
  const [deposit, setDeposit] = useState('0.00')
  const [note, setNote] = useState('')
  const [closeError, setCloseError] = useState<string | null>(null)

  const expected = parseFloat(recon.expected_balance)
  const countedNum = parseFloat(counted) || 0
  const variance = Number.isFinite(countedNum) ? Math.round((countedNum - expected) * 100) / 100 : null

  const deleteMutation = useMutation({
    mutationFn: (entryId: string) => deletePettyCash(recon.business_date, entryId),
    onSuccess: (data) => qc.setQueryData(['till-current'], data),
  })

  const closeMutation = useMutation({
    mutationFn: () => closePeriod(recon.business_date, {
      counted_balance: countedNum.toFixed(2),
      deposit_amount: (parseFloat(deposit) || 0).toFixed(2),
      variance_note: note,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['till-current'] })
      qc.invalidateQueries({ queryKey: ['till-history'] })
      setCloseError(null)
    },
    onError: (e: Error) => setCloseError(e.message),
  })

  return (
    <div className="space-y-6">
      {/* Cash summary */}
      <section className="border rounded-lg bg-white overflow-hidden">
        <div className="px-5 py-3 border-b bg-muted/30">
          <h2 className="text-sm font-medium">Cash position — {recon.business_date}</h2>
        </div>
        <div className="p-5 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Opening balance</span>
            <span>{fmt(recon.opening_balance)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Cash sales today</span>
            <span className="text-green-700">{fmt(recon.cash_in)}</span>
          </div>
          {parseFloat(recon.petty_cash_net) !== 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Petty cash net</span>
              <span>{fmtSigned(recon.petty_cash_net)}</span>
            </div>
          )}
          <div className="flex justify-between font-semibold border-t pt-2 mt-1">
            <span>Expected balance</span>
            <span>{fmt(recon.expected_balance)}</span>
          </div>
        </div>
      </section>

      {/* Petty cash */}
      <section className="border rounded-lg bg-white overflow-hidden">
        <div className="px-5 py-3 border-b bg-muted/30">
          <h2 className="text-sm font-medium">Petty cash entries</h2>
        </div>
        <div className="p-5 space-y-4">
          {recon.petty_cash_entries.length === 0 ? (
            <p className="text-sm text-muted-foreground">No entries yet.</p>
          ) : (
            <ul className="space-y-1.5 text-sm">
              {recon.petty_cash_entries.map(e => (
                <li key={e.id} className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">{e.description}</span>
                  <div className="flex items-center gap-3">
                    <span className={parseFloat(e.amount) < 0 ? 'text-destructive' : 'text-green-700'}>
                      {fmtSigned(e.amount)}
                    </span>
                    <button
                      onClick={() => deleteMutation.mutate(e.id)}
                      disabled={deleteMutation.isPending}
                      className="text-xs text-muted-foreground hover:text-destructive"
                    >
                      ×
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <PettyCashForm date={recon.business_date} />
        </div>
      </section>

      {/* Close till */}
      <section className="border rounded-lg bg-white overflow-hidden">
        <div className="px-5 py-3 border-b bg-muted/30">
          <h2 className="text-sm font-medium">Close till</h2>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Counted balance ($)</Label>
              <Input
                type="text"
                inputMode="decimal"
                value={counted}
                onChange={e => setCounted(e.target.value)}
                placeholder={recon.expected_balance}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Bank deposit ($)</Label>
              <Input
                type="text"
                inputMode="decimal"
                value={deposit}
                onChange={e => setDeposit(e.target.value)}
                placeholder="0.00"
              />
            </div>
          </div>

          {counted && variance !== null && (
            <div className={`rounded-md px-3 py-2 text-sm ${
              variance === 0 ? 'bg-green-50 text-green-800' : 'bg-amber-50 text-amber-800'
            }`}>
              {variance === 0
                ? 'Till balanced — no variance.'
                : `Variance: ${fmtSigned(variance.toFixed(2))}`}
            </div>
          )}

          {variance !== null && variance !== 0 && (
            <div className="space-y-1.5">
              <Label>Variance note <span className="text-destructive">*</span></Label>
              <Input
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="Explain the discrepancy…"
              />
            </div>
          )}

          {closeError && <p className="text-sm text-destructive">{closeError}</p>}

          <Button
            onClick={() => closeMutation.mutate()}
            disabled={!counted || closeMutation.isPending || (variance !== 0 && !note.trim())}
          >
            {closeMutation.isPending ? 'Closing…' : 'Close till'}
          </Button>
        </div>
      </section>
    </div>
  )
}

// ── History row ───────────────────────────────────────────────────────────────

function HistoryRow({ recon }: { recon: CashReconciliation }) {
  const [expanded, setExpanded] = useState(false)
  const v = parseFloat(recon.variance ?? '0')

  return (
    <>
      <tr
        className="border-b cursor-pointer hover:bg-muted/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-2.5 text-sm">{recon.business_date}</td>
        <td className="px-4 py-2.5 text-sm">{fmt(recon.expected_balance)}</td>
        <td className="px-4 py-2.5 text-sm">{fmt(recon.counted_balance)}</td>
        <td className={`px-4 py-2.5 text-sm font-medium ${v < 0 ? 'text-destructive' : v > 0 ? 'text-amber-600' : 'text-green-600'}`}>
          {v === 0 ? '—' : fmtSigned(recon.variance)}
        </td>
        <td className="px-4 py-2.5 text-sm text-muted-foreground">{fmt(recon.deposit_amount)}</td>
        <td className="px-4 py-2.5 text-xs text-muted-foreground">{expanded ? '▲' : '▼'}</td>
      </tr>
      {expanded && (
        <tr className="border-b bg-muted/10">
          <td colSpan={6} className="px-4 py-3">
            <div className="text-xs text-muted-foreground space-y-1">
              <div>Opening: {fmt(recon.opening_balance)} · Cash in: {fmt(recon.cash_in)} · Petty cash: {fmtSigned(recon.petty_cash_net)}</div>
              {recon.variance_note && <div>Note: {recon.variance_note}</div>}
              {recon.petty_cash_entries.length > 0 && (
                <div className="mt-2 space-y-0.5">
                  {recon.petty_cash_entries.map(e => (
                    <div key={e.id}>{e.description}: {fmtSigned(e.amount)}</div>
                  ))}
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function TillPage() {
  const qc = useQueryClient()
  const [openingOverride, setOpeningOverride] = useState('')
  const [openError, setOpenError] = useState<string | null>(null)

  const { data: current, isLoading: currentLoading } = useQuery({
    queryKey: ['till-current'],
    queryFn: getCurrentReconciliation,
    retry: false,
  })

  const { data: history = [] } = useQuery({
    queryKey: ['till-history'],
    queryFn: listReconciliations,
  })

  const openMutation = useMutation({
    mutationFn: () => openPeriod(
      TODAY,
      openingOverride ? openingOverride : undefined,
    ),
    onSuccess: (data) => {
      qc.setQueryData(['till-current'], data)
      qc.invalidateQueries({ queryKey: ['till-history'] })
      setOpenError(null)
    },
    onError: (e: Error) => setOpenError(e.message),
  })

  const noOpenPeriod = !currentLoading && !current

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Till</h1>
            <p className="text-sm text-muted-foreground mt-1">End-of-day cash reconciliation.</p>
          </div>
          {current && (
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${
              current.status === 'open'
                ? 'bg-green-100 text-green-800'
                : 'bg-muted text-muted-foreground'
            }`}>
              {current.status === 'open' ? 'Open' : 'Closed'}
            </span>
          )}
        </div>

        {currentLoading && (
          <p className="text-sm text-muted-foreground">Loading…</p>
        )}

        {noOpenPeriod && (
          <section className="border rounded-lg bg-white p-5 space-y-4">
            <p className="text-sm text-muted-foreground">No open till for today. Open one to start tracking cash.</p>
            <div className="flex gap-3 items-end flex-wrap">
              <div className="space-y-1">
                <Label className="text-xs">Opening balance ($) <span className="text-muted-foreground">(leave blank to use previous close)</span></Label>
                <Input
                  type="text"
                  inputMode="decimal"
                  value={openingOverride}
                  onChange={e => setOpeningOverride(e.target.value)}
                  placeholder="0.00"
                  className="w-36"
                />
              </div>
              <Button onClick={() => openMutation.mutate()} disabled={openMutation.isPending}>
                {openMutation.isPending ? 'Opening…' : 'Open today\'s till'}
              </Button>
            </div>
            {openError && <p className="text-sm text-destructive">{openError}</p>}
          </section>
        )}

        {current && current.status === 'open' && <OpenPeriodView recon={current} />}

        {current && current.status === 'closed' && (
          <section className="border rounded-lg bg-white p-5">
            <p className="text-sm text-muted-foreground">Today's till is closed. Closing balance: <strong>{fmt(current.closing_balance)}</strong></p>
          </section>
        )}

        {history.filter(r => r.status === 'closed').length > 0 && (
          <section className="border rounded-lg bg-white overflow-hidden">
            <div className="px-5 py-3 border-b bg-muted/30">
              <h2 className="text-sm font-medium">History (last 30 days)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/20 text-xs text-muted-foreground">
                    <th className="px-4 py-2 text-left">Date</th>
                    <th className="px-4 py-2 text-left">Expected</th>
                    <th className="px-4 py-2 text-left">Counted</th>
                    <th className="px-4 py-2 text-left">Variance</th>
                    <th className="px-4 py-2 text-left">Deposit</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {history.filter(r => r.status === 'closed').map(r => (
                    <HistoryRow key={r.id} recon={r} />
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
