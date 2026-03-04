import type { Config } from 'tailwindcss'

export default {
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './plugins/**/*.{js,ts}',
    './app.vue',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Syne', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        surface: {
          DEFAULT: '#0d1117',
          1: '#161b22',
          2: '#21262d',
          3: '#30363d',
        },
        border: '#30363d',
        accent: '#f78166',
        'accent-2': '#79c0ff',
        muted: '#8b949e',
        fg: '#e6edf3',
        'fg-dim': '#c9d1d9',
        success: '#3fb950',
        warning: '#d29922',
        danger: '#f85149',
      },
    },
  },
  plugins: [],
} satisfies Config
