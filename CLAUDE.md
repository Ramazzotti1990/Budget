# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A multi-tenant SaaS for construction studios in Uruguay, shipped first as an intranet tool for **Estudio Sarachaga**. It replaces the standalone `cotizacion_lapedrera-1.html` calculator at the repo root — that HTML is the **behavioral source of truth** for the calculation logic and is kept until end-to-end parity is verified.

The full spec lives at `/root/.claude/plans/review-banch-content-precious-parasol.md` (not in the repo). Reference it for goals, data model rationale, the 14-PR build sequence, and verification plan.

## Commands

All commands run from `sistema_presupuestos/` unless noted.

```bash
# Setup (once)
pip install -r requirements.txt

# Run the test suite (18 tests, 93% coverage at PR #1)
APP_ENV=test pytest                                  # all tests
APP_ENV=test pytest tests/unit                       # calc engine only — no DB needed
APP_ENV=test pytest tests/unit/test_calc.py::test_lapedrera_baseline_matches_html  # the acceptance test
APP_ENV=test pytest --cov=app --cov-report=term-missing

# Lint
ruff check .
ruff check . --fix

# Migrations (Flask-Migrate wraps Alembic)
APP_ENV=test FLASK_APP=wsgi:app python -m flask db upgrade --directory migrations
APP_ENV=test FLASK_APP=wsgi:app python -m flask db migrate --directory migrations -m "msg"

# Bootstrap a studio + admin + seeded catalog (full local dev)
flask bootstrap-studio --slug sarachaga --name "Estudio Sarachaga" \
    --admin-email admin@sarachaga.uy --admin-password change-me

# Full local stack (Postgres + app + MailHog)
docker compose -f docker/docker-compose.yml up --build      # from repo root
```

## Architecture — the parts that aren't obvious from file names

**The calc engine is the heart and the rest is plumbing.** `app/services/calc.py` is a pure-function port of `cotizacion_lapedrera-1.html`. It has no DB or Flask imports so it's trivially testable. The blocking acceptance test `tests/unit/test_calc.py::test_lapedrera_baseline_matches_html` asserts that `compute(default_inputs())` reproduces the HTML calculator's total to the penny ($243,063.70 USD baseline). **Any change to calc.py must keep this test green** — if you change a constant intentionally, also update the baseline expected values and `tests/fixtures/lapedrera_baseline.json`.

**Currency model.** Material option prices are in USD. Labor (jornal, viático) is in UYU. A single `fx_uyu_per_usd` converts labor → USD at subtotal time. Percentages (AUC, contingency, margin) are stored as percentages (75.8, not 0.758) for editor friendliness. Contingency and margin **compound multiplicatively**: `total = (materials + mo) × (1 + contingency/100) × (1 + margin/100)` — there's a test guarding that ordering.

**Multi-tenancy convention.** Every non-root table carries `studio_id`. The MVP runs intranet-only for one studio, but every query is written as if there are many. Don't relax this — it's what makes the v1.2 SaaS multi-studio rollout straightforward.

**Labor history.** `LaborParam` is effective-dated. `BudgetVersion.labor_param_id` snapshots the row at finalization so re-opening a 2024 budget still recomputes with 2024 rates even after the studio raises its jornal.

**Seed defaults are duplicated by design.** `app/services/calc.py` holds `DEFAULT_RUBROS` / `DEFAULT_LABOR` as Python constants (so the engine can compute the baseline without a DB). `app/services/seed.py` reads from those same constants to populate a fresh studio's catalog. The Excel importer (future PR #5) will then become the source of price updates for living catalogs, but the constants stay as the bootstrap default.

**App factory + extensions split.** `app/__init__.py:create_app()` is the only place that wires extensions to the app; `app/extensions.py` holds the singletons (`db`, `migrate`, `login_manager`, `mail`) so models and blueprints can import them without circular dependencies. The single `Base(DeclarativeBase)` in `extensions.py` is what Alembic autogenerate inspects — every model must inherit from `db.Model` (which subclasses `Base`).

**Migration directory quirk.** `migrations/alembic.ini` deliberately omits `script_location` and `version_locations` — Flask-Migrate sets them based on the `--directory` flag, and any value in `alembic.ini` overrides that and silently drops new migrations into the wrong folder. Keep it that way.

## Build sequence

Work proceeds through 14 PRs (see the plan file). PR #1 (this branch's foundation) covered scaffold + 14 SQLAlchemy models + initial Alembic migration + calc engine + seed service. Subsequent PRs:

| | |
|---|---|
| #4 | Auth (Flask-Login + role decorators) |
| #5 | Catalog UI + Excel importer for `planilla_precios_lapedrera.xlsx` |
| #6 | Projects + clients CRUD |
| #7 | Budget editor (htmx port of the HTML's 3-tab UI) |
| #8 | PDF export (ES) — closes MVP |
| #9–13 | Magic-link share, comments, EN PDF, email, BCU FX cron, audit log |
| #14 | Delete `cotizacion_lapedrera-1.html` and `planilla_precios_lapedrera.xlsx` from repo root after full parity verified |

## Working notes

- The repo runs in a remote sandbox via Claude Code on the web — anything not committed is lost when the container is reclaimed.
- Branch policy: develop on `claude/create-matprompt-branch-mKNDO`, push to the same branch, create a draft PR. Never push to `main` directly.
- `cotizacion_lapedrera-1.html` and `planilla_precios_lapedrera.xlsx` at the repo root are **inputs**, not artifacts — don't modify, don't delete until PR #14.
