import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listRetailItems, createRetailItem, updateRetailItem, type RetailItem } from '@/api/retailItems'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

function fmt(s: string | null | undefined): string {
  if (!s) return '—'
  const n = parseFloat(s)
  return Number.isFinite(n) ? `$${n.toFixed(2)}` : '—'
}

function RetailItemRow({ item }: { item: RetailItem }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(item.name)
  const [sku, setSku] = useState(item.sku ?? '')
  const [price, setPrice] = useState(item.default_price)
  const [cost, setCost] = useState(item.default_cost ?? '')
  const [gstExempt, setGstExempt] = useState(item.is_gst_exempt)
  const [pstExempt, setPstExempt] = useState(item.is_pst_exempt)
  const [error, setError] = useState<string | null>(null)

  const saveMutation = useMutation({
    mutationFn: () => updateRetailItem(item.id, {
      name: name.trim(),
      sku: sku.trim() || null,
      default_price: price,
      default_cost: cost || null,
      is_gst_exempt: gstExempt,
      is_pst_exempt: pstExempt,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['retail-items'] }); setEditing(false); setError(null) },
    onError: (e: Error) => setError(e.message),
  })

  const toggleMutation = useMutation({
    mutationFn: () => updateRetailItem(item.id, { is_active: !item.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['retail-items'] }),
  })

  if (editing) {
    return (
      <tr className="border-b">
        <td className="px-4 py-2" colSpan={6}>
          <div className="space-y-3 py-1">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><Label className="text-xs">Name</Label>
                <Input value={name} onChange={e => setName(e.target.value)} /></div>
              <div className="space-y-1"><Label className="text-xs">SKU</Label>
                <Input value={sku} onChange={e => setSku(e.target.value)} placeholder="optional" /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><Label className="text-xs">Price ($)</Label>
                <Input type="text" inputMode="decimal" value={price} onChange={e => setPrice(e.target.value)} /></div>
              <div className="space-y-1"><Label className="text-xs">Cost ($)</Label>
                <Input type="text" inputMode="decimal" value={cost} onChange={e => setCost(e.target.value)} placeholder="optional" /></div>
            </div>
            <div className="flex gap-4 text-sm">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={gstExempt} onChange={e => setGstExempt(e.target.checked)} />
                GST exempt
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={pstExempt} onChange={e => setPstExempt(e.target.checked)} />
                PST exempt
              </label>
            </div>
            {error && <p className="text-xs text-destructive">{error}</p>}
            <div className="flex gap-2">
              <Button size="sm" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
                {saveMutation.isPending ? 'Saving…' : 'Save'}
              </Button>
              <Button size="sm" variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
            </div>
          </div>
        </td>
      </tr>
    )
  }

  return (
    <tr className={`border-b text-sm ${!item.is_active ? 'opacity-50' : ''}`}>
      <td className="px-4 py-2.5 font-medium">{item.name}</td>
      <td className="px-4 py-2.5 text-muted-foreground">{item.sku ?? '—'}</td>
      <td className="px-4 py-2.5">{fmt(item.default_price)}</td>
      <td className="px-4 py-2.5 text-muted-foreground">{fmt(item.default_cost)}</td>
      <td className="px-4 py-2.5 text-xs text-muted-foreground">
        {[!item.is_gst_exempt && 'GST', !item.is_pst_exempt && 'PST'].filter(Boolean).join('+') || 'exempt'}
      </td>
      <td className="px-4 py-2.5 text-right">
        <Button size="sm" variant="ghost" className="text-xs h-7" onClick={() => setEditing(true)}>Edit</Button>
        <Button size="sm" variant="ghost" className="text-xs h-7 text-muted-foreground ml-1"
          onClick={() => toggleMutation.mutate()} disabled={toggleMutation.isPending}>
          {item.is_active ? 'Deactivate' : 'Activate'}
        </Button>
      </td>
    </tr>
  )
}

export default function RetailPage() {
  const qc = useQueryClient()
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState('')
  const [newSku, setNewSku] = useState('')
  const [newPrice, setNewPrice] = useState('')
  const [newCost, setNewCost] = useState('')
  const [newGst, setNewGst] = useState(false)
  const [newPst, setNewPst] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['retail-items'],
    queryFn: () => listRetailItems(false),
  })

  const createMutation = useMutation({
    mutationFn: () => createRetailItem({
      name: newName.trim(), sku: newSku.trim() || null,
      default_price: newPrice, default_cost: newCost || null,
      is_gst_exempt: newGst, is_pst_exempt: newPst,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['retail-items'] })
      setAdding(false)
      setNewName(''); setNewSku(''); setNewPrice(''); setNewCost('')
      setNewGst(false); setNewPst(false); setFormError(null)
    },
    onError: (e: Error) => setFormError(e.message),
  })

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!newName.trim() || !newPrice) { setFormError('Name and price are required'); return }
    setFormError(null)
    createMutation.mutate()
  }

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Retail</h1>
            <p className="text-sm text-muted-foreground mt-1">Product catalog for sale at checkout.</p>
          </div>
          {!adding && <Button onClick={() => setAdding(true)}>+ Add item</Button>}
        </div>

        {adding && (
          <form onSubmit={handleAdd} className="border rounded-lg bg-white p-5 space-y-4">
            <h2 className="text-sm font-medium">New retail item</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><Label className="text-xs">Name *</Label>
                <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="L'Oréal Mythic Oil" /></div>
              <div className="space-y-1"><Label className="text-xs">SKU</Label>
                <Input value={newSku} onChange={e => setNewSku(e.target.value)} placeholder="optional" /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><Label className="text-xs">Retail price ($) *</Label>
                <Input type="text" inputMode="decimal" value={newPrice} onChange={e => setNewPrice(e.target.value)} placeholder="0.00" /></div>
              <div className="space-y-1"><Label className="text-xs">Cost ($)</Label>
                <Input type="text" inputMode="decimal" value={newCost} onChange={e => setNewCost(e.target.value)} placeholder="optional" /></div>
            </div>
            <div className="flex gap-4 text-sm">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={newGst} onChange={e => setNewGst(e.target.checked)} />
                GST exempt
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={newPst} onChange={e => setNewPst(e.target.checked)} />
                PST exempt
              </label>
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <div className="flex gap-2">
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Saving…' : 'Save'}
              </Button>
              <Button type="button" variant="outline" onClick={() => { setAdding(false); setFormError(null) }}>Cancel</Button>
            </div>
          </form>
        )}

        <div className="border rounded-lg bg-white overflow-hidden">
          {isLoading ? (
            <p className="p-6 text-sm text-muted-foreground">Loading…</p>
          ) : items.length === 0 ? (
            <p className="p-6 text-sm text-muted-foreground text-center">No retail items yet.</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/30 text-xs text-muted-foreground">
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">SKU</th>
                  <th className="px-4 py-2 text-left">Price</th>
                  <th className="px-4 py-2 text-left">Cost</th>
                  <th className="px-4 py-2 text-left">Tax</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {items.map(item => <RetailItemRow key={item.id} item={item} />)}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
