import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/store/auth'
import {
  Home, CalendarDays, Users, ClipboardList, Settings, LogOut,
  ShieldCheck, Scissors, Vault, ShoppingBag, DollarSign, UserCog,
  ChevronRight, Receipt, Coins, Upload, ScrollText, User,
  PanelLeftClose, PanelLeftOpen,
} from 'lucide-react'
import { format } from 'date-fns'
import { listAllRequests } from '@/api/appointmentRequests'
import { getBranding } from '@/api/settings'
import { applyBranding } from '@/lib/branding'
import MiniCalendar from '@/components/MiniCalendar'

const NAV_LINK = `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors rounded-none`
const ACTIVE   = `bg-muted text-foreground font-medium`
const INACTIVE = `text-muted-foreground hover:text-foreground hover:bg-muted/50`

const ICON_LINK = `flex items-center justify-center py-2.5 transition-colors rounded-none`

function navClass({ isActive }: { isActive: boolean }) {
  return `${NAV_LINK} ${isActive ? ACTIVE : INACTIVE}`
}

function iconNavClass({ isActive }: { isActive: boolean }) {
  return `${ICON_LINK} ${isActive ? ACTIVE : INACTIVE}`
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

function SubNavLabel({ label }: { label: string }) {
  return (
    <div className="px-4 pt-3 pb-0.5">
      <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground/50">{label}</span>
    </div>
  )
}

export default function AppShell() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin'
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [sidebarOpen, setSidebarOpen] = useState(() =>
    localStorage.getItem('sidebarOpen') !== 'false'
  )

  const toggleSidebar = () => setSidebarOpen(v => {
    localStorage.setItem('sidebarOpen', String(!v))
    return !v
  })

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

  const [adminOpen, setAdminOpen] = useState(false)
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

  // Mini calendar date — read from URL if on appointment book, else today
  const isOnAppointments = location.pathname.startsWith('/appointments')
  const calendarDate = isOnAppointments
    ? (searchParams.get('date') ?? format(new Date(), 'yyyy-MM-dd'))
    : format(new Date(), 'yyyy-MM-dd')

  return (
    <div className="flex h-screen bg-muted/30">
      <nav className={`${sidebarOpen ? 'w-56' : 'w-12'} flex-shrink-0 bg-white border-r flex flex-col transition-[width] duration-200`}>

        {/* Logo / header */}
        {sidebarOpen ? (
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
        ) : (
          <div className="flex justify-center py-3 border-b">
            <img
              src={branding?.logo_url ?? '/salon-lyol-icon.png'}
              alt=""
              className="h-6 w-auto object-contain"
              onError={e => { e.currentTarget.src = '/salon-lyol-icon.png' }}
            />
          </div>
        )}

        {/* Nav items */}
        <div className="flex-1 py-2 overflow-auto">
          {sidebarOpen ? (
            <>
              {/* Expanded nav */}
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

              {/* Admin group */}
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
                      <SubNavLabel label="Catalog" />
                      <SubNavLink to="/services" icon={Scissors}    label="Services" />
                      <SubNavLink to="/retail"   icon={ShoppingBag} label="Retail"   />

                      <SubNavLabel label="Staff" />
                      <SubNavLink to="/staff"     icon={UserCog}    label="Staff"     />
                      <SubNavLink to="/users"     icon={User}       label="Users"     />
                      <SubNavLink to="/login-log" icon={ScrollText} label="Login Log" />

                      <SubNavLabel label="Finance" />
                      <SubNavLink to="/till"               icon={Vault}      label="Till"       />
                      <SubNavLink to="/reports/sales"      icon={Receipt}    label="Sales"      />
                      <SubNavLink to="/reports/payroll"    icon={DollarSign} label="Payroll"    />
                      <SubNavLink to="/reports/petty-cash" icon={Coins}      label="Petty Cash" />

                      <SubNavLabel label="Settings" />
                      <SubNavLink to="/settings" icon={Settings} label="Settings" />
                      <SubNavLink to="/import"   icon={Upload}   label="Import"   />
                    </>
                  )}
                </>
              )}

              {/* Settings for non-admins */}
              {!isAdmin && (
                <NavLink to="/settings" className={navClass}>
                  <Settings size={16} className="flex-shrink-0" />
                  <span className="flex-1">Settings</span>
                </NavLink>
              )}
            </>
          ) : (
            <>
              {/* Collapsed — icon-only top nav */}
              {TOP_NAV.map(({ to, icon: Icon, label, badge }) => (
                <NavLink key={to} to={to} className={iconNavClass} title={label}>
                  <div className="relative">
                    <Icon size={18} />
                    {badge > 0 && (
                      <span className="absolute -top-1 -right-1 bg-amber-500 text-white text-[9px] font-bold rounded-full w-3.5 h-3.5 flex items-center justify-center leading-none">
                        {badge}
                      </span>
                    )}
                  </div>
                </NavLink>
              ))}

              {/* Admin icon — click to expand sidebar */}
              {isAdmin && (
                <button
                  onClick={toggleSidebar}
                  title="Admin"
                  className={`${ICON_LINK} w-full ${isAdminRoute ? ACTIVE : INACTIVE}`}
                >
                  <ShieldCheck size={18} />
                </button>
              )}

              {/* Settings icon */}
              {isAdmin ? (
                <button
                  onClick={toggleSidebar}
                  title="Settings"
                  className={`${ICON_LINK} w-full ${location.pathname.startsWith('/settings') ? ACTIVE : INACTIVE}`}
                >
                  <Settings size={18} />
                </button>
              ) : (
                <NavLink to="/settings" className={iconNavClass} title="Settings">
                  <Settings size={18} />
                </NavLink>
              )}
            </>
          )}
        </div>

        {/* Mini calendar — expanded sidebar only */}
        {sidebarOpen && (
          <div className="border-t">
            <MiniCalendar
              selectedDate={calendarDate}
              onDateChange={d => navigate(`/appointments?date=${d}`)}
            />
          </div>
        )}

        {/* Footer — toggle + sign out */}
        <div className="border-t p-2 flex items-center justify-between gap-1">
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? <PanelLeftClose size={15} /> : <PanelLeftOpen size={15} />}
          </button>
          {sidebarOpen && (
            <button
              onClick={logout}
              className="flex items-center gap-2 px-2 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-muted/50 transition-colors"
            >
              <LogOut size={15} />
              Sign out
            </button>
          )}
          {!sidebarOpen && (
            <button
              onClick={logout}
              className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              title="Sign out"
            >
              <LogOut size={15} />
            </button>
          )}
        </div>
      </nav>

      <div className="flex-1 min-w-0 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}
