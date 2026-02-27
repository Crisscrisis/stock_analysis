/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary:   '#0f1117',
          secondary: '#1a1d27',
          panel:     '#1e2130',
          hover:     '#252838',
        },
        accent: {
          blue:  '#3b82f6',
          green: '#22c55e',
          red:   '#ef4444',
          gray:  '#6b7280',
        },
        border: '#2a2d3e',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
