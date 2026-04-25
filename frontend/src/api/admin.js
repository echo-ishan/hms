import { apiFetch } from './client'

export function getAdminStats(token) {
  return apiFetch('/api/admin/stats', { token })
}

export function listAdminAppointments({ status = '', limit = '', q = '' } = {}, token) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (limit !== '' && limit !== null && limit !== undefined) params.set('limit', String(limit))
  if (q) params.set('q', q)
  const query = params.toString()
  return apiFetch(`/api/admin/appointments${query ? `?${query}` : ''}`, { token })
}

export function cancelAdminAppointment(id, token) {
  return apiFetch(`/api/admin/appointments/${id}`, {
    method: 'PATCH',
    body: { status: 'cancelled' },
    token,
  })
}

export function listDepartments(token) {
  return apiFetch('/api/admin/departments', { token })
}

export function createDepartment(payload, token) {
  return apiFetch('/api/admin/departments', {
    method: 'POST',
    body: payload,
    token,
  })
}

export function listDoctors({ q = '', department_id = '' } = {}, token) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (department_id) params.set('department_id', String(department_id))
  const query = params.toString()
  return apiFetch(`/api/admin/doctors${query ? `?${query}` : ''}`, { token })
}

export function createDoctor(payload, token) {
  return apiFetch('/api/admin/doctors', {
    method: 'POST',
    body: payload,
    token,
  })
}

export function updateDoctor(id, payload, token) {
  return apiFetch(`/api/admin/doctors/${id}`, {
    method: 'PATCH',
    body: payload,
    token,
  })
}

export function deleteDoctor(id, token) {
  return apiFetch(`/api/admin/doctors/${id}`, {
    method: 'DELETE',
    token,
  })
}

export function listPatients({ q = '' } = {}, token) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  const query = params.toString()
  return apiFetch(`/api/admin/patients${query ? `?${query}` : ''}`, { token })
}

export function createPatient(payload, token) {
  return apiFetch('/api/admin/patients', {
    method: 'POST',
    body: payload,
    token,
  })
}

export function updatePatient(id, payload, token) {
  return apiFetch(`/api/admin/patients/${id}`, {
    method: 'PATCH',
    body: payload,
    token,
  })
}

export function deletePatient(id, token) {
  return apiFetch(`/api/admin/patients/${id}`, {
    method: 'DELETE',
    token,
  })
}
