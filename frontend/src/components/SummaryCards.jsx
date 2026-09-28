import { money } from "@/lib/format";

export default function SummaryCards({ rows }) {
  const byMol = rows.reduce((acc, r) => {
    if (r.price == null) return acc;
    (acc[r.molecule] ||= []).push(r);
    return acc;
  }, {});
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Object.entries(byMol).map(([mol, list]) => {
        const prices = list.map((r) => r.price);
        const min = Math.min(...prices), max = Math.max(...prices);
        const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
        const cheapest = list.find((r) => r.price === min);
        const labs = new Set(list.map((r) => r.laboratory).filter((l) => l !== "Não identificado"));
        const identified = list.filter((r) => r.laboratory !== "Não identificado").length;
        return (
          <div key={mol} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-brand-600">{mol}</p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">{money(min)}</p>
            <p className="truncate text-xs text-slate-500" title={cheapest?.name}>menor preço · {cheapest?.pharmacy}</p>
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
              <div><p className="text-slate-400">Média</p><p className="font-medium text-slate-700">{money(avg)}</p></div>
              <div><p className="text-slate-400">Máximo</p><p className="font-medium text-slate-700">{money(max)}</p></div>
              <div><p className="text-slate-400">Laboratórios</p><p className="font-medium text-slate-700">{labs.size}</p></div>
            </div>
            <p className="mt-3 text-[11px] text-slate-400">{list.length} produtos · {Math.round((identified / list.length) * 100)}% com laboratório identificado</p>
          </div>
        );
      })}
    </div>
  );
}
