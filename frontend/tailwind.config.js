/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gold: {
          light: '#FFC14D',
          DEFAULT: '#F6A623',
          dark: '#E8912D',
        },
        obsidian: {
          light: '#1F2937',
          DEFAULT: '#111827',
          dark: '#0B0F14',
        }
      }
    },
  },
  plugins: [],
}

