import { defineStore } from 'pinia'
import {
  bookPatientAppointment,
  getPatientDoctor,
  getPatientDoctorAvailability,
  getPatientMe,
  listPatientAppointments,
  listPatientDepartments,
  listPatientDoctors,
  updatePatientMe,
  updatePatientAppointment,
} from '@/api/patient'

export const usePatientStore = defineStore('patient', {
  state: () => ({
    profile: null,
    doctors: [],
    departments: [],
    appointments: [],
    loadingProfile: false,
    loadingDoctors: false,
    loadingAppointments: false,
    lastError: '',
  }),
  actions: {
    clearError() {
      this.lastError = ''
    },
    async fetchProfile(token) {
      this.loadingProfile = true
      this.lastError = ''
      try {
        const data = await getPatientMe(token)
        this.profile = data.patient
        return data.patient
      } catch (error) {
        this.lastError = error.message || 'Failed to load patient profile'
        throw error
      } finally {
        this.loadingProfile = false
      }
    },
    async updateProfile(payload, token) {
      this.lastError = ''
      try {
        const data = await updatePatientMe(payload, token)
        this.profile = data.patient
        return data.patient
      } catch (error) {
        this.lastError = error.message || 'Failed to update patient profile'
        throw error
      }
    },
    async fetchDoctors(params = {}) {
      this.loadingDoctors = true
      this.lastError = ''
      try {
        const data = await listPatientDoctors(params)
        this.doctors = data.doctors || []
        return this.doctors
      } catch (error) {
        this.lastError = error.message || 'Failed to load doctors'
        throw error
      } finally {
        this.loadingDoctors = false
      }
    },
    async fetchDepartments() {
      this.lastError = ''
      try {
        const data = await listPatientDepartments()
        this.departments = data.departments || []
        return this.departments
      } catch (error) {
        this.lastError = error.message || 'Failed to load departments'
        throw error
      }
    },
    async fetchDoctorDetails(doctorId) {
      this.lastError = ''
      try {
        const data = await getPatientDoctor(doctorId)
        return data.doctor
      } catch (error) {
        this.lastError = error.message || 'Failed to load doctor profile'
        throw error
      }
    },
    async fetchDoctorAvailability(doctorId, params = {}) {
      this.lastError = ''
      try {
        const data = await getPatientDoctorAvailability(doctorId, params)
        return data.availability || []
      } catch (error) {
        this.lastError = error.message || 'Failed to load doctor availability'
        throw error
      }
    },
    async fetchAppointments(params, token) {
      this.loadingAppointments = true
      this.lastError = ''
      try {
        const data = await listPatientAppointments(params, token)
        this.appointments = data.appointments || []
        return this.appointments
      } catch (error) {
        this.lastError = error.message || 'Failed to load appointments'
        throw error
      } finally {
        this.loadingAppointments = false
      }
    },
    async bookAppointment(payload, token) {
      this.lastError = ''
      try {
        const data = await bookPatientAppointment(payload, token)
        return data.appointment
      } catch (error) {
        this.lastError = error.message || 'Failed to book appointment'
        throw error
      }
    },
    async cancelAppointment(id, token) {
      this.lastError = ''
      try {
        const data = await updatePatientAppointment(id, { status: 'cancelled' }, token)
        return data.appointment
      } catch (error) {
        this.lastError = error.message || 'Failed to cancel appointment'
        throw error
      }
    },
  },
})
