import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import { listAppointments } from '@/api/appointments'
import { listAllRequests } from '@/api/appointmentRequests'
import { Button } from '@/components/ui/button'
import { CalendarDays, ClipboardList } from 'lucide-react'

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const today = format(new Date(), 'yyyy-MM-dd')

  const { data: appointments = [] } = useQuery({
    queryKey: ['appointments', today],
    queryFn: () => listAppointments(today),
  })

  const { data: pendingRequests = [] } = useQuery({
    queryKey: ['requests', 'new'],
    queryFn: () => listAllRequests('new'),
  })

  const itemCount = appointments.reduce((n, a) => n + a.items.length, 0)

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-2xl font-semibold mb-1">{greeting()}</h1>
      <p className="text-muted-foreground mb-8">{format(new Date(), 'EEEE, MMMM d, yyyy')}</p>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <button
          onClick={() => navigate('/appointments')}
          className="border rounded-lg p-5 bg-white text-left hover:border-foreground/30 transition-colors"
        >
          <div className="flex items-center gap-2 text-muted-foreground text-sm mb-3">
            <CalendarDays size={15} />
            Today's appointments
          </div>
          <p className="text-3xl font-semibold">{itemCount}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {appointments.length} {appointments.length === 1 ? 'visit' : 'visits'} booked
          </p>
        </button>

        <button
          onClick={() => navigate('/requests')}
          className={`border rounded-lg p-5 text-left hover:border-foreground/30 transition-colors
            ${pendingRequests.length > 0 ? 'bg-amber-50 border-amber-300' : 'bg-white'}`}
        >
          <div className="flex items-center gap-2 text-muted-foreground text-sm mb-3">
            <ClipboardList size={15} />
            Pending requests
          </div>
          <p className="text-3xl font-semibold">{pendingRequests.length}</p>
          <p className="text-xs text-muted-foreground mt-1">awaiting review</p>
        </button>
      </div>

      <div className="flex gap-3">
        <Button onClick={() => navigate('/appointments')}>Open appointment book</Button>
        {pendingRequests.length > 0 && (
          <Button variant="outline" onClick={() => navigate('/requests')}>
            Review {pendingRequests.length} {pendingRequests.length === 1 ? 'request' : 'requests'}
          </Button>
        )}
      </div>
    </div>
  )
}
