// Só roda no servidor (route handlers) — a chave nunca vai para o navegador
export async function backendFetch(path, init = {}) {
  const base = process.env.BACKEND_URL;
  if (!base) throw new Error("BACKEND_URL não configurada");
  return fetch(`${base.replace(/\/$/, "")}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "x-api-key": process.env.BACKEND_API_KEY || "", ...(init.headers || {}) },
    cache: "no-store",
  });
}
