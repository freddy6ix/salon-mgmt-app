import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { format, addDays, subDays, parseISO } from 'date-fns'
import { listAppointments, type Appointment, type AppointmentItem } from '@/api/appointments'
import { listProviders, type Provider } from '@/api/providers'
import { getSchedule } from '@/api/schedules'
import { getRequest } from '@/api/appointmentRequests'
import { getBranding, type SlotMinutes } from '@/api/settings'
import { listTimeBlocks, type TimeBlock } from '@/api/timeBlocks'
import TimeGrid from '@/components/appointment-book/TimeGrid'
import AppointmentDetail from '@/components/appointment-book/AppointmentDetail'
import BookingForm from '@/components/appointment-book/BookingForm'
import TimeBlockEditDialog from '@/components/appointment-book/TimeBlockEditDialog'
import ClientCard from '@/components/ClientCard'
import ConvertRequestPanel from '@/components/ConvertRequestPanel'
import ConfirmationDialog from '@/components/appointment-book/ConfirmationDialog'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Eye, EyeOff } from 'lucide-react'

export default function AppointmentBookPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const requestId = searchParams.get('request')
  const highlightApptId = searchParams.get('appointment')

  const [date, setDate] = useState(() => searchParams.get('date') ?? format(new Date(), 'yyyy-MM-dd'))
  const [selected, setSelected] = useState<{ item: AppointmentItem; appt: Appointment } | null>(null)
  const [booking, setBooking] = useState<{ time?: string; providerId?: string } | null>(null)
  const [editingBlock, setEditingBlock] = useState<TimeBlock | null>(null)
  const [creatingBlock, setCreatingBlock] = useState<{ time: string; providerId: string } | null>(null)
  const { data: branding } = useQuery({ queryKey: ['branding'], queryFn: getBranding })
  const slotMinutes: SlotMinutes = (branding?.slot_minutes ?? 10) as SlotMinutes
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null)
  const [pendingConfirmation, setPendingConfirmation] = useState<{
    id: string; appointment_date: string; clientEmail: string | null
  } | null>(null)
  const [showCancelled, setShowCancelled] = useState(() =>
    localStorage.getItem('showCancelled') === 'true'
  )

  const { data: convertRequest } = useQuery({
    queryKey: ['request', requestId],
    queryFn: () => getRequest(requestId!),
    enabled: !!requestId,
  })

  // Auto-jump to the requested date when the request loads
  useEffect(() => {
    if (convertRequest) {
      setDate(convertRequest.desired_date)
    }
  }, [convertRequest?.id])

  const { data: providers = [], isLoading: providersLoading } = useQuery<Provider[]>({
    queryKey: ['providers'],
    queryFn: listProviders,
  })

  const { data: appointments = [], isLoading: apptLoading } = useQuery<Appointment[]>({
    queryKey: ['appointments', date],
    queryFn: () => listAppointments(date),
  })

  // Auto-open appointment detail when navigated here with ?appointment=ID
  useEffect(() => {
    if (!highlightApptId || appointments.length === 0) return
    const appt = appointments.find(a => a.id === highlightApptId)
    if (appt && appt.items.length > 0) {
      setSelected({ item: appt.items[0], appt })
      navigate('/appointments', { replace: true })
    }
  }, [highlightApptId, appointments])

  const { data: schedules = [] } = useQuery({
    queryKey: ['schedules', date],
    queryFn: () => getSchedule(date),
  })

  const { data: timeBlocks = [] } = useQuery<TimeBlock[]>({
    queryKey: ['time-blocks', date],
    queryFn: () => listTimeBlocks(date),
  })

  const activeProviders = providers.filter((p) => p.has_appointments)
  const workingProviderIds = new Set(
    schedules.filter((s) => s.is_working).map((s) => s.provider_id)
  )
  // Show working providers only; if no schedule data yet, show all (schedules default to working)
  const visibleProviders = schedules.length === 0
    ? activeProviders
    : activeProviders.filter((p) => workingProviderIds.has(p.id))
  const displayDate = parseISO(date + 'T12:00:00')

  function prev() { setDate(format(subDays(displayDate, 1), 'yyyy-MM-dd')) }
  function next() { setDate(format(addDays(displayDate, 1), 'yyyy-MM-dd')) }
  function today() { setDate(format(new Date(), 'yyyy-MM-dd')) }
  function toggleCancelled() {
    setShowCancelled(v => {
      localStorage.setItem('showCancelled', String(!v))
      return !v
    })
  }

  const displayedAppointments = showCancelled
    ? appointments
    : appointments.filter(a => a.status !== 'cancelled' && a.status !== 'no_show')

  const isLoading = providersLoading || apptLoading

  return (
    <div className="flex flex-col h-full bg-muted/30">
      <header className="flex items-center justify-between px-4 py-2 bg-white border-b gap-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={prev}>‹</Button>
          <Button variant="outline" size="sm" onClick={today}>Today</Button>
          <span className="text-sm font-medium w-40 text-center">
            {format(displayDate, 'EEEE, MMM d, yyyy')}
          </span>
          <Button variant="outline" size="sm" onClick={next}>›</Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={toggleCancelled}
            className={showCancelled ? '' : 'text-muted-foreground'}
            title={showCancelled ? 'Hide cancelled & no-show' : 'Show cancelled & no-show'}
          >
            {showCancelled ? <Eye size={14} /> : <EyeOff size={14} />}
            <span className="ml-1.5">Cancelled</span>
          </Button>
          <Button size="sm" onClick={() => setBooking({})}>+ New</Button>
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
            providers={visibleProviders}
            appointments={displayedAppointments}
            timeBlocks={timeBlocks}
            date={date}
            slotMinutes={slotMinutes}
            providerHours={schedules}
            onItemClick={(item, appt) => setSelected({ item, appt })}
            onNewAppointment={(time, providerId) => setBooking({ time, providerId })}
            onNewBlock={(time, providerId) => setCreatingBlock({ time, providerId })}
            onBlockClick={setEditingBlock}
            onClientClick={setSelectedClientId}
          />
        )}
      </main>

      <AppointmentDetail
        item={selected?.item ?? null}
        appointment={selected ? (appointments.find(a => a.id === selected.appt.id) ?? selected.appt) : null}
        date={date}
        onClose={() => setSelected(null)}
      />

      <BookingForm
        open={booking !== null}
        date={date}
        initialTime={booking?.time}
        initialProviderId={booking?.providerId}
        providers={visibleProviders}
        providerHours={schedules}
        slotMinutes={slotMinutes}
        onClose={() => setBooking(null)}
        onSaved={(appt) => { setBooking(null); setPendingConfirmation(appt) }}
      />

      <TimeBlockEditDialog
        block={editingBlock}
        creating={creatingBlock}
        date={date}
        providers={visibleProviders}
        onClose={() => { setEditingBlock(null); setCreatingBlock(null) }}
      />

      <ClientCard
        clientId={selectedClientId}
        onClose={() => setSelectedClientId(null)}
      />

      {convertRequest && (
        <ConvertRequestPanel
          request={convertRequest}
          date={date}
          onDateChange={setDate}
          onClose={() => navigate('/appointments')}
          onConverted={apptDate => {
            setDate(apptDate)
            navigate('/appointments')
          }}
        />
      )}

      {pendingConfirmation && (
        <ConfirmationDialog
          appointmentId={pendingConfirmation.id}
          appointmentDate={pendingConfirmation.appointment_date}
          open={true}
          recipientEmail={pendingConfirmation.clientEmail}
          onClose={() => setPendingConfirmation(null)}
        />
      )}
    </div>
  )
}
