import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/store/auth'
import {
  Home, CalendarDays, Users, ClipboardList, Settings, LogOut,
  ShieldCheck, Scissors, Vault, ShoppingBag, DollarSign, UserCog,
  ChevronRight, Receipt, Coins, Upload, ScrollText, User,
} from 'lucide-react'
import { listAllRequests } from '@/api/appointmentRequests'
import { getBranding } from '@/api/settings'
import { applyBranding } from '@/lib/branding'

const NAV_LINK = `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors rounded-none`
const ACTIVE   = `bg-muted text-foreground font-medium`
const INACTIVE = `text-muted-foreground hover:text-foreground hover:bg-muted/50`

function navClass({ isActive }: { isActive: boolean }) {
  return `${NAV_LINK} ${isActive ? ACTIVE : INACTIVE}`
}

function SubNavLink({ to, icon: Icon, label }: { to: string; icon: React.ElementType; label: string }) {
  return (
    <NavLink to={to} className={navClass}>
      <span className="w-4 flex-shrink-0" />
      <Icon size={15} className="flex-shrink-0 text-muted-foreground" />
      <span className="flex-1">{label}</span>
    </NavLink>
  )
}

export default function AppShell() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin'
  const location = useLocation()

  const isAdminRoute = (
    location.pathname.startsWith('/services') ||
    location.pathname.startsWith('/staff') ||
    location.pathname.startsWith('/retail') ||
    location.pathname.startsWith('/till') ||
    location.pathname.startsWith('/reports') ||
    location.pathname.startsWith('/users') ||
    location.pathname.startsWith('/login-log') ||
    location.pathname.startsWith('/settings') ||
    location.pathname.startsWith('/import')
  )
  const isSettingsRoute = location.pathname.startsWith('/settings')

  const [adminOpen, setAdminOpen] = useState(isAdminRoute)

  useEffect(() => { if (isAdminRoute) setAdminOpen(true) }, [isAdminRoute])

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

  const TOP_NAV = [
    { to: '/dashboard',    icon: Home,          label: 'Home',             badge: 0 },
    { to: '/appointments', icon: CalendarDays,  label: 'Appointment Book', badge: 0 },
    { to: '/clients',      icon: Users,         label: 'Clients',          badge: 0 },
    { to: '/requests',     icon: ClipboardList, label: 'Requests',         badge: pendingCount },
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
          {TOP_NAV.map(({ to, icon: Icon, label, badge }) => (
            <NavLink key={to} to={to} className={navClass}>
              <Icon size={16} className="flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {badge > 0 && (
                <span className="ml-auto bg-amber-500 text-white text-xs font-medium rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center leading-none">
                  {badge}
                </span>
              )}
            </NavLink>
          ))}

          {/* Admin group (admin only) */}
          {isAdmin && (
            <>
              <button
                onClick={() => setAdminOpen(o => !o)}
                className={`${NAV_LINK} w-full ${isAdminRoute ? ACTIVE : INACTIVE}`}
              >
                <ShieldCheck size={16} className="flex-shrink-0" />
                <span className="flex-1 text-left">Admin</span>
                <ChevronRight
                  size={14}
                  className={`flex-shrink-0 transition-transform duration-150 ${adminOpen ? 'rotate-90' : ''}`}
                />
              </button>
              {adminOpen && (
                <>
                  <SubNavLink to="/services"          icon={Scissors}    label="Services"    />
                  <SubNavLink to="/staff"             icon={UserCog}     label="Staff"       />
                  <SubNavLink to="/retail"            icon={ShoppingBag} label="Retail"      />
                  <SubNavLink to="/till"              icon={Vault}       label="Till"        />
                  <SubNavLink to="/reports/sales"     icon={Receipt}     label="Sales"       />
                  <SubNavLink to="/reports/payroll"   icon={DollarSign}  label="Payroll"     />
                  <SubNavLink to="/reports/petty-cash" icon={Coins}      label="Petty Cash"  />
                  <SubNavLink to="/users"     icon={User}        label="Users"      />
                  <SubNavLink to="/login-log" icon={ScrollText}  label="Login Log"  />
                  <SubNavLink to="/settings"  icon={Settings}    label="Settings"   />
                  <SubNavLink to="/import"    icon={Upload}      label="Import"     />
                </>
              )}
            </>
          )}

          {/* Settings — direct link for non-admins */}
          {!isAdmin && (
            <NavLink to="/settings" className={navClass}>
              <Settings size={16} className="flex-shrink-0" />
              <span className="flex-1">Settings</span>
            </NavLink>
          )}
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
