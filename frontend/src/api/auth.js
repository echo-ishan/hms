import { apiFetch } from './client'

export function login(payload) {
  return apiFetch('/api/auth/login', {
    method: 'POST',
    body: payload,
  })
}

export function registerPatient(payload) {
  return apiFetch('/api/auth/register', {
    method: 'POST',
    body: payload,
  })
}

export function logout() {
  return apiFetch('/api/auth/logout', {
    method: 'POST',
  })
}

export function getMe(token) {
  return apiFetch('/api/auth/me', { token })
}