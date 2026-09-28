const MAP = {
  waking: { dot: "bg-amber-400 animate-pulse", text: "Iniciando servidor…" },
  online: { dot: "bg-emerald-500", text: "Servidor online" },
  offline: { dot: "bg-red-500", text: "Servidor indisponível" },
};
export default function BackendStatus({ state }) {
  const s = MAP[state] || MAP.waking;
  return (
    <span className="flex items-center gap-2 text-xs text-slate-500">
      <span className={`h-2 w-2 rounded-full ${s.dot}`} /> {s.text}
    </span>
  );
}
