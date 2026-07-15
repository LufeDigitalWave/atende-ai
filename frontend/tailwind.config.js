/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand gradient: violet → cyan
        brand: {
          violet: '#a855f7',  // 600
          cyan: '#06b6d4',    // 500
          violet_light: '#c084fc',  // 400
          cyan_light: '#22d3ee',    // 400
        },
        // Dark canvas (quasi-black, bluish tint)
        dark: {
          bg: '#0a0f1f',      // Deep navy-black
          surface: '#141929',  // Slightly lighter for cards
          border: '#1f2937',   // Subtle borders
        },
      },
      animation: {
        'pulse-dot': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(168, 85, 247, 0.3)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 30px rgba(168, 85, 247, 0.5)' },
        },
      },
    },
  },
  plugins: [],
};
