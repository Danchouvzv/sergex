/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0056C7',
        secondary: '#00AEEF',
        danger: '#FF5F57',
        success: '#28A745',
        warning: '#FFC107',
        info: '#17A2B8',
        dark: '#343A40',
        light: '#F8F9FA',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '1rem',
      },
    },
  },
  plugins: [],
} 