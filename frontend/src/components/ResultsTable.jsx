"use client";
import { ArrowDown, ArrowUp, Download, ExternalLink } from "lucide-react";
import { useTableControls } from "@/hooks/useTableControls";
import { exportToExcel } from "@/lib/exportExcel";
import { LAB_SOURCE, money, pct } from "@/lib/format";

const COLS = [
  ["molecule", "Molécula"], ["pharmacy", "Farmácia"], ["name", "Produto"], ["laboratory", "Laboratório"],
  ["quantity", "Qtd."], ["price", "Preço"], ["discount_pct", "Desc."], ["unit_price", "Preço unit."],
];

function Select({ value, onChange, options, placeholder }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-600 focus:border-brand-500 focus:outline-none">
      <option value="">{placeholder}</option>
      {options.map((o) => <option key={o}>{o}</option>)}
    </select>
  );
}

export default function ResultsTable({ rows }) {
  const { view, sort, toggleSort, filters, setFilters, options } = useTableControls(rows);
  const set = (k) => (v) => setFilters((f) => ({ ...f, [k]: v }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 p-4">
        <input value={filters.text} onChange={(e) => set("text")(e.target.value)} placeholder="Filtrar produto…"
          className="w-52 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none" />
        <Select value={filters.molecule} onChange={set("molecule")} options={options.molecule} placeholder="Todas moléculas" />
        <Select value={filters.pharmacy} onChange={set("pharmacy")} options={options.pharmacy} placeholder="Todas farmácias" />
        <Select value={filters.laboratory} onChange={set("laboratory")} options={options.laboratory} placeholder="Todos laboratórios" />
        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          <input type="checkbox" checked={filters.onlyAvailable} onChange={(e) => set("onlyAvailable")(e.target.checked)} className="accent-brand-600" />
          Só disponíveis
        </label>
        <span className="ml-auto text-xs text-slate-400">{view.length} de {rows.length}</span>
        <button onClick={() => exportToExcel(view)}
          className="flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50">
          <Download size={14} /> Excel
        </button>
      </div>
      <div className="max-h-[65vh] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {COLS.map(([k, label]) => (
                <th key={k} onClick={() => toggleSort(k)} className="cursor-pointer select-none whitespace-nowrap px-4 py-3 hover:text-slate-800">
                  <span className="inline-flex items-center gap-1">{label}
                    {sort.key === k && (sort.dir === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}
                  </span>
                </th>
              ))}
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {view.map((r, i) => {
              const src = LAB_SOURCE[r.lab_source] || LAB_SOURCE.nenhum;
              return (
                <tr key={`${r.pharmacy}-${r.name}-${i}`} className={`hover:bg-brand-50/40 ${!r.available ? "opacity-50" : ""}`}>
                  <td className="whitespace-nowrap px-4 py-2.5 capitalize text-slate-600">{r.molecule}</td>
                  <td className="whitespace-nowrap px-4 py-2.5 text-slate-600">{r.pharmacy}</td>
                  <td className="px-4 py-2.5 text-slate-900">{r.name}</td>
                  <td className="whitespace-nowrap px-4 py-2.5">
                    <span className={r.laboratory === "Não identificado" ? "text-slate-400 italic" : "text-slate-700"}>{r.laboratory}</span>
                    <span className={`ml-2 rounded px-1.5 py-0.5 text-[10px] ring-1 ${src.cls}`}>{src.label}</span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">{r.quantity ?? "—"}</td>
                  <td className="whitespace-nowrap px-4 py-2.5 font-medium text-slate-900">
                    {money(r.price)}
                    {r.list_price && <span className="ml-1.5 text-xs text-slate-400 line-through">{money(r.list_price)}</span>}
                  </td>
                  <td className="px-4 py-2.5 text-emerald-600">{pct(r.discount_pct)}</td>
                  <td className="whitespace-nowrap px-4 py-2.5 text-slate-600">{money(r.unit_price)}</td>
                  <td className="px-4 py-2.5">
                    {r.url && <a href={r.url} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-brand-600"><ExternalLink size={14} /></a>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!view.length && <p className="p-10 text-center text-sm text-slate-400">Nenhum produto com esses filtros.</p>}
      </div>
    </div>
  );
}
