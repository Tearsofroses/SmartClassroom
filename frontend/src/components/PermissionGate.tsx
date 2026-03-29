import type { JSX, ReactNode } from 'react'
import type { PermissionKey } from '../constants/permissions'
import { usePermissions } from '../hooks/usePermissions'

interface PermissionGateProps {
  requires: PermissionKey | PermissionKey[]
  requireAll?: boolean
  fallback?: ReactNode
  children: ReactNode
}

export function PermissionGate({
  requires,
  requireAll = false,
  fallback = null,
  children,
}: PermissionGateProps): JSX.Element {
  const { hasAny, hasAll } = usePermissions()
  const required = Array.isArray(requires) ? requires : [requires]
  const allowed = requireAll ? hasAll(required) : hasAny(required)

  if (!allowed) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
