"use client";
import { Loader2, Lock, Pill } from "lucide-react";
import { useState } from "react";

export default function Login() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const r = await fetch("/api/login", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password }),
    });
    if (r.ok) window.location.href = "/";
    else { setError("Senha incorreta"); setLoading(false); }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-gradient-to-br from-brand-50 to-slate-100 px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 grid h-12 w-12 place-items-center rounded-xl bg-brand-700 text-white"><Pill size={22} /></div>
          <h1 className="text-lg font-semibold text-slate-900">Pesquisa de Preços por Molécula</h1>
          <p className="text-sm text-slate-500">Acesso restrito ao time Libbs</p>
        </div>
        <div className="relative">
          <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Senha de acesso" autoFocus
            className="w-full rounded-lg border border-slate-300 py-2.5 pl-9 pr-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100" />
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button disabled={loading || !password}
          className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-brand-700 py-2.5 text-sm font-medium text-white hover:bg-brand-900 disabled:opacity-50">
          {loading && <Loader2 size={16} className="animate-spin" />} Entrar
        </button>
      </form>
    </main>
  );
}
