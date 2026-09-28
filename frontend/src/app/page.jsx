"use client";
import { AlertCircle, Loader2 } from "lucide-react";
import Header from "@/components/Header";
import HistoryChart from "@/components/HistoryChart";
import ResultsTable from "@/components/ResultsTable";
import SearchForm from "@/components/SearchForm";
import StatusBar from "@/components/StatusBar";
import SummaryCards from "@/components/SummaryCards";
import { useBackendWarmup } from "@/hooks/useBackendWarmup";
import { useSearch } from "@/hooks/useSearch";

export default function Home() {
  const backend = useBackendWarmup();
  const { data, loading, error, search } = useSearch();
  const results = data?.results || [];
  const molecules = [...new Set(results.map((r) => r.molecule))];

  return (
    <>
      <Header backend={backend} />
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <SearchForm onSearch={search} loading={loading} />

        {loading && (
          <div className="flex items-center gap-3 rounded-xl bg-brand-50 px-4 py-3 text-sm text-brand-700">
            <Loader2 size={16} className="animate-spin" />
            Consultando farmácias… {backend === "waking" && "o servidor está acordando, a primeira busca pode levar até 1 minuto."}
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {data && (
          <>
            <StatusBar status={data.status} elapsed={data.elapsed_s} />
            {results.length ? (
              <>
                <SummaryCards rows={results} />
                <ResultsTable rows={results} />
                <HistoryChart key={molecules.join("|")} molecules={molecules} />
              </>
            ) : (
              <p className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
                Nenhum produto encontrado. Verifique a grafia da molécula ou o status das farmácias acima.
              </p>
            )}
          </>
        )}
      </main>
    </>
  );
}
