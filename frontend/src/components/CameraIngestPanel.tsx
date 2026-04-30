import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { Camera, CameraOff, AlertCircle } from 'lucide-react'

type CameraState = 'IDLE' | 'STARTING' | 'RUNNING' | 'STOPPING' | 'ERROR'

export interface CameraIngestPanelHandle {
  startCamera: () => Promise<void>
  stopCamera: () => void
  captureFrame: () => string | null
  getState: () => CameraState
}

interface CameraIngestPanelProps {
  onCapture?: (dataUri: string) => void
  onStateChange?: (state: CameraState) => void
}

export const CameraIngestPanel = forwardRef<CameraIngestPanelHandle, CameraIngestPanelProps>(
  function CameraIngestPanel({ onCapture, onStateChange }: CameraIngestPanelProps, ref): JSX.Element {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [state, setState] = useState<CameraState>('IDLE')
  const [error, setError] = useState<string | null>(null)

  const updateState = (newState: CameraState) => {
    setState(newState)
    onStateChange?.(newState)
  }

  const startCamera = async (): Promise<void> => {
    if (state !== 'IDLE') return

    updateState('STARTING')
    setError(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      })

      streamRef.current = stream

      const videoElement = videoRef.current
      if (videoElement) {
        videoElement.srcObject = stream
        // Wait for video to load
        await new Promise<void>((resolve) => {
          const handler = () => {
            videoElement.removeEventListener('loadedmetadata', handler)
            resolve()
          }
          videoElement.addEventListener('loadedmetadata', handler)
        })
      }

      updateState('RUNNING')
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : 'Failed to access camera. Check permissions.'
      setError(errorMsg)
      updateState('ERROR')
    }
  }

  const stopCamera = (): void => {
    if (state !== 'RUNNING') return

    updateState('STOPPING')

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null
    }

    updateState('IDLE')
  }

  const captureFrame = (): string | null => {
    if (!videoRef.current || !canvasRef.current || state !== 'RUNNING') {
      return null
    }

    const ctx = canvasRef.current.getContext('2d')
    if (!ctx) return null

    // Match canvas size to video dimensions
    canvasRef.current.width = videoRef.current.videoWidth
    canvasRef.current.height = videoRef.current.videoHeight

    // Draw video frame to canvas
    ctx.drawImage(videoRef.current, 0, 0)

    // Convert to JPEG data URI (70% quality for smaller payload)
    try {
      const dataUri = canvasRef.current.toDataURL('image/jpeg', 0.7)
      onCapture?.(dataUri)
      return dataUri
    } catch {
      return null
    }
  }

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  useImperativeHandle(
    ref,
    () => ({
      startCamera,
      stopCamera,
      captureFrame,
      getState: () => state,
    }),
    [state],
  )

  return (
    <div className="camera-panel">
      <div className="camera-header">
        {state === 'RUNNING' ? <Camera size={18} /> : <CameraOff size={18} />}
        <span className="camera-status">{state}</span>
      </div>

      {error && (
        <div className="camera-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="camera-feed-wrapper">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="camera-feed"
          style={{
            display: state === 'RUNNING' ? 'block' : 'none',
            width: '100%',
            backgroundColor: '#000',
            borderRadius: '8px',
          }}
        />
        {state !== 'RUNNING' && (
          <div
            className="camera-placeholder"
            style={{
              width: '100%',
              aspectRatio: '16/9',
              backgroundColor: '#1a1a1a',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CameraOff size={48} color="#666" />
          </div>
        )}
      </div>

      <div className="camera-controls">
        {state === 'IDLE' || state === 'ERROR' ? (
          <button className="btn btn-primary" onClick={startCamera}>
            Start Camera
          </button>
        ) : state === 'RUNNING' ? (
          <button className="btn btn-danger" onClick={stopCamera}>
            Stop Camera
          </button>
        ) : (
          <button className="btn" disabled>
            {state}...
          </button>
        )}
      </div>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  )
  },
)

export { type CameraState, type CameraIngestPanelProps }
