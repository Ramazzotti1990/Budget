# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a single-file, self-contained construction budget tool (`cotizacion_lapedrera-1.html`) for Estudio Sarachaga, quoting a residential project at La Pedrera, Uruguay. No build system, no dependencies, no package manager — open the file directly in a browser to run it.

## Development

Open `cotizacion_lapedrera-1.html` directly in a browser. There are no build, lint, or test commands. All logic, styles, and markup live in that one file.

## Architecture

The file follows a **data → state → render** pattern using vanilla JavaScript:

1. **Data layer** — two top-level constants define all domain data:
   - `RUBROS` — array of construction line items, each with `{id, cat, nom, un, cant, sel, ops[]}`. Each option (`ops`) has `{id, lbl, dc, p}` where `p` is the unit price in USD.
   - `MO` — object with all labor parameters: `jornal` (daily wage UYU), `viatico` (travel allowance), `jCasa`/`jDeck` (labor days per m²), `m2Casa`/`m2Deck` (surface areas), `auc` (unified construction contribution %), `empresa` (company margin %).

2. **State** — three mutable variables:
   - `uyu` (boolean) — whether to display in Uruguayan pesos instead of USD
   - `openId` (string|null) — which `RUBROS` item is expanded in the materials tab
   - `cantsState` (object) — maps `rub.id → quantity`, initialized from `RUBROS[*].cant` and mutated by the user; kept separate from `RUBROS` defaults so original values are preserved
   - `MO` object is mutated directly when the user edits labor parameters

3. **Render** — a single `render()` function rebuilds `#content` innerHTML on every state change. It branches on `tab` (`'mat'`, `'mo'`, `'res'`) and recomputes all derived values inline using helper functions.

## Key Calculations

All prices in `RUBROS` are in USD. Labor (`MO`) is computed in UYU then divided by `TC = 41.5` to convert to USD.

```
jornadaUYU  = jornal + viatico             // cost per worker-day in UYU
nominaUYU   = totalJornales × jornadaUYU  // gross payroll
aucUYU      = nominaUYU × (auc / 100)     // 71.8% BPS + 4% Caja Prof. = 75.8%
moUSD       = (nominaUYU + aucUYU) / TC

subtotalUSD = matUSD + moUSD
imprevistos = subtotalUSD × 0.10          // fixed 10% contingency
totalUSD    = (subtotalUSD + imprevistos) × (1 + empresa / 100)
```

## Domain Context (Uruguay)

- **Laudo** — official wage table set by the MTSS (Ministry of Labor) per trade group. `MO.jornal` follows Grupo 9 Sub 01 (construction), Category V.
- **BPS** — social security agency; contribution is 71.8% of gross payroll.
- **AUC** — Aporte Unificado Construcción: the combined employer contribution (BPS 71.8% + Caja de Profesionales 4% = 75.8%).
- **Viático** — travel allowance for workers traveling to La Pedrera; set at 50% of the daily wage per the Décima Ronda 2023 agreement for Grupo 9.
- Prices are oriented to **May 2026**; exchange rate `TC` is hardcoded at 41.5 UYU/USD.

## Conventions

- CSS is in a `<style>` block at the top; short utility class names (`.rv`, `.rl`, `.rs`, `.rc`, `.op`, etc.) are intentional and consistent throughout.
- Color per construction category is defined in `COL` and applied inline throughout the render function for visual grouping.
- The deck (131 m²) is tracked separately in calculations because it is not covered area (`m2Casa = 107`) — deck labor uses `jDeck` j/m² (placement only, no masonry or plastering).
- The currency toggle only affects display; all internal math uses USD.
