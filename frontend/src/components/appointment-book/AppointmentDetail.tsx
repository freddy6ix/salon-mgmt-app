import { format } from 'date-fns'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Appointment, AppointmentItem } from '@/api/appointments'
import { updateAppointmentStatus } from '@/api/appointments'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  in_progress: 'default',
  completed: 'outline',
  cancelled: 'destructive',
}

interface Props {
  item: AppointmentItem | null
  appointment: Appointment | null
  date: string
  onClose: () => void
}

export default function AppointmentDetail({ item, appointment, date, onClose }: Props) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (newStatus: Appointment['status']) =>
      updateAppointmentStatus(appointment!.id, newStatus),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointments', date] })
      onClose()
    },
  })

  if (!item || !appointment) return null

  const startTime = new Date(item.start_time)
  const effectiveDuration = item.duration_override_minutes ?? item.duration_minutes
  const endTime = new Date(startTime.getTime() + effectiveDuration * 60000)

  const apptStatus = appointment.status

  return (
    <Dialog open onOpenChange={(isOpen: boolean) => !isOpen && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {appointment.client.first_name} {appointment.client.last_name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {appointment.client.cell_phone && (
            <p className="text-sm text-muted-foreground">{appointment.client.cell_phone}</p>
          )}

          {appointment.client.special_instructions && (
            <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800">
              {appointment.client.special_instructions}
            </div>
          )}

          <Separator />

          <div className="space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-sm">{item.service.name}</p>
                <p className="text-xs text-muted-foreground">
                  {format(startTime, 'h:mm a')} – {format(endTime, 'h:mm a')} · {effectiveDuration} min
                </p>
                <p className="text-xs text-muted-foreground">
                  with {item.provider.display_name}
                  {item.second_provider ? ` & ${item.second_provider.display_name}` : ''}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <Badge variant={STATUS_VARIANT[item.status]}>{item.status.replace('_', ' ')}</Badge>
                <span className="text-sm font-medium">${item.price.toFixed(2)}</span>
              </div>
            </div>

            {item.notes && (
              <p className="text-xs text-muted-foreground italic">{item.notes}</p>
            )}

            {item.service.processing_duration_minutes > 0 && (
              <p className="text-xs text-muted-foreground">
                Processing: {item.service.processing_duration_minutes} min
                (starts at {format(new Date(startTime.getTime() + item.service.processing_offset_minutes * 60000), 'h:mm a')})
              </p>
            )}
          </div>

          {appointment.notes && (
            <>
              <Separator />
              <p className="text-xs text-muted-foreground">{appointment.notes}</p>
            </>
          )}

          {/* ── Action buttons ── */}
          {mutation.isError && (
            <p className="text-xs text-destructive">
              {mutation.error instanceof Error ? mutation.error.message : 'Update failed'}
            </p>
          )}

          {apptStatus === 'confirmed' && (
            <div className="flex gap-2 pt-1">
              <Button
                className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate('in_progress')}
              >
                Client arrived
              </Button>
              <Button
                variant="destructive"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate('cancelled')}
              >
                Cancel
              </Button>
            </div>
          )}

          {apptStatus === 'in_progress' && (
            <div className="flex gap-2 pt-1">
              <Button
                className="flex-1"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate('completed')}
              >
                Check out
              </Button>
              <Button
                variant="destructive"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate('cancelled')}
              >
                Cancel
              </Button>
            </div>
          )}

          {apptStatus === 'completed' && (
            <p className="text-xs text-muted-foreground text-center pt-1">Checked out</p>
          )}

          {apptStatus === 'cancelled' && (
            <p className="text-xs text-destructive text-center pt-1">Cancelled</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
