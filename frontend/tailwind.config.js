/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Verde Libbs — ações principais
        brand: {
          50: "#eefaef",   // fundos suaves
          100: "#d3f2d6",  // hover leve
          500: "#23C02E",  // verde Libbs — botões e seleção
          600: "#1da627",  // hover de botão
          700: "#178c20",  // ícone do cabeçalho
          900: "#116619",  // hover escuro
        },
        // Cinza-azulado — textos, títulos e elementos secundários
        accent: {
          50: "#f4f6f7",
          500: "#516D7F",
          600: "#455c6b",
          700: "#3a4f5c",
        },
      },
      fontFamily: { sans: ["var(--font-inter)", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
