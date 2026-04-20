import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, addDays, subDays, parseISO } from 'date-fns'
import { listAppointments, type Appointment, type AppointmentItem } from '@/api/appointments'
import { listProviders, type Provider } from '@/api/providers'
import TimeGrid from '@/components/appointment-book/TimeGrid'
import AppointmentDetail from '@/components/appointment-book/AppointmentDetail'
import BookingForm from '@/components/appointment-book/BookingForm'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/store/auth'

export default function AppointmentBookPage() {
  const { logout } = useAuth()
  const [date, setDate] = useState(() => format(new Date(), 'yyyy-MM-dd'))
  const [selected, setSelected] = useState<{ item: AppointmentItem; appt: Appointment } | null>(null)
  const [booking, setBooking] = useState<{ time?: string; providerId?: string } | null>(null)

  const { data: providers = [], isLoading: providersLoading } = useQuery<Provider[]>({
    queryKey: ['providers'],
    queryFn: listProviders,
  })

  const { data: appointments = [], isLoading: apptLoading } = useQuery<Appointment[]>({
    queryKey: ['appointments', date],
    queryFn: () => listAppointments(date),
  })

  const activeProviders = providers.filter((p) => p.has_appointments)
  const displayDate = parseISO(date + 'T12:00:00')

  function prev() { setDate(format(subDays(displayDate, 1), 'yyyy-MM-dd')) }
  function next() { setDate(format(addDays(displayDate, 1), 'yyyy-MM-dd')) }
  function today() { setDate(format(new Date(), 'yyyy-MM-dd')) }

  const isLoading = providersLoading || apptLoading

  return (
    <div className="flex flex-col h-screen bg-muted/30">
      <header className="flex items-center justify-between px-4 py-2 bg-white border-b gap-4 flex-shrink-0">
        <span className="font-semibold text-base">Salon Lyol</span>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={prev}>‹</Button>
          <Button variant="outline" size="sm" onClick={today}>Today</Button>
          <span className="text-sm font-medium w-40 text-center">
            {format(displayDate, 'EEEE, MMM d, yyyy')}
          </span>
          <Button variant="outline" size="sm" onClick={next}>›</Button>
        </div>

        <div className="flex items-center gap-2">
          <Button size="sm" onClick={() => setBooking({})}>+ New</Button>
          <Button variant="ghost" size="sm" onClick={logout}>Sign out</Button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden p-4">
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-96 w-full" />
          </div>
        ) : (
          <TimeGrid
            providers={activeProviders}
            appointments={appointments}
            onItemClick={(item, appt) => setSelected({ item, appt })}
            onSlotClick={(time, providerId) => setBooking({ time, providerId })}
          />
        )}
      </main>

      <AppointmentDetail
        item={selected?.item ?? null}
        appointment={selected?.appt ?? null}
        date={date}
        onClose={() => setSelected(null)}
      />

      <BookingForm
        open={booking !== null}
        date={date}
        initialTime={booking?.time}
        initialProviderId={booking?.providerId}
        providers={activeProviders}
        onClose={() => setBooking(null)}
        onSaved={() => setBooking(null)}
      />
    </div>
  )
}
