import { defineStore } from 'pinia'
import { getMe, login, logout, registerPatient } from '@/api/auth'

const TOKEN_KEY = 'hms_access_token'
const ROLE_KEY = 'hms_user_role'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem(TOKEN_KEY) || '',
    isBootstrapped: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
    isAdmin: (state) => state.user?.type === 'admin' || localStorage.getItem(ROLE_KEY) === 'admin',
    isDoctor: (state) => state.user?.type === 'doctor' || localStorage.getItem(ROLE_KEY) === 'doctor',
    isPatient: (state) => state.user?.type === 'patient' || localStorage.getItem(ROLE_KEY) === 'patient',
  },
  actions: {
    clearSession() {
      this.setAccessToken('')
      this.setUser(null)
    },
    setAccessToken(token) {
      this.accessToken = token || ''
      if (this.accessToken) {
        localStorage.setItem(TOKEN_KEY, this.accessToken)
      } else {
        localStorage.removeItem(TOKEN_KEY)
      }
    },
    setUser(user) {
      this.user = user || null
      if (user?.type) {
        localStorage.setItem(ROLE_KEY, user.type)
      } else {
        localStorage.removeItem(ROLE_KEY)
      }
    },
    async bootstrap() {
      if (!this.accessToken) {
        this.isBootstrapped = true
        return
      }

      try {
        const data = await getMe(this.accessToken)
        this.setUser(data.user)
      } catch {
        this.clearSession()
      } finally {
        this.isBootstrapped = true
      }
    },
    async login(credentials) {
      const data = await login(credentials)
      this.setAccessToken(data.access_token)
      this.setUser(data.user)
      this.isBootstrapped = true
      return data.user
    },
    async register(payload) {
      return registerPatient(payload)
    },
    async logout() {
      try {
        await logout()
      } finally {
        this.clearSession()
      }
    },
  },
})
