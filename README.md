# Sistema de Presupuestos — Estudio Sarachaga

Flask + Postgres app for pricing construction projects in Uruguay.
Replaces the standalone `cotizacion_lapedrera-1.html` calculator with a
multi-tenant intranet that persists projects, generates branded PDFs, and
(in v1.1) shares quotes with clients via magic-link.

See [CLAUDE.md](./CLAUDE.md) for architecture notes and build sequence.

## Quickstart (local)

```bash
docker compose -f docker/docker-compose.yml up --build
docker compose -f docker/docker-compose.yml exec app flask db upgrade
docker compose -f docker/docker-compose.yml exec app flask bootstrap-studio \
    --slug sarachaga --name "Estudio Sarachaga" \
    --admin-email admin@sarachaga.uy --admin-password change-me
```

Open <http://localhost:8000/health> for a liveness check, <http://localhost:8025>
for the local MailHog inbox.

## Project layout

```
sistema_presupuestos/
  app/
    services/calc.py       # The calculation engine — pure functions, well tested
    services/seed.py       # Studio catalog bootstrap
    models/                # SQLAlchemy models (studio, user, project, budget, …)
    blueprints/            # Flask routes
    templates/             # Jinja (web UI + PDF templates)
  migrations/              # Alembic
  tests/
    unit/test_calc.py      # Calc engine — covers La Pedrera baseline
    integration/           # Flask test client
  pyproject.toml           # ruff + mypy + pytest config
  requirements.txt
  wsgi.py
docker/
  Dockerfile
  docker-compose.yml       # app + Postgres + MailHog
.github/workflows/ci.yml
```

## Tests

```bash
cd sistema_presupuestos
pip install -r requirements.txt
pytest                       # all
pytest tests/unit            # calc engine only
pytest --cov=app             # with coverage
```

The acceptance test for MVP parity is
`tests/unit/test_calc.py::test_lapedrera_baseline_matches_html` — it asserts
that `compute(default_inputs())` reproduces the HTML calculator's total to
the penny.

## Roadmap

| Phase | Scope |
|-------|-------|
| **MVP (v1.0)** | Auth, catalog UI, projects/clients, budget editor, ES PDF export. |
| **v1.1**       | Magic-link share pages, comments + approval, EN PDF, email, BCU FX cron, audit log surfaced, object storage. |
| **v1.2**       | Multi-studio signup + billing. |

## Source artifacts

- `cotizacion_lapedrera-1.html` — original calculator. Kept until calc-engine
  parity tests are green; will be removed in a follow-up commit.
- `planilla_precios_lapedrera.xlsx` — initial materials catalog, ingested by
  `flask import-excel` (PR #5).
