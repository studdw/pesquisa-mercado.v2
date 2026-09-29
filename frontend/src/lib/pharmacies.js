// Deve bater com as chaves de backend/app/scrapers/registry.py
export const PHARMACIES = [
  { key: "cmed", label: "CMED/Anvisa", source: "Oficial" },
  { key: "ultrafarma", label: "Ultrafarma", source: "HTML" },
  { key: "drogariasaopaulo", label: "Drogaria São Paulo", source: "API" },
  { key: "pacheco", label: "Drogarias Pacheco", source: "API" },
  { key: "paguemenos", label: "Pague Menos", source: "API" },
];
export const DEFAULT_PHARMACIES = ["ultrafarma", "drogariasaopaulo", "cmed"];
