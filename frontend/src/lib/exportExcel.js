import * as XLSX from "xlsx";

export function exportToExcel(rows, filename = "pesquisa-precos.xlsx") {
  const data = rows.map((r) => ({
    Molécula: r.molecule, Farmácia: r.pharmacy, Produto: r.name, Laboratório: r.laboratory,
    "Origem Lab.": r.lab_source, Concentração: r.concentration ?? "", Quantidade: r.quantity ?? "",
    "Preço (R$)": r.price ?? "", "Preço De (R$)": r.list_price ?? "", "Desconto (%)": r.discount_pct ?? "",
    "Preço Unit. (R$)": r.unit_price ?? "", EAN: r.ean ?? "", Disponível: r.available ? "Sim" : "Não", Link: r.url ?? "",
  }));
  const ws = XLSX.utils.json_to_sheet(data);
  ws["!cols"] = [14, 18, 48, 20, 11, 14, 10, 11, 12, 11, 13, 15, 10, 50].map((w) => ({ wch: w }));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Resultados");
  XLSX.writeFile(wb, filename);
}
