"use client";
import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useHistory } from "@/hooks/useHistory";
import { money } from "@/lib/format";

const COLORS = ["#1f4e5f", "#2e9e8f", "#e0a13a", "#c2410c", "#6366f1"];

export default function HistoryChart({ molecules }) {
  const [mol, setMol] = useState(molecules[0] || "");
  const { rows, loading } = useHistory(mol);
  const pharmacies = [...new Set(rows.map((r) => r.pharmacy))];
  const byDay = Object.values(rows.reduce((acc, r) => {
    (acc[r.day] ||= { day: r.day.split("-").reverse().slice(0, 2).join("/") })[r.pharmacy] = r.min;
    return acc;
  }, {}));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Histórico do menor preço</h3>
          <p className="text-xs text-slate-500">Registrado a cada pesquisa realizada</p>
        </div>
        <select value={mol} onChange={(e) => setMol(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm capitalize">
          {molecules.map((m) => <option key={m}>{m}</option>)}
        </select>
      </div>
      {loading ? <p className="py-16 text-center text-sm text-slate-400">Carregando…</p>
        : byDay.length < 2 ? (
          <p className="py-16 text-center text-sm text-slate-400">
            O gráfico aparece a partir de 2 dias de pesquisas para esta molécula.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={byDay}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f5" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `R$${v}`} width={60} />
              <Tooltip formatter={(v) => money(v)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {pharmacies.map((p, i) => <Line key={p} type="monotone" dataKey={p} stroke={COLORS[i % 5]} strokeWidth={2} dot={{ r: 3 }} />)}
            </LineChart>
          </ResponsiveContainer>
        )}
    </div>
  );
}
