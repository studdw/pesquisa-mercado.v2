"use client";
import { LogOut, Pill } from "lucide-react";
import BackendStatus from "./BackendStatus";

export default function Header({ backend }) {
  const logout = async () => {
    await fetch("/api/login", { method: "DELETE" });
    window.location.href = "/login";
  };
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-20">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-brand-700 text-white"><Pill size={18} /></div>
          <div>
            <h1 className="text-base font-semibold text-slate-900">Pesquisa de Preços por Molécula</h1>
            <p className="text-xs text-slate-500">Novos Produtos Varejo · Libbs</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <BackendStatus state={backend} />
          <button onClick={logout} className="text-slate-400 hover:text-slate-700" title="Sair"><LogOut size={18} /></button>
        </div>
      </div>
    </header>
  );
}
