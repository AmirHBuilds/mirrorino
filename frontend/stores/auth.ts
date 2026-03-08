import { defineStore } from 'pinia'
import type { User } from '~/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: null as string | null,
    hydrated: false,
  }),
  actions: {
    hydrateToken() {
      const tokenCookie = useCookie<string | null>('token')
      const token = tokenCookie.value || (process.client ? localStorage.getItem('token') : null)
      this.token = token || null
      if (token) {
        tokenCookie.value = token
        if (process.client) localStorage.setItem('token', token)
      }
      this.hydrated = true
    },
    async login(token: string) {
      this.token = token
      useCookie<string | null>('token').value = token
      if (process.client) localStorage.setItem('token', token)
      await this.fetchUser()
    },
    logout() {
      this.user = null
      this.token = null
      useCookie<string | null>('token').value = null
      if (process.client) localStorage.removeItem('token')
      navigateTo('/login')
    },
    async fetchUser() {
      try {
        const config = useRuntimeConfig()
        const token = this.token || useCookie<string | null>('token').value || (process.client ? localStorage.getItem('token') : null)
        if (!token) return
        const res = await fetch(`${config.public.apiBase}/api/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          this.user = await res.json()
          this.token = token
          useCookie<string | null>('token').value = token
        } else {
          if (res.status === 401 || res.status === 403) this.logout()
        }
      } catch {
        // Keep existing session on transient network issues.
      }
    },
  },
})
