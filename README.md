# Pesquisa de Preços por Molécula — v2

Frontend **Next.js + Tailwind (Vercel)** · Backend **FastAPI + Playwright (Render)**

```
Navegador ──► Vercel (Next.js)  ──[x-api-key]──►  Render (FastAPI)  ──►  Farmácias
              /api/search (proxy)                  cache + histórico
              senha do time                        matching de laboratório
```

A chave do backend fica **só no servidor da Vercel** — nunca vai para o navegador.

## Estrutura
```
backend/
  app/main.py                 endpoints: /health /pharmacies /search /history
  app/scrapers/               um conector por farmácia (vtex.py, html_generic.py, browser.py)
  app/scrapers/registry.py    registre novas farmácias aqui
  app/services/lab_matcher.py identificação de laboratório (brand > base ref. > título)
  app/services/storage.py     cache TTL + histórico (SQLite local / Postgres em produção)
  data/referencia_laboratorios.csv   base produto;molecula;laboratorio (EDITE/AMPLIE)
  Dockerfile                  imagem oficial do Playwright
frontend/
  src/app/                    páginas (/, /login) e rotas proxy (/api/*)
  src/components/  src/hooks/  src/lib/
  src/middleware.js           proteção por senha
render.yaml                   blueprint do Render
.github/workflows/keepalive.yml   ping para o Render não dormir
```

## 1. Rodar localmente
```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env                              # Linux/Mac: cp
uvicorn app.main:app --reload                       # http://localhost:8000/docs
python -m pytest -q tests                           # 11 testes

# Frontend (outro terminal)
cd frontend
npm install
copy .env.example .env.local
npm run dev                                         # http://localhost:3000
```
Para testar o Playwright localmente: `playwright install chromium` e `ENABLE_BROWSER=true` no `.env`.

## 2. Deploy
Veja o passo a passo completo na resposta do Copilot / seção abaixo.

1. Suba tudo para um repositório no GitHub.
2. **Render** → New → Blueprint → repositório → aplica `render.yaml`.
3. Copie a `API_KEY` gerada e a URL do serviço (`https://xxx.onrender.com`).
4. **Vercel** → Add New Project → repositório → **Root Directory = `frontend`** → variáveis:
   `BACKEND_URL`, `BACKEND_API_KEY`, `ACCESS_PASSWORD`, `SESSION_SECRET`.
5. No Render, ajuste `ALLOWED_ORIGINS` com a URL da Vercel.
6. GitHub → Settings → Secrets → `RENDER_HEALTH_URL = https://xxx.onrender.com/health`.

## Adicionar farmácia
- Site VTEX: crie uma classe em `vtex.py` com `key`, `label`, `base_url`.
- Outros: classe em `html_generic.py` com `search_url` contendo `{q}`.
- Registre em `registry.py` e adicione em `frontend/src/lib/pharmacies.js`.

## Uso responsável
Ferramenta para consulta pontual interna. Cache de 8h, 1 requisição por vez por farmácia
com delay aleatório. Não use para coleta massiva; respeite os termos de uso dos sites.
