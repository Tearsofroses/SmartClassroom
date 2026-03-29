import { FormEvent, useMemo, useState } from 'react'
import type { JSX } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { getCurrentPermissions, login } from '../services/auth'
import { useAuthStore } from '../store/auth'

interface LocationState {
  from?: string
}

export function LoginPage(): JSX.Element {
  const navigate = useNavigate()
  const location = useLocation()
  const token = useAuthStore((state) => state.token)
  const setAuthSession = useAuthStore((state) => state.setAuthSession)
  const [username, setUsername] = useState('admin_demo')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const redirectTo = useMemo(() => {
    const state = location.state as LocationState | null
    return state?.from ?? '/'
  }, [location.state])

  if (token) {
    return <Navigate to={redirectTo} replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const response = await login({ username, password })
      setAuthSession(response.access_token, response.user, [])
      const permissions = await getCurrentPermissions()
      setAuthSession(response.access_token, response.user, permissions)
      navigate(redirectTo, { replace: true })
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Login failed'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page auth-page">
      <section className="panel auth-panel">
        <p className="eyebrow">Authentication Required</p>
        <h1>Sign In</h1>
        <p className="subcopy">Use your system account to access classroom dashboards and controls.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </section>
    </main>
  )
}
