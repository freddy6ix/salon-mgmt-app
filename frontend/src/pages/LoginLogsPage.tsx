import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { getLoginLogs } from '@/api/admin'
import { useTimeFormat } from '@/lib/timeFormat'

export default function LoginLogsPage() {
  const { t } = useTranslation()
  const ROLE_LABEL: Record<string, string> = {
    super_admin: t('users.role_super_admin'),
    tenant_admin: t('users.role_admin_label'),
    staff: t('users.role_staff_label'),
    guest: t('users.role_guest'),
  }

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['login-logs'],
    queryFn: () => getLoginLogs(),
    refetchInterval: 60_000,
  })
  const { formatTime } = useTimeFormat()

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-xl font-semibold mb-1">{t('login_log.page_title')}</h1>
        <p className="text-sm text-muted-foreground mb-6">
          {t('login_log.page_subtitle')}
        </p>

        {isLoading ? (
          <div className="text-sm text-muted-foreground">{t('common.loading')}</div>
        ) : logs.length === 0 ? (
          <div className="text-sm text-muted-foreground">{t('login_log.no_logins')}</div>
        ) : (
          <div className="border rounded-lg overflow-hidden bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">{t('login_log.col_date')}</th>
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">{t('login_log.col_time')}</th>
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">{t('login_log.col_user')}</th>
                  <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">{t('login_log.col_role')}</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((entry, i) => {
                  const d = new Date(entry.logged_in_at)
                  const date = d.toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' })
                  return (
                    <tr key={entry.id} className={i % 2 === 1 ? 'bg-muted/20' : ''}>
                      <td className="px-4 py-2 tabular-nums">{date}</td>
                      <td className="px-4 py-2 tabular-nums text-muted-foreground">{formatTime(d)}</td>
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
