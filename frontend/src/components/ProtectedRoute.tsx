import type { JSX } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

export function ProtectedRoute(): JSX.Element {
  const location = useLocation()
  const token = useAuthStore((state) => state.token)

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
