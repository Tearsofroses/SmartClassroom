import { useEffect, useMemo, useState } from 'react'
import type { JSX } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  getStudentAttendanceSummary,
  getStudentWeeklySessions,
} from '../services/api'
import type {
  AttendanceStatus,
  StudentAttendanceSummary,
  StudentSessionCalendarItem,
} from '../types'

const MINUTES_START = 7 * 60
const MINUTES_END = 22 * 60
const TOTAL_MINUTES = MINUTES_END - MINUTES_START

function getWeekStart(base: Date): Date {
  const copy = new Date(base)
  const day = (copy.getDay() + 6) % 7
  copy.setHours(0, 0, 0, 0)
  copy.setDate(copy.getDate() - day)
  return copy
}

function formatWeekRange(weekStart: Date): string {
  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekEnd.getDate() + 6)
  return `${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}`
}

function formatTimeLabel(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function getAttendanceClass(status: AttendanceStatus): string {
  if (status === 'PRESENT') return 'attendance-badge present'
  if (status === 'LATE') return 'attendance-badge late'
  return 'attendance-badge absent'
}

function getSessionBlockStyle(session: StudentSessionCalendarItem): { top: string; height: string } {
  const startDate = new Date(session.start_time)
  const endDate = session.end_time ? new Date(session.end_time) : new Date(startDate.getTime() + 60 * 60 * 1000)

  const startMinutes = startDate.getHours() * 60 + startDate.getMinutes()
  const endMinutes = endDate.getHours() * 60 + endDate.getMinutes()

  const clampedStart = Math.max(MINUTES_START, Math.min(startMinutes, MINUTES_END - 30))
  const clampedEnd = Math.max(clampedStart + 30, Math.min(endMinutes, MINUTES_END))

  const top = ((clampedStart - MINUTES_START) / TOTAL_MINUTES) * 100
  const height = ((clampedEnd - clampedStart) / TOTAL_MINUTES) * 100

  return {
    top: `${top}%`,
    height: `${Math.max(height, 6)}%`,
  }
}

export function StudentDashboardPage(): JSX.Element {
  const navigate = useNavigate()
  const [weekStart, setWeekStart] = useState<Date>(() => getWeekStart(new Date()))
  const [sessions, setSessions] = useState<StudentSessionCalendarItem[]>([])
  const [summary, setSummary] = useState<StudentAttendanceSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function load(): Promise<void> {
      try {
        setError(null)
        const weekStartIso = weekStart.toISOString()
        const [sessionData, summaryData] = await Promise.all([
          getStudentWeeklySessions(weekStartIso),
          getStudentAttendanceSummary(30),
        ])

        if (!isMounted) return

        setSessions(sessionData)
        setSummary(summaryData)
      } catch (loadError) {
        if (!isMounted) return
        setError(loadError instanceof Error ? loadError.message : 'Failed to load student dashboard')
      }
    }

    void load()

    return () => {
      isMounted = false
    }
  }, [weekStart])

  const sessionsByDay = useMemo(() => {
    const map = new Map<number, StudentSessionCalendarItem[]>()
    for (let i = 0; i < 7; i += 1) {
      map.set(i, [])
    }

    sessions.forEach((session) => {
      const day = new Date(session.start_time)
      const mondayIndex = (day.getDay() + 6) % 7
      const bucket = map.get(mondayIndex)
      if (bucket) {
        bucket.push(session)
      }
    })

    for (const daySessions of map.values()) {
      daySessions.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    }

    return map
  }, [sessions])

  const dayHeaders = useMemo(() => {
    const labels: string[] = []
    for (let i = 0; i < 7; i += 1) {
      const date = new Date(weekStart)
      date.setDate(weekStart.getDate() + i)
      labels.push(`${date.toLocaleDateString([], { weekday: 'short' })} ${date.getDate()}`)
    }
    return labels
  }, [weekStart])

  function goToPreviousWeek(): void {
    const next = new Date(weekStart)
    next.setDate(weekStart.getDate() - 7)
    setWeekStart(next)
  }

  function goToNextWeek(): void {
    const next = new Date(weekStart)
    next.setDate(weekStart.getDate() + 7)
    setWeekStart(next)
  }

  function goToCurrentWeek(): void {
    setWeekStart(getWeekStart(new Date()))
  }

  return (
    <main className="page campus-bg student-dashboard-page">
      <section className="panel student-dashboard-header">
        <p className="eyebrow">Student Stakeholder</p>
        <h1>My Weekly Schedule</h1>
        <p className="subcopy">
          Calendar view of your enrolled sessions. Click any session block to review attendance, behavior in class,
          and risk incidents.
        </p>

        <div className="student-kpi-header">
          <article className="student-stat-tile">
            <strong>{summary?.present ?? 0}</strong>
            <p>Present (30 days)</p>
          </article>
          <article className="student-stat-tile">
            <strong>{summary?.late ?? 0}</strong>
            <p>Late (30 days)</p>
          </article>
          <article className="student-stat-tile">
            <strong>{summary?.absent ?? 0}</strong>
            <p>Absent (30 days)</p>
          </article>
          <article className="student-stat-tile">
            <strong>{summary?.total_sessions ?? sessions.length}</strong>
            <p>Total Sessions</p>
          </article>
        </div>

        <div className="week-picker">
          <button type="button" onClick={goToPreviousWeek}>Prev</button>
          <strong className="active-week">{formatWeekRange(weekStart)}</strong>
          <button type="button" onClick={goToNextWeek}>Next</button>
          <button type="button" onClick={goToCurrentWeek}>Today</button>
        </div>

        {error ? <div className="error-panel">{error}</div> : null}
      </section>

      <section className="student-dashboard-layout-full">
        <article className="panel">
          <div className="schedule-grid">
            <div className="schedule-time-axis">
              {Array.from({ length: 16 }).map((_, index) => {
                const hour = 7 + index
                return (
                  <div key={hour} className="schedule-time-mark">
                    {`${hour.toString().padStart(2, '0')}:00`}
                  </div>
                )
              })}
            </div>

            <div className="schedule-week-columns">
              {dayHeaders.map((header, index) => (
                <div key={header} className="schedule-day-column-wrap">
                  <header className="schedule-day-header">{header}</header>
                  <div className="schedule-day-column">
                    {Array.from({ length: 16 }).map((_, slot) => (
                      <div key={`${header}-${slot}`} className="schedule-slot" />
                    ))}

                    {(sessionsByDay.get(index) ?? []).map((session) => {
                      const style = getSessionBlockStyle(session)
                      return (
                        <button
                          key={session.session_id}
                          type="button"
                          className="schedule-block"
                          style={style}
                          onClick={() => navigate(`/students/me/sessions/${session.session_id}`)}
                        >
                          <p className="schedule-block-title">{session.subject_code ?? session.subject_name ?? 'Session'}</p>
                          <p className="schedule-block-time">
                            {formatTimeLabel(session.start_time)} - {formatTimeLabel(session.end_time ?? session.start_time)}
                          </p>
                          <p className="schedule-block-room">{session.room_code ?? 'Room N/A'}</p>
                          <span className={getAttendanceClass(session.attendance_status)}>{session.attendance_status}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </article>
      </section>
    </main>
  )
}
