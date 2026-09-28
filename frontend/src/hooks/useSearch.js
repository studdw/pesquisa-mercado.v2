"use client";
import { useCallback, useState } from "react";

export function useSearch() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const search = useCallback(async ({ molecules, pharmacies, forceRefresh }) => {
    setLoading(true);
    setError("");
    try {
      const r = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ molecules, pharmacies, force_refresh: forceRefresh }),
      });
      const json = await r.json();
      if (!r.ok) throw new Error(typeof json.detail === "string" ? json.detail : "Erro na pesquisa");
      setData(json);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, search };
}
