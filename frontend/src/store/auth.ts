import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'
import type { AuthUser } from '../types'
import type { PermissionKey } from '../constants/permissions'

interface AuthState {
  token: string | null
  user: AuthUser | null
  permissions: PermissionKey[]
  setAuthSession: (token: string, user: AuthUser, permissions?: PermissionKey[]) => void
  setPermissions: (permissions: PermissionKey[]) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      permissions: [],
      setAuthSession: (token, user, permissions = []) => set({ token, user, permissions }),
      setPermissions: (permissions) => set({ permissions }),
      clearAuth: () => set({ token: null, user: null, permissions: [] }),
    }),
    {
      name: 'smart-classroom-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, user: state.user, permissions: state.permissions }),
    },
  ),
)
