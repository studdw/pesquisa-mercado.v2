const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
export const money = (v) => (v == null ? "—" : brl.format(v));
export const pct = (v) => (v == null ? "—" : `${v.toLocaleString("pt-BR")}%`);
export const LAB_SOURCE = {
  brand: { label: "Farmácia", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  referencia: { label: "Base ref.", cls: "bg-sky-50 text-sky-700 ring-sky-200" },
  titulo: { label: "Título", cls: "bg-amber-50 text-amber-700 ring-amber-200" },
  nenhum: { label: "—", cls: "bg-slate-100 text-slate-500 ring-slate-200" },
};
