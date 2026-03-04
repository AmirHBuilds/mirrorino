import { useAuthStore } from '~/stores/auth'

export function useAuth() {
  const store = useAuthStore()
  return {
    user: computed(() => store.user),
    isLoggedIn: computed(() => !!store.user),
    isAdmin: computed(() => ['admin', 'superadmin'].includes(store.user?.role || '')),
    isSuperAdmin: computed(() => store.user?.role === 'superadmin'),
    login: store.login,
    logout: store.logout,
    fetchUser: store.fetchUser,
  }
}
