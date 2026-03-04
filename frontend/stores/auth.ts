import { defineStore } from 'pinia'
import type { User } from '~/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: null as string | null,
  }),
  actions: {
    async login(token: string) {
      this.token = token
      if (process.client) localStorage.setItem('token', token)
      await this.fetchUser()
    },
    logout() {
      this.user = null
      this.token = null
      if (process.client) localStorage.removeItem('token')
      navigateTo('/login')
    },
    async fetchUser() {
      try {
        const config = useRuntimeConfig()
        const token = this.token || (process.client ? localStorage.getItem('token') : null)
        if (!token) return
        const res = await fetch(`${config.public.apiBase}/api/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          this.user = await res.json()
          this.token = token
        } else {
          this.logout()
        }
      } catch {
        this.logout()
      }
    },
  },
})
