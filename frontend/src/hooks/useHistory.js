"use client";
import { useEffect, useState } from "react";

export function useHistory(molecule) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!molecule) return;
    setLoading(true);
    fetch(`/api/history?molecule=${encodeURIComponent(molecule)}`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [molecule]);
  return { rows, loading };
}
