import type { Ad } from '~/types'

export function useAds() {
  const { get, post } = useApi()

  const { data, pending, refresh } = useAsyncData(
    'active-ads-global',
    () => get<Ad[]>('/api/ads/active'),
    { server: false, default: () => [] },
  )

  const ads = computed(() => data.value || [])

  async function trackClick(adId: number) {
    try {
      await post<{ target_url: string }>(`/api/ads/${adId}/click`, {})
    } catch {
      // Keep UX smooth if tracking fails.
    }
  }

  return {
    ads,
    pending,
    refresh,
    trackClick,
  }
}
