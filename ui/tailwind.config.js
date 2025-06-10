/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // SentinelForge Dark Theme Colors - Matching Sign-in Page
        primary: {
          DEFAULT: '#9333ea', // purple-600 from sign-in
          foreground: '#ffffff',
        },
        accent: {
          DEFAULT: '#a855f7', // purple-500 accent
          foreground: '#ffffff',
        },
        background: '#0f172a', // slate-900 from sign-in gradient
        'background-muted': '#1e293b', // slate-800
        card: '#1e293b80', // slate-800/50 like sign-in card
        panel: '#334155', // slate-700
        modal: '#1e293b80', // slate-800/50 for modals
        border: '#475569', // slate-600 like sign-in inputs
        'text-primary': '#ffffff', // white like sign-in
        'text-muted': '#cbd5e1', // slate-300 like sign-in labels
        'text-low': '#94a3b8', // slate-400 like placeholders
        ring: '#9333ea', // purple-600 for focus
        // Severity colors - WCAG compliant
        critical: '#FF4D6D',
        high: '#FFAD60',
        medium: '#FFE062',
        low: '#92FFD0',
        // Tag colors
        'tag-bg': '#3B2A5E',
        'tag-text': '#E8DBFF',
        // Chart colors
        'chart-primary': '#7DF9FF',
        'chart-muted': '#3C314E',
        // Semantic colors
        destructive: {
          DEFAULT: '#FF4D6D',
          foreground: '#FFFFFF',
        },
        success: {
          DEFAULT: '#92FFD0',
          foreground: '#1A102E',
        },
        warning: {
          DEFAULT: '#FFAD60',
          foreground: '#1A102E',
        },
        // Light mode comprehensive colors
        light: {
          background: '#FFFFFF', /* Pure white */
          card: '#FAFAFA', /* Very light gray */
          panel: '#F8FAFC', /* Light panel background */
          modal: '#FFFFFF', /* White modals */
          sidebar: '#FFFFFF', /* White sidebar */
          'text-primary': '#0F172A', /* Dark slate text */
          'text-muted': '#475569', /* Medium gray text */
          'text-low': '#94A3B8', /* Light gray text */
          border: '#E2E8F0', /* Light border */
          hover: '#F1F5F9', /* Light hover state */
          'table-header': '#F8FAFC', /* Light table header */
          input: '#F8FAFC', /* Light input background */
        },
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "glow": {
          "0%, 100%": { boxShadow: "0 0 10px #A177FF" },
          "50%": { boxShadow: "0 0 20px #A177FF, 0 0 30px #A177FF" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      boxShadow: {
        'glow': '0 0 10px #A177FF',
        'glow-lg': '0 0 20px #A177FF, 0 0 30px #A177FF',
      },
    },
  },
  plugins: [],
};
