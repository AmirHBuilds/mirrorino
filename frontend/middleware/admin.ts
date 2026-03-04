import { useAuthStore } from '~/stores/auth'
export default defineNuxtRouteMiddleware(() => {
  const store = useAuthStore()
  if (!store.user || !['admin', 'superadmin'].includes(store.user.role)) {
    return navigateTo('/')
  }
})
