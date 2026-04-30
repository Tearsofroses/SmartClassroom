import { useEffect, useState } from 'react'
import { getEffectiveRefreshInterval, getTutorRoomContext } from '../services/api'

interface UseCameraIntervalReturn {
  intervalMs: number | null
  sourceScope: string | null
  buildingId: string | null
  roomId: string | null
  isReady: boolean
  error: string | null
}

export function useCameraInterval(sessionMode: 'NORMAL' | 'TESTING'): UseCameraIntervalReturn {
  const [intervalMs, setIntervalMs] = useState<number | null>(null)
  const [sourceScope, setSourceScope] = useState<string | null>(null)
  const [buildingId, setBuildingId] = useState<string | null>(null)
  const [roomId, setRoomId] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function resolveInterval(): Promise<void> {
      setError(null)
      setIsReady(false)

      try {
        // Step 1: Get room context
        const context = await getTutorRoomContext()
        if (!isMounted) return

        if (!context.building_id || !context.room_id) {
          setError('No assigned room found')
          return
        }

        setBuildingId(context.building_id)
        setRoomId(context.room_id)

        // Step 2: Get effective interval for this mode
        const intervalConfig = await getEffectiveRefreshInterval(
          context.building_id,
          sessionMode,
          context.room_id,
        )
        if (!isMounted) return

        setIntervalMs(intervalConfig.interval_ms)
        setSourceScope(intervalConfig.source_scope)
        setIsReady(true)
      } catch (err) {
        if (!isMounted) return
        setError(err instanceof Error ? err.message : 'Failed to resolve interval')
        setIsReady(false)
      }
    }

    void resolveInterval()

    return () => {
      isMounted = false
    }
  }, [sessionMode])

  return {
    intervalMs,
    sourceScope,
    buildingId,
    roomId,
    isReady,
    error,
  }
}
