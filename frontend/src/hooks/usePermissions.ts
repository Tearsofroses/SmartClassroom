import { useMemo } from 'react'
import type { PermissionKey } from '../constants/permissions'
import { useAuthStore } from '../store/auth'

export function usePermissions() {
  const permissions = useAuthStore((state) => state.permissions)

  const permissionSet = useMemo(() => new Set(permissions), [permissions])

  const has = (permission: PermissionKey): boolean => permissionSet.has(permission)

  const hasAny = (required: PermissionKey[]): boolean => required.some((perm) => permissionSet.has(perm))

  const hasAll = (required: PermissionKey[]): boolean => required.every((perm) => permissionSet.has(perm))

  return {
    permissions,
    has,
    hasAny,
    hasAll,
  }
}
