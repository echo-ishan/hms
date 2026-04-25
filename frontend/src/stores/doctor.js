import { defineStore } from 'pinia'
import {
  createDoctorAvailability,
  deleteDoctorAvailability,
  getDoctorMe,
  listDoctorAppointments,
  listDoctorAvailability,
  updateDoctorAppointment,
} from '@/api/doctor'

export const useDoctorStore = defineStore('doctor', {
  state: () => ({
    profile: null,
    appointments: [],
    availability: [],
    loadingProfile: false,
    loadingAppointments: false,
    loadingAvailability: false,
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
        const data = await getDoctorMe(token)
        this.profile = data.doctor
        return data.doctor
      } catch (error) {
        this.lastError = error.message || 'Failed to load profile'
        throw error
      } finally {
        this.loadingProfile = false
      }
    },
    async fetchAppointments(params, token) {
      this.loadingAppointments = true
      this.lastError = ''
      try {
        const data = await listDoctorAppointments(params, token)
        this.appointments = data.appointments || []
        return this.appointments
      } catch (error) {
        this.lastError = error.message || 'Failed to load appointments'
        throw error
      } finally {
        this.loadingAppointments = false
      }
    },
    async fetchAvailability(params, token) {
      this.loadingAvailability = true
      this.lastError = ''
      try {
        const data = await listDoctorAvailability(params, token)
        this.availability = data.availability || []
        return this.availability
      } catch (error) {
        this.lastError = error.message || 'Failed to load availability'
        throw error
      } finally {
        this.loadingAvailability = false
      }
    },
    async addAvailability(payload, token) {
      this.lastError = ''
      try {
        await createDoctorAvailability(payload, token)
      } catch (error) {
        this.lastError = error.message || 'Failed to create availability'
        throw error
      }
    },
    async removeAvailability(id, token) {
      this.lastError = ''
      try {
        await deleteDoctorAvailability(id, token)
      } catch (error) {
        this.lastError = error.message || 'Failed to delete availability'
        throw error
      }
    },
    async saveAppointment(id, payload, token) {
      this.lastError = ''
      try {
        const data = await updateDoctorAppointment(id, payload, token)
        return data.appointment
      } catch (error) {
        this.lastError = error.message || 'Failed to update appointment'
        throw error
      }
    },
  },
})
