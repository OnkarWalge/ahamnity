/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
  bg: '#0B0712',
  surface: '#171022',
  ink: '#F3EFFA',
  'ink-soft': '#9A8CB5',
  teal: {
    deep: '#2E1065',
    bright: '#A855F7',
  },
  saffron: {
    DEFAULT: '#E879F9',
    soft: '#4A044E',
  },
  risk: {
    low: '#22C55E',
    'low-bg': '#0F2E1B',
    medium: '#F59E0B',
    'medium-bg': '#3A2305',
    high: '#DC2626',
    'high-bg': '#3A0D0D',
  },
},
      fontFamily: {
        display: ['Sora', 'Noto Sans', 'sans-serif'],
        body: ['Inter', 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Bengali', 'Noto Sans Telugu', 'Noto Sans Tamil', 'sans-serif'],
      },
     boxShadow: {
  card: '0 2px 20px -2px rgba(168, 85, 247, 0.15)',
  'card-lg': '0 8px 40px -4px rgba(168, 85, 247, 0.28)',
},
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.04)', opacity: '0.92' },
        },
        ringPulse: {
          '0%': { transform: 'scale(0.9)', opacity: '0.7' },
          '100%': { transform: 'scale(1.8)', opacity: '0' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        flashTeal: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(20, 184, 166, 0)' },
          '15%': { boxShadow: '0 0 0 4px rgba(20, 184, 166, 0.45)' },
        },
        flashAlert: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(220, 38, 38, 0)' },
          '15%': { boxShadow: '0 0 0 5px rgba(220, 38, 38, 0.5)' },
        },
      },
      animation: {
        breathe: 'breathe 3.5s ease-in-out infinite',
        ringPulse: 'ringPulse 1.6s ease-out infinite',
        fadeUp: 'fadeUp 0.4s ease-out forwards',
        flashTeal: 'flashTeal 1.4s ease-out 2',
        flashAlert: 'flashAlert 1.4s ease-out 3',
      },
    },
  },
  plugins: [],
}