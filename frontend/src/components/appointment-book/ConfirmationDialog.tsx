import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  getConfirmation,
  saveConfirmationDraft,
  sendConfirmation,
  skipConfirmation,
  type Confirmation,
} from '@/api/appointments'
import RichTextEditor from '@/components/RichTextEditor'

interface Props {
  appointmentId: string
  appointmentDate: string
  open: boolean
  recipientEmail: string | null
  onClose: () => void
}

export default function ConfirmationDialog({
  appointmentId,
  appointmentDate,
  open,
  recipientEmail,
  onClose,
}: Props) {
  const qc = useQueryClient()
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: confirmation, isLoading } = useQuery({
    queryKey: ['confirmation', appointmentId],
    queryFn: () => getConfirmation(appointmentId),
    enabled: open,
  })

  // Reset local form state when the dialog reopens or fresh data loads.
  useEffect(() => {
    if (open && confirmation) {
      setSubject(confirmation.subject)
      setBody(confirmation.body)
      setDirty(false)
      setError(null)
    }
  }, [open, confirmation])

  const isSent = confirmation?.status === 'sent'
  const readOnly = isSent

  const onMutationDone = (updated: Confirmation) => {
    qc.setQueryData(['confirmation', appointmentId], updated)
    qc.invalidateQueries({ queryKey: ['appointments'] })
    setDirty(false)
    setError(null)
  }

  const saveMutation = useMutation({
    mutationFn: () => saveConfirmationDraft(appointmentId, subject, body),
    onSuccess: onMutationDone,
    onError: (e: Error) => setError(e.message || 'Save failed'),
  })

  const sendMutation = useMutation({
    mutationFn: () => sendConfirmation(appointmentId, { subject, body }),
    onSuccess: (updated) => { onMutationDone(updated); onClose() },
    onError: (e: Error) => setError(e.message || 'Send failed'),
  })

  const skipMutation = useMutation({
    mutationFn: () => skipConfirmation(appointmentId),
    onSuccess: (updated) => { onMutationDone(updated); onClose() },
    onError: (e: Error) => setError(e.message || 'Skip failed'),
  })

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Confirmation email</DialogTitle>
          <DialogDescription>
            {isSent ? (
              <>
                Sent {confirmation?.sent_at && new Date(confirmation.sent_at).toLocaleString()}
                {recipientEmail && <> to <strong>{recipientEmail}</strong></>}
              </>
            ) : (
              <>
                {recipientEmail
                  ? <>Will be sent to <strong>{recipientEmail}</strong> for the {new Date(appointmentDate).toLocaleDateString()} appointment.</>
                  : <span className="text-destructive">Client has no email address — cannot send.</span>}
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <p className="text-sm text-muted-foreground py-8 text-center">Loading…</p>
        ) : (
          <>
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Subject</label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => { setSubject(e.target.value); setDirty(true) }}
                  disabled={readOnly}
                  className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background disabled:opacity-60"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">
                  {readOnly ? 'Body' : 'Body'}
                </label>
                <RichTextEditor
                  value={body}
                  onChange={(html) => { setBody(html); setDirty(true) }}
                  disabled={readOnly}
                />
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t">
              <Button
                variant="ghost"
                onClick={onClose}
                disabled={sendMutation.isPending || saveMutation.isPending || skipMutation.isPending}
              >
                {readOnly ? 'Close' : 'Cancel'}
              </Button>

              {!readOnly && (
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => skipMutation.mutate()}
                    disabled={skipMutation.isPending || sendMutation.isPending || saveMutation.isPending}
                    title="Mark this confirmation as skipped (you can change your mind later)"
                  >
                    {skipMutation.isPending ? 'Skipping…' : 'Skip'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => saveMutation.mutate()}
                    disabled={!dirty || saveMutation.isPending || sendMutation.isPending}
                  >
                    {saveMutation.isPending ? 'Saving…' : 'Save draft'}
                  </Button>
                  <Button
                    onClick={() => sendMutation.mutate()}
                    disabled={!recipientEmail || sendMutation.isPending || saveMutation.isPending}
                  >
                    {sendMutation.isPending ? 'Sending…' : 'Send'}
                  </Button>
                </div>
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
