/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        // Institutional dark surface scale (zinc-based, opaque)
        surface: {
          950: '#09090b',  // zinc-950
          900: '#18181b',  // zinc-900
          800: '#27272a',  // zinc-800
          700: '#3f3f46',  // zinc-700
          600: '#52525b',  // zinc-600
          500: '#71717a',  // zinc-500
        },
        accent: {
          primary: '#f59e0b',  // amber-500   — primary UI accent
          buy:     '#10b981',  // emerald-500 — buy / profit
          sell:    '#f43f5e',  // rose-500    — sell / loss
          muted:   '#71717a',  // zinc-500    — secondary text / hold
        },
      },
    },
  },
  plugins: [],
}
