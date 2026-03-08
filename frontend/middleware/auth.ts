export default defineNuxtRouteMiddleware(() => {
  const token = useCookie<string | null>('token').value || (process.client ? localStorage.getItem('token') : null)
  if (!token) return navigateTo('/login')
})
