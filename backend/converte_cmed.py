"""Converte a planilha CMED para Parquet (menor e muito mais leve de carregar)."""
import pandas as pd
from app.services.cmed import CmedCatalog, DATA

cat = CmedCatalog()
assert cat.available, "planilha CMED não encontrada"

c = cat._cols
cols = {v: k for k, v in c.items() if k != "pmc" and v}
cols.update({v: f"pmc_{k}" for k, v in c["pmc"].items()})

df = cat.df[list(cols)].rename(columns=cols)
for col in df.columns:
    if col.startswith("pmc_") or col == "pf":
        df[col] = (df[col].astype(str).str.replace(r"[^\d,.]", "", regex=True)
                   .str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
        df[col] = pd.to_numeric(df[col], errors="coerce")

out = DATA / "cmed.parquet"
df.to_parquet(out, index=False, compression="zstd")
print(f"OK: {len(df)} linhas -> {out} ({out.stat().st_size/1e6:.1f} MB)")