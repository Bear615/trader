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
        surface: {
          950: '#030712',
          900: '#0d1117',
          800: '#161b22',
          700: '#21262d',
          600: '#30363d',
          500: '#484f58',
        },
        accent: {
          buy: '#10b981',      // emerald-500
          sell: '#f43f5e',     // rose-500
          ai: '#38bdf8',       // sky-400
          warning: '#f59e0b',  // amber-500
        },
      },
    },
  },
  plugins: [],
}
