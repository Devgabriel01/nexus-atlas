/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        nexus: {
          black: '#050810',
          dark: '#090d1a',
          panel: '#0d1526',
          border: '#1a2a4a',
          cyan: '#00d4ff',
          blue: '#0066ff',
          green: '#00ff88',
          orange: '#ff6b00',
          red: '#ff2244',
          purple: '#8b5cf6',
          muted: '#4a6080',
          text: '#a0b4cc',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan-line': 'scanLine 2s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'radar-spin': 'radarSpin 3s linear infinite',
        'flicker': 'flicker 0.15s infinite',
        'data-stream': 'dataStream 10s linear infinite',
      },
      keyframes: {
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #00d4ff, 0 0 10px #00d4ff' },
          '100%': { boxShadow: '0 0 20px #00d4ff, 0 0 40px #00d4ff, 0 0 80px #00d4ff' },
        },
        radarSpin: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
        dataStream: {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '0% 100%' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'nexus-cyan': '0 0 20px rgba(0, 212, 255, 0.3)',
        'nexus-green': '0 0 20px rgba(0, 255, 136, 0.3)',
        'nexus-red': '0 0 20px rgba(255, 34, 68, 0.3)',
        'nexus-inner': 'inset 0 0 30px rgba(0, 212, 255, 0.05)',
      },
    },
  },
  plugins: [],
}
