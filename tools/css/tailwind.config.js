/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['../../src/templates/**/*.j2', '../../assets/js/**/*.{js,mjs}'],
  theme: {
    extend: {
      colors: {
        sand: '#fcf6ee',
        card: '#fffbf6',
        linen: '#f3e5d6',
        ink: '#34251a',
        muted: '#706052',
        line: '#e0d6ca',
        peach: '#eda97c',
        sage: '#88aa80',
        terracotta: { DEFAULT: '#c06143', dark: '#a94c2e', darker: '#8f3d22' },
        olive: { DEFAULT: '#405f39', dark: '#33502d', fg: '#f6f2e7' },
      },
      fontFamily: {
        display: ['"Instrument Serif"', 'Georgia', 'serif'],
        sans: ['"Work Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
