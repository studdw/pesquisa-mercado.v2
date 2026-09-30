# Pesquisa de Preços por Molécula — v2

Sistema web que pesquisa o preço de medicamentos por **molécula (princípio ativo)** em várias farmácias e na tabela oficial **CMED/Anvisa**, e reúne tudo em um só painel. Nasceu para eliminar uma tarefa manual e repetitiva do time de Novos Produtos: abrir o site de cada farmácia, buscar a molécula, anotar marcas e apresentações e montar o relatório.

**Frontend:** Next.js + Tailwind (Vercel) · **Backend:** FastAPI + Playwright (Render) · **Acesso:** [farmaciaslibbs.vercel.app](https://farmaciaslibbs.vercel.app) (protegido por senha do time)

![Tela da v2](docs/tela-v2.png)

---

## Da v1 para a v2

A [v1 (IALibbs)](https://github.com/studdw/IALibbs) era um protótipo em Streamlit que usava uma chave gratuita do Gemini. Validou a ideia, mas tinha limites para o uso diário. A v2 foi reconstruída como um sistema de produção.

| | v1 | v2 |
|---|---|---|
| Deploy | Streamlit | Vercel (frontend) + Render (backend) |
| IA | Chave gratuita do Gemini, com limite de uso | Sem ficar limitado ao uso do Gemini |
| Dados | Coleta sem base oficial | Base oficial da CMED/Anvisa (PMC) |
| Armazenamento | Sem banco de dados | Cache + histórico em banco de dados (SQLite local / Postgres em produção) |
| Disponibilidade | Sob demanda | Funcionamento 24/7 |

## Funcionalidades

- Busca de **várias moléculas de uma vez** (até 15, uma por linha ou separadas por vírgula).
- **Várias fontes** por busca: CMED/Anvisa (oficial) e farmácias por API ou HTML (Ultrafarma, Drogaria São Paulo, Drogarias Pacheco, Pague Menos).
- **Resumo por molécula:** menor preço (e em qual farmácia), média, máximo e número de laboratórios.
- **Identificação de laboratório** por prioridade: marca > base de referência > título do produto.
- **Cache com TTL** de 8 horas, com opção de ignorar o cache e buscar preços na hora.
- **Histórico** das consultas.
- **Acesso protegido por senha** do time.

## Arquitetura

```
Navegador ──► Vercel (Next.js)  ──[x-api-key]──►  Render (FastAPI)  ──►  Farmácias / CMED
              /api/search (proxy)                  cache + histórico
              senha do time                        matching de laboratório
```

A chave do backend fica **somente no servidor da Vercel** e nunca é exposta ao navegador. O frontend chama a própria rota `/api/*`, que repassa a requisição ao backend com a `x-api-key`.

## Estrutura do repositório

```
backend/
  app/main.py                 endpoints: /health /pharmacies /search /history
  app/scrapers/               um conector por farmácia (vtex.py, html_generic.py, browser.py)
  app/scrapers/registry.py    registro das farmácias disponíveis
  app/services/lab_matcher.py identificação de laboratório (marca > base ref. > título)
  app/services/storage.py     cache TTL + histórico (SQLite local / Postgres em produção)
  data/referencia_laboratorios.csv   base produto;molecula;laboratorio (editável)
  Dockerfile                  imagem oficial do Playwright
frontend/
  src/app/                    páginas (/, /login) e rotas proxy (/api/*)
  src/components/  src/hooks/  src/lib/
  src/middleware.js           proteção por senha
render.yaml                   blueprint do Render
.github/workflows/keepalive.yml   ping periódico para o Render não dormir
```

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | Next.js, React, Tailwind CSS |
| Backend | Python, FastAPI, Playwright |
| Dados | SQLite (local), PostgreSQL (produção), base CMED/Anvisa |
| Infra | Vercel, Render, Docker, GitHub Actions |

## 1. Rodar localmente

Pré-requisitos: Python 3.10+ e Node.js 18+.

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env            # Linux/Mac: cp .env.example .env
uvicorn app.main:app --reload     # http://localhost:8000/docs
python -m pytest -q tests         # 11 testes

# Frontend (em outro terminal)
cd frontend
npm install
copy .env.example .env.local      # Linux/Mac: cp .env.example .env.local
npm run dev                       # http://localhost:3000
```

Para testar os conectores que usam navegador (Playwright) localmente:

```bash
playwright install chromium
# e no backend/.env:
ENABLE_BROWSER=true
```

## 2. Variáveis de ambiente

| Onde | Variável | Para que serve |
|---|---|---|
| Render | `API_KEY` | Chave exigida pelo backend (gerada pelo blueprint) |
| Render | `ALLOWED_ORIGINS` | URL do frontend na Vercel (CORS) |
| Vercel | `BACKEND_URL` | URL do serviço no Render (`https://xxx.onrender.com`) |
| Vercel | `BACKEND_API_KEY` | Mesma `API_KEY` do Render |
| Vercel | `ACCESS_PASSWORD` | Senha de acesso do time |
| Vercel | `SESSION_SECRET` | Segredo usado para assinar a sessão |
| GitHub | `RENDER_HEALTH_URL` | `https://xxx.onrender.com/health` (usado pelo keepalive) |

## 3. Deploy

1. Suba o projeto para um repositório no GitHub.
2. **Render** → New → Blueprint → selecione o repositório. O `render.yaml` cria o serviço.
3. Copie a `API_KEY` gerada e a URL do serviço (`https://xxx.onrender.com`).
4. **Vercel** → Add New Project → selecione o repositório → **Root Directory = `frontend`** → configure `BACKEND_URL`, `BACKEND_API_KEY`, `ACCESS_PASSWORD` e `SESSION_SECRET`.
5. No Render, ajuste `ALLOWED_ORIGINS` com a URL da Vercel.
6. No GitHub → Settings → Secrets and variables → Actions, crie `RENDER_HEALTH_URL` com `https://xxx.onrender.com/health`. O workflow `keepalive.yml` evita que o Render hiberne no plano gratuito.

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verifica se o servidor está online |
| GET | `/pharmacies` | Lista as fontes disponíveis |
| POST | `/search` | Busca preços por molécula(s) e fonte(s) |
| GET | `/history` | Histórico de consultas |

A documentação interativa fica em `/docs` (Swagger) quando o backend está rodando.

## Adicionar uma farmácia

1. **Site VTEX:** crie uma classe em `backend/app/scrapers/vtex.py` com `key`, `label` e `base_url`.
2. **Outros sites:** crie uma classe em `backend/app/scrapers/html_generic.py` com `search_url` contendo `{q}`.
3. Registre a nova classe em `backend/app/scrapers/registry.py`.
4. Adicione a farmácia em `frontend/src/lib/pharmacies.js`.

## Base de laboratórios

O arquivo `backend/data/referencia_laboratorios.csv` (formato `produto;molecula;laboratorio`) é usado para identificar o laboratório de cada produto. Amplie-o sempre que encontrar itens sem laboratório identificado.

## Uso responsável

Ferramenta para consulta pontual e interna. O cache de 8 horas, a limitação de 1 requisição por vez por farmácia e o atraso aleatório entre requisições reduzem a carga nos sites consultados. **Não use para coleta em massa** e respeite os termos de uso de cada site. Os valores exibidos são de apoio à análise e devem ser conferidos na fonte antes de qualquer decisão comercial.

## Roadmap

- [ ] Adicionar mais farmácias
- [ ] Exportar resultados para Excel/CSV
- [ ] Gráfico de evolução de preços a partir do histórico
- [ ] Alertas de variação de preço

## Autor

**Lucas Pasturuti** — [LinkedIn](https://www.linkedin.com/in/lucas-pasturuti-354523273) · [GitHub](https://github.com/studdw)
