/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ChatGPT-inspired color palette
        'chat': {
          'bg-light': '#ffffff',
          'bg-dark': '#212121',
          'surface-light': '#f7f7f8',
          'surface-dark': '#2f2f2f',
          'sidebar-light': '#f7f7f8',
          'sidebar-dark': '#171717',
          'border-light': '#e5e5e7',
          'border-dark': '#4d4d4f',
          'text-primary-light': '#0d0e0f',
          'text-primary-dark': '#ececf1',
          'text-secondary-light': '#676767',
          'text-secondary-dark': '#8e8ea0',
          'accent': '#10a37f',
          'accent-hover': '#0d8968',
        }
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      animation: {
        'slide-in': 'slideIn 0.2s ease-out',
        'fade-in': 'fadeIn 0.15s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        }
      }
    },
  },
  plugins: [],
}
