import { apiFetch } from './client'

export function getPatientMe(token) {
  return apiFetch('/api/patient/me', { token })
}

export function updatePatientMe(payload, token) {
  return apiFetch('/api/patient/me', {
    method: 'PATCH',
    body: payload,
    token,
  })
}

export function listPatientDepartments() {
  return apiFetch('/api/patient/departments')
}

export function listPatientDoctors({ q = '', department_id = '' } = {}) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (department_id) params.set('department_id', String(department_id))
  const query = params.toString()
  return apiFetch(`/api/patient/doctors${query ? `?${query}` : ''}`)
}

export function getPatientDoctor(doctorId) {
  return apiFetch(`/api/patient/doctors/${doctorId}`)
}

export function getPatientDoctorAvailability(doctorId, { date = '' } = {}) {
  const params = new URLSearchParams()
  if (date) params.set('date', date)
  const query = params.toString()
  return apiFetch(`/api/patient/doctors/${doctorId}/availability${query ? `?${query}` : ''}`)
}

export function listPatientAppointments({ status = '' } = {}, token) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  const query = params.toString()
  return apiFetch(`/api/patient/appointments${query ? `?${query}` : ''}`, { token })
}

export function bookPatientAppointment(payload, token) {
  return apiFetch('/api/patient/appointments', {
    method: 'POST',
    body: payload,
    token,
  })
}

export function updatePatientAppointment(id, payload, token) {
  return apiFetch(`/api/patient/appointments/${id}`, {
    method: 'PATCH',
    body: payload,
    token,
  })
}

export function requestPatientTreatmentsExport(token) {
  return apiFetch('/api/patient/exports/treatments', {
    method: 'POST',
    token,
  })
}

export function getPatientExportStatus(taskId, token) {
  return apiFetch(`/api/patient/exports/${taskId}`, { token })
}
