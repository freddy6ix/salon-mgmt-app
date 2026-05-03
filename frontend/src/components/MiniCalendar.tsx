import { useState, useEffect } from 'react'
import {
  format, parseISO,
  startOfMonth, endOfMonth,
  startOfWeek, endOfWeek,
  addDays, addMonths, subMonths,
  isSameDay, isSameMonth,
} from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const DAY_HEADERS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

interface Props {
  selectedDate: string        // 'yyyy-MM-dd'
  onDateChange: (date: string) => void
}

export default function MiniCalendar({ selectedDate, onDateChange }: Props) {
  const selected = parseISO(selectedDate + 'T12:00:00')
  const today = new Date()

  const [viewMonth, setViewMonth] = useState(() => startOfMonth(selected))

  // Follow the selected date into a new month
  useEffect(() => {
    setViewMonth(startOfMonth(parseISO(selectedDate + 'T12:00:00')))
  }, [selectedDate])

  // Build the 6-week grid
  const gridStart = startOfWeek(startOfMonth(viewMonth), { weekStartsOn: 0 })
  const gridEnd   = endOfWeek(endOfMonth(viewMonth),     { weekStartsOn: 0 })
  const days: Date[] = []
  let cur = gridStart
  while (cur <= gridEnd) {
    days.push(cur)
    cur = addDays(cur, 1)
  }

  return (
    <div className="p-3 select-none">
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={() => setViewMonth(m => subMonths(m, 1))}
          className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronLeft size={13} />
        </button>
        <span className="text-xs font-semibold">{format(viewMonth, 'MMMM yyyy')}</span>
        <button
          onClick={() => setViewMonth(m => addMonths(m, 1))}
          className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronRight size={13} />
        </button>
      </div>

      {/* Day-of-week headers */}
      <div className="grid grid-cols-7 mb-1">
        {DAY_HEADERS.map(d => (
          <div key={d} className="text-center text-[10px] text-muted-foreground/60 font-medium py-0.5">
            {d}
          </div>
        ))}
      </div>

      {/* Day grid */}
      <div className="grid grid-cols-7 gap-y-0.5">
        {days.map((day, i) => {
          const isSelected     = isSameDay(day, selected)
          const isToday        = isSameDay(day, today)
          const isCurrentMonth = isSameMonth(day, viewMonth)

          return (
            <button
              key={i}
              onClick={() => onDateChange(format(day, 'yyyy-MM-dd'))}
              className={[
                'text-[11px] h-6 w-full rounded transition-colors',
                isSelected
                  ? 'bg-primary text-primary-foreground font-semibold'
                  : isToday
                    ? 'text-primary font-semibold hover:bg-muted'
                    : isCurrentMonth
                      ? 'text-foreground hover:bg-muted'
                      : 'text-muted-foreground/30 hover:bg-muted',
              ].join(' ')}
            >
              {format(day, 'd')}
            </button>
          )
        })}
      </div>
    </div>
  )
}
