import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend";

export async function GET(req) {
  const molecule = req.nextUrl.searchParams.get("molecule") || "";
  try {
    const r = await backendFetch(`/history?molecule=${encodeURIComponent(molecule)}`);
    return NextResponse.json(await r.json(), { status: r.status });
  } catch (e) {
    return NextResponse.json({ detail: e.message }, { status: 502 });
  }
}
