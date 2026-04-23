import { useEffect } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/store/auth'
import {
  Home, CalendarDays, Users, ClipboardList, UserCog, BarChart2, Settings, LogOut, ShieldCheck,
} from 'lucide-react'
import { listAllRequests } from '@/api/appointmentRequests'
import { getBranding } from '@/api/settings'
import { applyBranding } from '@/lib/branding'

export default function AppShell() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin'

  const { data: pendingRequests = [] } = useQuery({
    queryKey: ['requests', 'new'],
    queryFn: () => listAllRequests('new'),
    refetchInterval: 60_000,
  })
  const pendingCount = pendingRequests.length

  const { data: branding } = useQuery({
    queryKey: ['branding'],
    queryFn: getBranding,
    staleTime: Infinity,
  })

  useEffect(() => {
    if (branding) applyBranding(branding)
  }, [branding])

  const NAV = [
    { to: '/dashboard',    icon: Home,           label: 'Home',             badge: 0 },
    { to: '/appointments', icon: CalendarDays,   label: 'Appointment Book', badge: 0 },
    { to: '/clients',      icon: Users,          label: 'Clients',          badge: 0 },
    { to: '/requests',     icon: ClipboardList,  label: 'Requests',         badge: pendingCount },
    { to: '/staff',        icon: UserCog,        label: 'Staff',            badge: 0 },
    { to: '/reports',      icon: BarChart2,      label: 'Reports',          badge: 0 },
    { to: '/settings',     icon: Settings,       label: 'Settings',         badge: 0 },
    ...(isAdmin ? [{ to: '/users', icon: ShieldCheck, label: 'Users', badge: 0 }] : []),
  ]

  return (
    <div className="flex h-screen bg-muted/30">
      <nav className="w-56 flex-shrink-0 bg-white border-r flex flex-col">
        <div className="flex flex-col items-center py-5 border-b gap-2">
          <img
            src={branding?.logo_url ?? '/salon-lyol-icon.png'}
            alt={branding?.salon_name ?? 'Salon Lyol'}
            className="h-10 w-auto object-contain"
            onError={e => { e.currentTarget.src = '/salon-lyol-icon.png' }}
          />
          <span className="text-xs font-medium tracking-widest uppercase text-muted-foreground">
            {branding?.salon_name ?? 'Salon Lyol'}
          </span>
        </div>

        <div className="flex-1 py-2 overflow-auto">
          {NAV.map(({ to, icon: Icon, label, badge }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors rounded-none
                ${isActive
                  ? 'bg-muted text-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                }`
              }
            >
              <Icon size={16} className="flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {badge > 0 && (
                <span className="ml-auto bg-amber-500 text-white text-xs font-medium rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center leading-none">
                  {badge}
                </span>
              )}
            </NavLink>
          ))}
        </div>

        <div className="border-t p-3">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-2 py-2 text-sm text-muted-foreground hover:text-foreground w-full rounded-md hover:bg-muted/50 transition-colors"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </nav>

      <div className="flex-1 min-w-0 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}
