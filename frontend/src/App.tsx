import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from '@/store/auth'
import AppShell from '@/components/AppShell'
import LandingPage from '@/pages/LandingPage'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import AppointmentBookPage from '@/pages/AppointmentBookPage'
import StaffSchedulePage from '@/pages/StaffSchedulePage'
import MyRequestsPage from '@/pages/MyRequestsPage'
import RequestsPage from '@/pages/RequestsPage'

function StaffShell() {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-muted/30" />
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'guest') return <Navigate to="/my-requests" replace />
  return <AppShell />
}

function RequireGuest({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-muted/30" />
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'guest') return <Navigate to="/" replace />
  return <>{children}</>
}

function Placeholder({ title }: { title: string }) {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold mb-2">{title}</h1>
      <p className="text-muted-foreground">Coming soon.</p>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/my-requests"
        element={
          <RequireGuest>
            <MyRequestsPage />
          </RequireGuest>
        }
      />

      {/* Staff shell — all staff routes nested here */}
      <Route element={<StaffShell />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/appointments" element={<AppointmentBookPage />} />
        <Route path="/requests" element={<RequestsPage />} />
        <Route path="/staff" element={<StaffSchedulePage />} />
        <Route path="/clients" element={<Placeholder title="Clients" />} />
        <Route path="/reports" element={<Placeholder title="Reports" />} />
        <Route path="/settings" element={<Placeholder title="Settings" />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
