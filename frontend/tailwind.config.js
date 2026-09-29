/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Tema Libbs
        brand: {
          50: "#eef4ff",   // fundos suaves
          100: "#dbe7ff",  // hover leve
          500: "#0049FF",  // azul Libbs — ações principais
          600: "#0040e0",  // hover de botão
          700: "#516D7F",  // cinza-azulado — cabeçalho e títulos
          900: "#3a4f5c",  // texto escuro / hover do header
        },
        accent: {
          50: "#e9f9eb",
          500: "#23C02E",  // verde Libbs — sucesso, descontos, status online
          600: "#1da627",
        },
      },
      fontFamily: { sans: ["var(--font-inter)", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
