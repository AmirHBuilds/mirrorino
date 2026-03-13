export default defineNuxtConfig({
  devtools: { enabled: false },
  components: [{ path: '~/components', pathPrefix: false }],
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/icon',
    '@nuxtjs/color-mode',
  ],
  icon: {
    provider: 'server',
    fallbackToApi: false,
    customCollections: [
      { prefix: 'mdilocal', dir: './icons/mdi' },
      { prefix: 'mirror-platforms', dir: './icons/platforms' },
    ],
  },
  colorMode: {
    preference: 'dark',
    fallback: 'dark',
    classSuffix: '',
  },
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'https://api.mirrorino.com',
      supportEmail: process.env.NUXT_PUBLIC_SUPPORT_EMAIL || '',
      supportTelegramId: process.env.NUXT_PUBLIC_SUPPORT_TELEGRAM_ID || '',
      supportWebsite: process.env.NUXT_PUBLIC_SUPPORT_WEBSITE || '',
    },
  },
  app: {
    head: {
      htmlAttrs: { class: 'dark' },
      titleTemplate: '%s — Mirrorino',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
      ],
    },
  },
})
