/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        medical: {
          primary: '#2563eb',
          secondary: '#0ea5e9',
          danger: '#dc2626',
          warning: '#f59e0b',
          success: '#10b981',
        }
      }
    },
  },
  plugins: [],
}

