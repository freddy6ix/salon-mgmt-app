import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getSchedule, setWorkingStatus } from '@/api/schedules'
import { buttonVariants } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

interface Props {
  date: string
}

export default function WhoIsWorking({ date }: Props) {
  const qc = useQueryClient()

  const { data: statuses = [] } = useQuery({
    queryKey: ['schedules', date],
    queryFn: () => getSchedule(date),
  })

  const toggle = useMutation({
    mutationFn: ({ provider_id, is_working }: { provider_id: string; is_working: boolean }) =>
      setWorkingStatus(provider_id, date, is_working),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedules', date] })
    },
  })

  const workingCount = statuses.filter((s) => s.is_working).length

  return (
    <Popover>
      <PopoverTrigger className={buttonVariants({ variant: 'outline', size: 'sm' })}>
        Staff ({workingCount}/{statuses.length})
      </PopoverTrigger>
      <PopoverContent className="w-52 p-2" align="end">
        <p className="text-xs font-medium text-muted-foreground mb-2 px-1">Who's working today</p>
        <div className="space-y-1">
          {statuses.map((s) => (
            <button
              key={s.provider_id}
              onClick={() => toggle.mutate({ provider_id: s.provider_id, is_working: !s.is_working })}
              className={`w-full flex items-center justify-between px-2 py-1.5 rounded-md text-sm transition-colors ${
                s.is_working
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              <span>{s.display_name}</span>
              <span className="text-xs opacity-70">{s.is_working ? 'In' : 'Off'}</span>
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
