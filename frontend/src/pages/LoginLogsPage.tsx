import { useQuery } from '@tanstack/react-query'
import { getLoginLogs } from '@/api/admin'

const ROLE_LABEL: Record<string, string> = {
  super_admin: 'Super Admin',
  tenant_admin: 'Admin',
  staff: 'Staff',
  guest: 'Guest',
}

function fmt(iso: string): { date: string; time: string } {
  const d = new Date(iso)
  return {
    date: d.toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' }),
    time: d.toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  }
}

export default function LoginLogsPage() {
  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['login-logs'],
    queryFn: () => getLoginLogs(),
    refetchInterval: 60_000,
  })

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-xl font-semibold mb-1">Login Log</h1>
        <p className="text-sm text-muted-foreground mb-6">
          All successful logins, most recent first. Refreshes every minute.
        </p>

        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading…</div>
        ) : logs.length === 0 ? (
          <div className="text-sm text-muted-foreground">No logins recorded yet.</div>
        ) : (
          <div className="border rounded-lg overflow-hidden bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Date</th>
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Time</th>
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">User</th>
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Role</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((entry, i) => {
                  const { date, time } = fmt(entry.logged_in_at)
                  return (
                    <tr key={entry.id} className={i % 2 === 1 ? 'bg-muted/20' : ''}>
                      <td className="px-4 py-2 tabular-nums">{date}</td>
                      <td className="px-4 py-2 tabular-nums text-muted-foreground">{time}</td>
                      <td className="px-4 py-2">{entry.email}</td>
                      <td className="px-4 py-2 text-muted-foreground">
                        {ROLE_LABEL[entry.role] ?? entry.role}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
