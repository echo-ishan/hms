import { apiFetch } from './client'

export function getDoctorMe(token) {
  return apiFetch('/api/doctor/me', { token })
}

export function listDoctorAvailability({ date = '' } = {}, token) {
  const params = new URLSearchParams()
  if (date) params.set('date', date)
  const query = params.toString()
  return apiFetch(`/api/doctor/availability${query ? `?${query}` : ''}`, { token })
}

export function createDoctorAvailability(payload, token) {
  return apiFetch('/api/doctor/availability', {
    method: 'POST',
    body: payload,
    token,
  })
}

export function deleteDoctorAvailability(id, token) {
  return apiFetch(`/api/doctor/availability/${id}`, {
    method: 'DELETE',
    token,
  })
}

export function listDoctorAppointments({ status = '', from = '', to = '' } = {}, token) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const query = params.toString()
  return apiFetch(`/api/doctor/appointments${query ? `?${query}` : ''}`, { token })
}

export function updateDoctorAppointment(id, payload, token) {
  return apiFetch(`/api/doctor/appointments/${id}`, {
    method: 'PATCH',
    body: payload,
    token,
  })
}

export function getDoctorPatientHistory(patientId, token) {
  return apiFetch(`/api/doctor/patient-history/${patientId}`, { token })
}
