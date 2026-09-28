"use client";
import { useEffect, useState } from "react";

// Render free "dorme" após 15 min: acordamos o backend assim que a página abre
export function useBackendWarmup() {
  const [state, setState] = useState("waking"); // waking | online | offline
  useEffect(() => {
    let alive = true;
    const t0 = Date.now();
    const ping = async () => {
      try {
        const r = await fetch("/api/health", { cache: "no-store" });
        if (alive) setState(r.ok ? "online" : Date.now() - t0 > 90000 ? "offline" : "waking");
        if (!r.ok && alive && Date.now() - t0 <= 90000) setTimeout(ping, 5000);
      } catch {
        if (alive) setTimeout(ping, 5000);
      }
    };
    ping();
    return () => { alive = false; };
  }, []);
  return state;
}
