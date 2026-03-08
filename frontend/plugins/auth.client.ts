import { useAuthStore } from '~/stores/auth'
export default defineNuxtPlugin(async () => {
  const store = useAuthStore()
  store.hydrateToken()
  await store.fetchUser()
})
