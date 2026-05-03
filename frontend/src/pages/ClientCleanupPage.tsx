import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeftRight, Merge, Users, X, UserPlus, Trash2 } from 'lucide-react'
import {
  type ClientDetail, type DuplicatePair, type Household, type HouseholdMember,
  getDuplicatePairs, mergeClients, listHouseholds, createHousehold,
  deleteHousehold, setClientHousehold,
} from '@/api/clientCleanup'
import { searchClients } from '@/api/clients'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

// ── Shared ────────────────────────────────────────────────────────────────────

const REASON_LABEL: Record<string, string> = {
  email: 'Same email',
  phone: 'Same phone',
  name: 'Same name',
}

// ── Client card ───────────────────────────────────────────────────────────────

function ClientCard({
  client,
  recommended,
}: {
  client: ClientDetail
  recommended: boolean
}) {
  return (
    <div className={`flex-1 rounded-lg border p-4 space-y-1.5 ${recommended ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'bg-white'}`}>
      {recommended && (
        <Badge className="mb-1 text-xs">Recommended primary</Badge>
      )}
      <p className="font-semibold text-sm">{client.first_name} {client.last_name}</p>
      {client.email && <p className="text-xs text-muted-foreground">{client.email}</p>}
      {client.cell_phone && <p className="text-xs text-muted-foreground">{client.cell_phone}</p>}
      <div className="flex gap-3 pt-1">
        <span className="text-xs text-muted-foreground">{client.appointment_count} appt{client.appointment_count !== 1 ? 's' : ''}</span>
        {client.no_show_count > 0 && <span className="text-xs text-muted-foreground">{client.no_show_count} no-show{client.no_show_count !== 1 ? 's' : ''}</span>}
        {client.is_vip && <span className="text-xs font-medium text-amber-600">VIP</span>}
      </div>
    </div>
  )
}

// ── Duplicate pair card ───────────────────────────────────────────────────────

function DuplicatePairCard({
  pair,
  onMerged,
  onSkip,
}: {
  pair: DuplicatePair
  onMerged: () => void
  onSkip: () => void
}) {
  const [swapped, setSwapped] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const primary = swapped ? pair.client_b : pair.client_a
  const secondary = swapped ? pair.client_a : pair.client_b
  const recommendedId = pair.recommended_primary_id

  const mutation = useMutation({
    mutationFn: () => mergeClients(primary.id, secondary.id),
    onSuccess: onMerged,
    onError: (e: unknown) => setError((e as Error).message ?? 'Merge failed'),
  })

  return (
    <div className="border rounded-xl p-4 bg-muted/20 space-y-3">
      <div className="flex items-center justify-between">
        <Badge variant="outline" className="text-xs">{REASON_LABEL[pair.reason] ?? pair.reason}</Badge>
        <button onClick={onSkip} className="text-muted-foreground hover:text-foreground transition-colors" title="Skip">
          <X size={15} />
        </button>
      </div>

      <div className="flex items-start gap-3">
        <ClientCard client={primary} recommended={primary.id === recommendedId} />

        <button
          onClick={() => setSwapped(s => !s)}
          className="mt-6 p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
          title="Swap primary"
        >
          <ArrowLeftRight size={14} />
        </button>

        <ClientCard client={secondary} recommended={secondary.id === recommendedId} />
      </div>

      <div className="flex items-center justify-between pt-1">
        <p className="text-xs text-muted-foreground">
          Merging keeps <span className="font-medium">{primary.first_name} {primary.last_name}</span> and
          moves all history from <span className="font-medium">{secondary.first_name} {secondary.last_name}</span>
        </p>
        <div className="flex items-center gap-2 flex-shrink-0">
          {error && <span className="text-xs text-destructive">{error}</span>}
          <Button
            size="sm"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="gap-1.5"
          >
            <Merge size={13} />
            {mutation.isPending ? 'Merging…' : 'Merge'}
          </Button>
        </div>
      </div>
    </div>
  )
}

// ── Duplicates tab ────────────────────────────────────────────────────────────

function DuplicatesTab() {
  const qc = useQueryClient()
  const { data: pairs = [], isLoading } = useQuery({
    queryKey: ['duplicate-pairs'],
    queryFn: getDuplicatePairs,
  })
  const [skipped, setSkipped] = useState<Set<string>>(new Set())

  const visible = pairs.filter(p => !skipped.has(`${p.client_a.id}:${p.client_b.id}`))

  const skip = (pair: DuplicatePair) =>
    setSkipped(s => new Set(s).add(`${pair.client_a.id}:${pair.client_b.id}`))

  const onMerged = () => {
    qc.invalidateQueries({ queryKey: ['duplicate-pairs'] })
    qc.invalidateQueries({ queryKey: ['clients'] })
  }

  if (isLoading) return <p className="text-sm text-muted-foreground py-8 text-center">Scanning for duplicates…</p>

  if (visible.length === 0)
    return (
      <div className="py-16 text-center">
        <p className="text-sm font-medium mb-1">No duplicates found</p>
        <p className="text-xs text-muted-foreground">All client records look unique.</p>
      </div>
    )

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">{visible.length} potential duplicate{visible.length !== 1 ? 's' : ''} found</p>
      {visible.map(pair => (
        <DuplicatePairCard
          key={`${pair.client_a.id}:${pair.client_b.id}`}
          pair={pair}
          onMerged={onMerged}
          onSkip={() => skip(pair)}
        />
      ))}
    </div>
  )
}

// ── Client search for household ───────────────────────────────────────────────

function ClientSearch({
  placeholder,
  excludeIds,
  onSelect,
}: {
  placeholder: string
  excludeIds: string[]
  onSelect: (id: string, name: string) => void
}) {
  const [q, setQ] = useState('')
  const { data: results = [] } = useQuery({
    queryKey: ['clients', q],
    queryFn: () => searchClients(q),
    enabled: q.length >= 1,
  })
  const filtered = results.filter(r => !excludeIds.includes(r.id))

  return (
    <div className="relative">
      <input
        value={q}
        onChange={e => setQ(e.target.value)}
        placeholder={placeholder}
        className="w-full border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
      />
      {q.length >= 1 && filtered.length > 0 && (
        <div className="absolute top-full mt-1 w-full bg-white border rounded-md shadow-md z-10 max-h-48 overflow-y-auto">
          {filtered.map(r => (
            <button
              key={r.id}
              onClick={() => { onSelect(r.id, `${r.first_name} ${r.last_name}`); setQ('') }}
              className="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors"
            >
              {r.last_name}, {r.first_name}
              {r.email && <span className="ml-2 text-xs text-muted-foreground">{r.email}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Household card ────────────────────────────────────────────────────────────

function HouseholdCard({ household }: { household: Household }) {
  const qc = useQueryClient()

  const removeMutation = useMutation({
    mutationFn: (clientId: string) => setClientHousehold(clientId, null),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['households'] }),
  })

  const addMutation = useMutation({
    mutationFn: (clientId: string) => setClientHousehold(clientId, household.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['households'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteHousehold(household.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['households'] }),
  })

  const memberIds = household.members.map(m => m.id)

  return (
    <div className="border rounded-xl p-4 bg-white space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {household.members.map(m => (
            <div key={m.id} className="flex items-center gap-1 bg-muted rounded-full pl-3 pr-1 py-0.5">
              <span className="text-xs font-medium">{m.first_name} {m.last_name}</span>
              <button
                onClick={() => removeMutation.mutate(m.id)}
                disabled={removeMutation.isPending}
                className="p-0.5 rounded-full hover:bg-muted-foreground/20 text-muted-foreground hover:text-foreground transition-colors"
                title={`Remove ${m.first_name}`}
              >
                <X size={11} />
              </button>
            </div>
          ))}
        </div>
        <button
          onClick={() => deleteMutation.mutate()}
          disabled={deleteMutation.isPending}
          className="p-1.5 text-muted-foreground hover:text-destructive transition-colors flex-shrink-0"
          title="Delete household"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <ClientSearch
        placeholder="Add member…"
        excludeIds={memberIds}
        onSelect={(id) => addMutation.mutate(id)}
      />
    </div>
  )
}

// ── Households tab ────────────────────────────────────────────────────────────

function HouseholdsTab() {
  const qc = useQueryClient()
  const { data: households = [], isLoading } = useQuery({
    queryKey: ['households'],
    queryFn: listHouseholds,
  })

  const [showCreate, setShowCreate] = useState(false)
  const [newMembers, setNewMembers] = useState<{ id: string; name: string }[]>([])

  const createMutation = useMutation({
    mutationFn: () => createHousehold(newMembers.map(m => m.id)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['households'] })
      setShowCreate(false)
      setNewMembers([])
    },
  })

  if (isLoading) return <p className="text-sm text-muted-foreground py-8 text-center">Loading…</p>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-xs text-muted-foreground">{households.length} household{households.length !== 1 ? 's' : ''}</p>
        <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setShowCreate(s => !s)}>
          <UserPlus size={13} />
          New household
        </Button>
      </div>

      {showCreate && (
        <div className="border rounded-xl p-4 bg-muted/20 space-y-3">
          <p className="text-sm font-medium">New household</p>
          <div className="flex flex-wrap gap-2 min-h-[28px]">
            {newMembers.map(m => (
              <div key={m.id} className="flex items-center gap-1 bg-white border rounded-full pl-3 pr-1 py-0.5">
                <span className="text-xs">{m.name}</span>
                <button
                  onClick={() => setNewMembers(ms => ms.filter(x => x.id !== m.id))}
                  className="p-0.5 rounded-full hover:bg-muted text-muted-foreground transition-colors"
                >
                  <X size={11} />
                </button>
              </div>
            ))}
          </div>
          <ClientSearch
            placeholder="Search clients to add…"
            excludeIds={newMembers.map(m => m.id)}
            onSelect={(id, name) => setNewMembers(ms => [...ms, { id, name }])}
          />
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => { setShowCreate(false); setNewMembers([]) }}>Cancel</Button>
            <Button size="sm" disabled={newMembers.length < 2 || createMutation.isPending} onClick={() => createMutation.mutate()}>
              {createMutation.isPending ? 'Creating…' : 'Create'}
            </Button>
          </div>
        </div>
      )}

      {households.length === 0 && !showCreate && (
        <div className="py-16 text-center">
          <p className="text-sm font-medium mb-1">No households yet</p>
          <p className="text-xs text-muted-foreground">Link family members who often pay together.</p>
        </div>
      )}

      {households.map(hh => (
        <HouseholdCard key={hh.id} household={hh} />
      ))}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

type Tab = 'duplicates' | 'households'

export default function ClientCleanupPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('duplicates')

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'duplicates', label: 'Duplicates', icon: Merge },
    { id: 'households', label: 'Households', icon: Users },
  ]

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate('/clients')}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← Clients
          </button>
          <h1 className="text-xl font-semibold">Client Cleanup</h1>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b mb-6">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                tab === id
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>

        {tab === 'duplicates' && <DuplicatesTab />}
        {tab === 'households' && <HouseholdsTab />}
      </div>
    </div>
  )
}
