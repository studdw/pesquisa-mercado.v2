import { AlertTriangle, CheckCircle2, Database } from "lucide-react";

export default function StatusBar({ status, elapsed }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {status.map((s) => (
        <span key={s.pharmacy} title={s.error || ""}
          className={`flex items-center gap-1.5 rounded-full px-3 py-1 ring-1 ${s.ok ? "bg-white text-slate-600 ring-slate-200" : "bg-red-50 text-red-700 ring-red-200"}`}>
          {s.ok ? <CheckCircle2 size={13} className="text-emerald-500" /> : <AlertTriangle size={13} />}
          {s.pharmacy}: {s.ok ? `${s.count} itens` : "falhou"}
          {s.cached && s.ok && <Database size={12} className="text-slate-400" title="do cache" />}
        </span>
      ))}
      <span className="ml-auto text-slate-400">{elapsed}s</span>
    </div>
  );
}
