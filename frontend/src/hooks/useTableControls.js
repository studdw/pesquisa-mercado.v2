"use client";
import { useMemo, useState } from "react";

export function useTableControls(rows) {
  const [sort, setSort] = useState({ key: "price", dir: "asc" });
  const [filters, setFilters] = useState({ text: "", pharmacy: "", laboratory: "", molecule: "", onlyAvailable: false });

  const options = useMemo(() => {
    const uniq = (k) => [...new Set(rows.map((r) => r[k]).filter(Boolean))].sort();
    return { pharmacy: uniq("pharmacy"), laboratory: uniq("laboratory"), molecule: uniq("molecule") };
  }, [rows]);

  const view = useMemo(() => {
    const t = filters.text.toLowerCase();
    const out = rows.filter((r) =>
      (!t || r.name.toLowerCase().includes(t)) &&
      (!filters.pharmacy || r.pharmacy === filters.pharmacy) &&
      (!filters.laboratory || r.laboratory === filters.laboratory) &&
      (!filters.molecule || r.molecule === filters.molecule) &&
      (!filters.onlyAvailable || r.available));
    const { key, dir } = sort;
    const m = dir === "asc" ? 1 : -1;
    return out.sort((a, b) => {
      const x = a[key], y = b[key];
      if (x == null) return 1;
      if (y == null) return -1;
      return (typeof x === "number" ? x - y : String(x).localeCompare(String(y), "pt-BR")) * m;
    });
  }, [rows, filters, sort]);

  const toggleSort = (key) =>
    setSort((s) => ({ key, dir: s.key === key && s.dir === "asc" ? "desc" : "asc" }));

  return { view, sort, toggleSort, filters, setFilters, options };
}
