import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/store/auth'
import {
  CalendarDays, Users, ClipboardList, UserCog, BarChart2, Settings, LogOut,
} from 'lucide-react'

const NAV = [
  { to: '/appointments', icon: CalendarDays, label: 'Appointment Book' },
  { to: '/clients',      icon: Users,          label: 'Clients' },
  { to: '/requests',     icon: ClipboardList,  label: 'Requests' },
  { to: '/staff',        icon: UserCog,         label: 'Staff' },
  { to: '/reports',      icon: BarChart2,       label: 'Reports' },
  { to: '/settings',     icon: Settings,        label: 'Settings' },
]

export default function AppShell() {
  const { logout } = useAuth()
  return (
    <div className="flex h-screen bg-muted/30">
      <nav className="w-56 flex-shrink-0 bg-white border-r flex flex-col">
        <div className="px-4 py-4 border-b">
          <span className="font-semibold text-base">Salon Lyol</span>
        </div>

        <div className="flex-1 py-2 overflow-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
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
              {label}
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
