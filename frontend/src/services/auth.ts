import { AxiosError } from 'axios'
import { api } from './api'
import type { AuthLoginRequest, AuthTokenResponse, AuthUser } from '../types'
import type { PermissionKey } from '../constants/permissions'

function normalizeAuthError(error: unknown): Error {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    return new Error(detail ?? error.message)
  }

  return error instanceof Error ? error : new Error('Authentication request failed')
}

export async function login(payload: AuthLoginRequest): Promise<AuthTokenResponse> {
  try {
    const { data } = await api.post<AuthTokenResponse>('/auth/login', payload)
    return data
  } catch (error) {
    throw normalizeAuthError(error)
  }
}

export async function getCurrentUser(): Promise<AuthUser> {
  try {
    const { data } = await api.get<AuthUser>('/auth/me')
    return data
  } catch (error) {
    throw normalizeAuthError(error)
  }
}

export async function getCurrentPermissions(): Promise<PermissionKey[]> {
  try {
    const { data } = await api.get<{ role: string; permissions: PermissionKey[] }>('/auth/permissions')
    return data.permissions
  } catch (error) {
    throw normalizeAuthError(error)
  }
}

export async function refreshToken(): Promise<AuthTokenResponse> {
  try {
    const { data } = await api.post<AuthTokenResponse>('/auth/refresh')
    return data
  } catch (error) {
    throw normalizeAuthError(error)
  }
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout')
  } catch {
    // Ignore logout failures and let client-side auth state clear.
  }
}
