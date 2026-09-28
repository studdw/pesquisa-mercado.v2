import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend";

export const maxDuration = 60;

export async function GET() {
  try {
    const r = await backendFetch("/health");
    return NextResponse.json(await r.json(), { status: r.status });
  } catch (e) {
    return NextResponse.json({ status: "down", detail: e.message }, { status: 502 });
  }
}
