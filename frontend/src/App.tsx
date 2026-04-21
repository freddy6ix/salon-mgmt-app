import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from '@/store/auth'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import AppointmentBookPage from '@/pages/AppointmentBookPage'
import StaffSchedulePage from '@/pages/StaffSchedulePage'
import MyRequestsPage from '@/pages/MyRequestsPage'
import RequestsPage from '@/pages/RequestsPage'

function RequireStaff({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-muted/30" />
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'guest') return <Navigate to="/my-requests" replace />
  return <>{children}</>
}

function RequireGuest({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-muted/30" />
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'guest') return <Navigate to="/" replace />
  return <>{children}</>
}

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-muted/30" />
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'guest') return <Navigate to="/my-requests" replace />
  return <AppointmentBookPage />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route path="/" element={<RootRedirect />} />

      <Route
        path="/my-requests"
        element={
          <RequireGuest>
            <MyRequestsPage />
          </RequireGuest>
        }
      />

      <Route
        path="/requests"
        element={
          <RequireStaff>
            <RequestsPage />
          </RequireStaff>
        }
      />

      <Route
        path="/settings/staff"
        element={
          <RequireStaff>
            <StaffSchedulePage />
          </RequireStaff>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
