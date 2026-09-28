// Funciona no Edge (middleware) e no Node (route handlers): usa Web Crypto
export const COOKIE = "pp_session";
export async function sessionToken() {
  const data = new TextEncoder().encode(`${process.env.ACCESS_PASSWORD}|${process.env.SESSION_SECRET}`);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map((b) => b.toString(16).padStart(2, "0")).join("");
}
