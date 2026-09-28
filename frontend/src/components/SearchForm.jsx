"use client";
import { Loader2, Search } from "lucide-react";
import { useState } from "react";
import { DEFAULT_PHARMACIES, PHARMACIES } from "@/lib/pharmacies";

export default function SearchForm({ onSearch, loading }) {
  const [text, setText] = useState("");
  const [selected, setSelected] = useState(DEFAULT_PHARMACIES);
  const [force, setForce] = useState(false);

  const molecules = text.split(/[\n;,]+/).map((m) => m.trim()).filter(Boolean);
  const toggle = (k) => setSelected((s) => (s.includes(k) ? s.filter((x) => x !== k) : [...s, k]));
  const submit = (e) => {
    e.preventDefault();
    if (molecules.length && selected.length) onSearch({ molecules, pharmacies: selected, forceRefresh: force });
  };

  return (
    <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <label className="text-sm font-medium text-slate-700">Moléculas</label>
      <p className="mb-2 text-xs text-slate-500">Uma por linha, ou separadas por vírgula (máx. 15).</p>
      <textarea
        value={text} onChange={(e) => setText(e.target.value)} rows={3}
        placeholder={"semaglutida\nempagliflozina\nlosartana"}
        className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
      />
      <div className="mt-5">
        <span className="text-sm font-medium text-slate-700">Farmácias</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {PHARMACIES.map((p) => {
            const on = selected.includes(p.key);
            return (
              <button type="button" key={p.key} onClick={() => toggle(p.key)}
                className={`rounded-full border px-3 py-1.5 text-sm transition ${on ? "border-brand-600 bg-brand-600 text-white" : "border-slate-300 bg-white text-slate-600 hover:border-brand-500"}`}>
                {p.label}
                <span className={`ml-1.5 text-[10px] ${on ? "text-brand-100" : "text-slate-400"}`}>{p.source}</span>
              </button>
            );
          })}
        </div>
      </div>
      <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} className="accent-brand-600" />
          Ignorar cache (buscar preços agora)
        </label>
        <button disabled={loading || !molecules.length || !selected.length}
          className="flex items-center gap-2 rounded-lg bg-brand-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-900 disabled:cursor-not-allowed disabled:opacity-50">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          {loading ? "Pesquisando…" : `Pesquisar ${molecules.length ? `(${molecules.length})` : ""}`}
        </button>
      </div>
    </form>
  );
}
