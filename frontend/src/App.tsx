import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from '@/store/auth'
import LoginPage from '@/pages/LoginPage'
import AppointmentBookPage from '@/pages/AppointmentBookPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-muted/30" />
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppointmentBookPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
