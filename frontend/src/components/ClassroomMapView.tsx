import { useMemo } from 'react'

export interface ClassroomMapDevice {
  device_id: string
  device_type: string
  device_index: number
  location_front_back: 'FRONT' | 'BACK'
  location_left_right: 'LEFT' | 'RIGHT'
  status?: string
  room_id?: string
}

interface ClassroomMapViewProps {
  devices: ClassroomMapDevice[]
  onToggle?: (deviceId: string, action: 'ON' | 'OFF', roomId?: string) => void
  disabled?: boolean
  roomCode?: string
}

interface PositionedDevice extends ClassroomMapDevice {
  left: number
  top: number
}

/**
 * Renders a 2D classroom map with positioned devices.
 *
 * Layout:
 *   - Top center: Board
 *   - Left/Right walls: ACs
 *   - Center grid: Lights and Fans arranged in rows
 *   - Left/Right edges: Doors
 */
export function ClassroomMapView({ devices, onToggle, disabled = false, roomCode }: ClassroomMapViewProps): JSX.Element {
  const positioned = useMemo<PositionedDevice[]>(() => {
    const acs = devices.filter((d) => d.device_type === 'AC')
    const lights = devices.filter((d) => d.device_type === 'LIGHT')
    const fans = devices.filter((d) => d.device_type === 'FAN')

    const result: PositionedDevice[] = []

    // Place ACs on the walls (left side and right side, vertically centered)
    acs.forEach((ac, idx) => {
      const isLeft = ac.location_left_right === 'LEFT' || idx % 2 === 0
      result.push({
        ...ac,
        left: isLeft ? 8 : 92,
        top: 65,
      })
    })

    // Place Lights and Fans in a structured grid in the center
    // Grid layout: alternating rows of lights and fans
    // Lights: 3 rows of 2 (or as many as we have)
    // Fans: 2 rows of 2 (between light rows)

    const centerStartTop = 28
    const centerEndTop = 88
    const totalCenterDevices = lights.length + fans.length

    if (totalCenterDevices > 0) {
      // Sort lights and fans by index for consistent layout
      const sortedLights = [...lights].sort((a, b) => a.device_index - b.device_index)
      const sortedFans = [...fans].sort((a, b) => a.device_index - b.device_index)

      // Create rows: alternate lights and fans
      // Pair them: 2 per row (left and right)
      const lightPairs: ClassroomMapDevice[][] = []
      for (let i = 0; i < sortedLights.length; i += 2) {
        lightPairs.push(sortedLights.slice(i, i + 2))
      }

      const fanPairs: ClassroomMapDevice[][] = []
      for (let i = 0; i < sortedFans.length; i += 2) {
        fanPairs.push(sortedFans.slice(i, i + 2))
      }

      // Interleave: light row, fan row, light row, fan row, ...
      const rows: Array<{ type: 'LIGHT' | 'FAN'; pair: ClassroomMapDevice[] }> = []
      const maxRows = Math.max(lightPairs.length, fanPairs.length)
      for (let i = 0; i < maxRows; i++) {
        if (i < lightPairs.length) rows.push({ type: 'LIGHT', pair: lightPairs[i] })
        if (i < fanPairs.length) rows.push({ type: 'FAN', pair: fanPairs[i] })
      }

      const rowCount = rows.length
      const rowSpacing = rowCount > 1 ? (centerEndTop - centerStartTop) / (rowCount - 1) : 0

      rows.forEach((row, rowIdx) => {
        const topPos = rowCount === 1 ? (centerStartTop + centerEndTop) / 2 : centerStartTop + rowIdx * rowSpacing
        row.pair.forEach((device, pairIdx) => {
          const leftPos = pairIdx === 0 ? 35 : 65
          result.push({
            ...device,
            left: leftPos,
            top: topPos,
          })
        })
      })
    }

    // Clamp all positions to safe bounds
    return result.map((d) => ({
      ...d,
      left: Math.max(5, Math.min(95, d.left)),
      top: Math.max(8, Math.min(92, d.top)),
    }))
  }, [devices])

  return (
    <div className="classroom-map-container">
      <div className="classroom-canvas classroom-canvas-enhanced">
        {/* Wiring Overlay */}
        <svg className="classroom-wiring-overlay">
          {positioned.map((device) => (
            <line
              key={`wire-${device.device_id}`}
              x1="50%"
              y1="18%"
              x2={`${device.left}%`}
              y2={`${device.top}%`}
              stroke="#e2e8f0"
              strokeWidth="1"
              strokeDasharray="4 2"
            />
          ))}
        </svg>

        {/* Board at the top */}
        <div className="classroom-board">Board</div>

        {/* Relay */}
        <div className="classroom-fixture classroom-relay" style={{ left: '50%', top: '18%', transform: 'translateX(-50%)' }}>Relay</div>

        {/* Lecturer desk */}
        <div className="classroom-fixture classroom-desk">Lecturer Desk</div>

        {/* Doors */}
        <div className="classroom-fixture classroom-door classroom-door-left">Door</div>
        <div className="classroom-fixture classroom-door classroom-door-right">Door</div>

        {/* Devices */}
        {positioned.map((device) => {
          const isOn = (device.status ?? 'OFF').toUpperCase() === 'ON'
          return (
            <button
              key={device.device_id}
              type="button"
              className={`classroom-device ${isOn ? 'on' : 'off'}`}
              style={{ left: `${device.left}%`, top: `${device.top}%` }}
              onClick={() => {
                if (onToggle) {
                  void onToggle(device.device_id, isOn ? 'OFF' : 'ON', device.room_id)
                }
              }}
              disabled={disabled || !onToggle}
              title={`${device.device_type} ${device.device_index} — ${isOn ? 'ON' : 'OFF'}${roomCode ? ` (${roomCode})` : ''}`}
            >
              <span className="classroom-device-type">{device.device_type} {device.device_index}</span>
              <span className={`classroom-device-status ${isOn ? 'on' : 'off'}`}>{isOn ? 'ON' : 'OFF'}</span>
            </button>
          )
        })}

        {devices.length === 0 && (
          <p className="classroom-empty-label">No devices in this room</p>
        )}
      </div>
    </div>
  )
}
