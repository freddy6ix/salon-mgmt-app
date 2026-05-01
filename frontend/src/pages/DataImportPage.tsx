import { useRef, useState } from 'react'
import { AlertCircle, CheckCircle2, FileText, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { importLegacyData, type ImportResult } from '@/api/admin'

const FILES = [
  { key: 'clients_csv',          label: 'Client Details',          hint: 'Client Details.txt',            required: true  },
  { key: 'all_bookings_csv',     label: 'Future & Past Bookings',  hint: 'Future and Past Bookings.txt',  required: true  },
  { key: 'receipts_csv',         label: 'Receipt Transactions',    hint: 'Receipt Transactions.txt',      required: true  },
  { key: 'current_bookings_csv', label: 'All Bookings',            hint: 'All Bookings.txt',              required: false },
  { key: 'on_account_csv',       label: 'On Account Summary',      hint: 'On Account Summary.txt',        required: false },
] as const

type FileKey = typeof FILES[number]['key']

const RESULT_LABELS: Record<string, string> = {
  clients:          'Clients',
  receipts:         'Receipt Transactions',
  past_unreceipted: 'Past Unreceipted Bookings',
  future_bookings:  'Future Bookings',
  current_bookings: 'Current Bookings',
  on_account:       'Account Balances',
}

export default function DataImportPage() {
  const [files, setFiles] = useState<Partial<Record<FileKey, File>>>({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRefs = useRef<Partial<Record<FileKey, HTMLInputElement | null>>>({})

  const canRun = FILES.filter(f => f.required).every(f => files[f.key])

  function handleFile(key: FileKey, file: File | null) {
    setFiles(prev => {
      const next = { ...prev }
      if (file) next[key] = file
      else delete next[key]
      return next
    })
    setResult(null)
  }

  async function handleRun() {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const fd = new FormData()
      for (const [key, file] of Object.entries(files)) {
        if (file) fd.append(key, file)
      }
      setResult(await importLegacyData(fd))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-xl mx-auto">
        <h1 className="text-xl font-semibold mb-1">Data Import</h1>
        <p className="text-sm text-muted-foreground mb-6">
          Upload the latest export files from Milano. The import is safe to run repeatedly — existing records are updated, not duplicated.
        </p>

        <div className="space-y-2 mb-6">
          {FILES.map(({ key, label, hint, required }) => {
            const file = files[key]
            return (
              <div key={key} className="flex items-center gap-3 p-3 border rounded-lg bg-white">
                <FileText size={16} className="text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-sm font-medium">{label}</span>
                    {!required && (
                      <span className="text-xs text-muted-foreground">(optional)</span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {file ? file.name : hint}
                  </p>
                </div>
                {file && <CheckCircle2 size={15} className="text-green-500 flex-shrink-0" />}
                <input
                  ref={el => { inputRefs.current[key] = el }}
                  type="file"
                  accept=".txt,.csv"
                  className="hidden"
                  onChange={e => handleFile(key, e.target.files?.[0] ?? null)}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => inputRefs.current[key]?.click()}
                >
                  {file ? 'Change' : 'Browse'}
                </Button>
              </div>
            )
          })}
        </div>

        <Button
          onClick={handleRun}
          disabled={!canRun || loading}
          className="w-full gap-2"
        >
          <Upload size={15} />
          {loading ? 'Importing…' : 'Run Import'}
        </Button>

        {error && (
          <div className="mt-4 flex items-start gap-2 text-destructive text-sm">
            <AlertCircle size={15} className="flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {result && <ImportResults result={result} />}
      </div>
    </div>
  )
}

function ImportResults({ result }: { result: ImportResult }) {
  const entries = Object.entries(result).filter(([k]) => k !== 'error')

  return (
    <div className="mt-6">
      <h2 className="text-sm font-semibold mb-3">Import Results</h2>

      {result.error && (
        <div className="mb-3 text-sm text-destructive bg-destructive/10 rounded-lg p-3">
          <pre className="whitespace-pre-wrap font-mono text-xs">{result.error}</pre>
        </div>
      )}

      <div className="space-y-2">
        {entries.map(([key, data]) => (
          <div key={key} className="border rounded-lg p-3 bg-white">
            <div className="text-sm font-medium mb-1.5">
              {RESULT_LABELS[key] ?? key}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              {Object.entries(data as Record<string, unknown>).map(([k, v]) => (
                Array.isArray(v) ? (
                  v.length > 0 && (
                    <span key={k} className="text-xs text-muted-foreground w-full">
                      {k.replace(/_/g, ' ')}:{' '}
                      <span className="text-foreground font-medium">{v.join(', ')}</span>
                    </span>
                  )
                ) : (
                  <span key={k} className="text-xs text-muted-foreground">
                    {k.replace(/_/g, ' ')}:{' '}
                    <span className="text-foreground font-medium">{String(v)}</span>
                  </span>
                )
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
