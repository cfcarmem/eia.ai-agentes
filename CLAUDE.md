# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Didactic Python + Streamlit application for customer registration ("Cadastro de Clientes"). Single-user, no database — `clientes.csv` is the sole source of truth. Built via a documented multi-agent workflow (analyst → architect → dev → QA → docs) and intentionally kept minimal; do not introduce a database, auth, multi-user support, or editing/deletion of records unless explicitly asked.

## Commands

```bash
pip install -r requirements.txt   # install deps (streamlit>=1.45,<2, pandas>=2.2,<3)
streamlit run app.py              # run the app (http://localhost:8501)
python -m py_compile app.py validacoes.py repositorio_clientes.py   # syntax check
```

There is no automated test suite. QA verification in this project has been done via ad-hoc Python snippets exercising `validacoes.py` / `repositorio_clientes.py` directly (e.g. `python -c "import validacoes as v; ..."`) and by running the Streamlit server and checking it responds (`curl -s -o /dev/null -w "%{http_code}" http://localhost:8501`). Follow that pattern for verification — write a throwaway script, run it, and clean up any `clientes.csv`/`__pycache__` it generates before finishing.

## Architecture

Three flat Python modules, each with a single responsibility, communicating via plain function calls (no classes, no DI):

- **`app.py`** — Streamlit UI layer only. Renders the form, calls into validation and persistence, shows `st.success`/`st.error`. Contains no business rules and no file I/O.
- **`validacoes.py`** — pure validation functions (no disk access, no Streamlit). Central entry point is `validar_cliente(dados, email_existe)`, which returns a list of error strings (empty = valid). `email_existe` is computed by the caller (`app.py`) via the repository, since duplicate-checking needs persisted data.
- **`repositorio_clientes.py`** — persistence only (no validation, no Streamlit). Reads/writes `clientes.csv` via pandas with fixed columns `nome,email,telefone,cidade`.

Flow: form submit → `app.py` calls `repositorio.email_ja_cadastrado()` then `validacoes.validar_cliente()` → on errors, `st.error` per message and nothing is saved → on success, `repositorio.salvar_cliente()`, `st.success`, clear the form via `st.session_state`, `st.rerun()`. The list below the form is always re-read fresh from `repositorio.ler_clientes()` on every rerun, which is how "list updates automatically" is satisfied without extra refresh code.

**Important invariants (source of a past critical bug, now fixed):**
- `salvar_cliente` never does a positional CSV append. It reads the full file via `ler_clientes` (which reindexes to the fixed `COLUNAS` order and fills any missing column with `""`), concatenates the new row, and rewrites the whole file. This avoids silently corrupting columns if the on-disk header is ever reordered or incomplete.
- Email is lower-cased before being persisted, and duplicate checks (`email_ja_cadastrado`) compare case-insensitively.
- Any text field starting with `=`, `+`, `-`, or `@` is rejected by `validar_caractere_formula` (CSV/formula-injection protection for users who open the export in Excel/LibreOffice) — applied to `nome` and `cidade`.
- Technical I/O errors (`OSError`, `pd.errors.ParserError`) are converted to `RuntimeError` inside `repositorio_clientes.py` and caught in `app.py`'s `main()`, so raw stack traces are never shown to the user.
- There is no file locking; concurrent writers (e.g. two browser sessions) can race. This is a known, accepted limitation, not a bug to silently "fix" with added complexity — see `docs/qa_relatorio.md` (P4) before changing this.

## Repo conventions specific to this project

- Comments/docstrings and all agent-facing docs are written in Portuguese; keep new code/comments in Portuguese for consistency.
- Out of scope by design (do not add without the user explicitly asking): editing or deleting customers, a real database, authentication, multi-user concurrency handling, data import, advanced email/phone verification.
- `docs/requisitos.md`, `docs/arquitetura.md`, and `docs/qa_relatorio.md` are living design docs from the original build (requirements RF01-RF10/RN01-RN08 with Gherkin-style acceptance criteria, architecture rationale, and a QA findings log with severities). Check them before changing validation rules, the CSV schema, or the module split — they record *why* things are the way they are, including bugs already found and fixed.
- `.claude/agents/` defines five custom subagents (`analista`, `arquiteto`, `dev`, `qa`, `documentador`) used to build this project in sequence. When asked to extend the app following the same process, reuse this pipeline (analyst → architect → dev → QA → fix → docs) rather than editing code directly.
