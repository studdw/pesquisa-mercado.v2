import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend";

export const maxDuration = 60; // segundos — cobre cold start do Render + scraping

export async function POST(req) {
  try {
    const body = await req.json();
    const r = await backendFetch("/search", { method: "POST", body: JSON.stringify(body) });
    const data = await r.json().catch(() => ({ detail: "Resposta inválida do backend" }));
    return NextResponse.json(data, { status: r.status });
  } catch (e) {
    return NextResponse.json({ detail: `Backend indisponível: ${e.message}` }, { status: 502 });
  }
}
