"""Unit tests for the calculation engine.

The blocking acceptance test is ``test_lapedrera_baseline_matches_html``:
it asserts that running ``compute(default_inputs())`` produces the same
totals as the HTML calculator on first render. Any drift here means the
port has diverged from the source of truth.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.calc import (
    DEFAULT_FX_UYU_PER_USD,
    DEFAULT_RUBROS,
    BudgetInputs,
    LaborParams,
    LineItem,
    ProjectAreas,
    compute,
    default_inputs,
    default_line_items,
)

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "lapedrera_baseline.json"


def approx(value: float, rel: float = 1e-6):
    return pytest.approx(value, rel=rel)


# ────────────────────────────────────────────────────────────────────────────
# Baseline regression — the acceptance test for MVP parity with the HTML.
# ────────────────────────────────────────────────────────────────────────────

def test_lapedrera_baseline_matches_html():
    """Default inputs reproduce the La Pedrera total from the HTML calculator.

    Verified values (computed by hand from the HTML constants):
      materials_usd  = 65_072.00
      jornales_total = 559        (428 casa + 131 deck)
      nomina_uyu     = 2_476_370.00
      auc_uyu        = 1_877_088.46
      mo_total_uyu   = 4_353_458.46
      mo_total_usd   = 104_902.6135...
      subtotal_usd   = 169_974.6135...
      contingency_usd= 16_997.4614...
      margin_usd     = 56_091.6225...
      total_usd      = 243_063.6973...
    """
    totals = compute(default_inputs())

    assert totals.materials_usd == approx(65_072.0)
    assert totals.jornales_casa == approx(428.0)
    assert totals.jornales_deck == approx(131.0)
    assert totals.jornales_total == approx(559.0)
    assert totals.nomina_uyu == approx(2_476_370.0)
    assert totals.auc_uyu == approx(1_877_088.46)
    assert totals.mo_total_uyu == approx(4_353_458.46)
    assert totals.mo_total_usd == approx(104_902.613493975903)
    assert totals.subtotal_usd == approx(169_974.613493975903)
    assert totals.contingency_usd == approx(16_997.4613493976)
    assert totals.margin_usd == approx(56_091.6224831116)
    assert totals.total_usd == approx(243_063.6907601169)
    assert totals.cost_per_m2_casa == approx(243_063.6907601169 / 107)
    assert totals.cost_per_m2_total == approx(243_063.6907601169 / 238)


def test_baseline_fixture_matches_engine():
    """The JSON fixture stays in sync with what the engine actually produces.

    Re-generate via:  python -m app.services.calc_dump_baseline > tests/fixtures/lapedrera_baseline.json
    """
    fixture = json.loads(FIXTURE_PATH.read_text())
    totals = compute(default_inputs())

    for field_name, expected in fixture["totals"].items():
        actual = getattr(totals, field_name)
        assert actual == approx(expected), f"{field_name}: {actual!r} != {expected!r}"


# ────────────────────────────────────────────────────────────────────────────
# Catalog shape — guards against accidentally dropping or duplicating rubros.
# ────────────────────────────────────────────────────────────────────────────

def test_default_catalog_has_17_rubros():
    assert len(DEFAULT_RUBROS) == 17


def test_default_catalog_codes_are_unique():
    codes = [r["code"] for r in DEFAULT_RUBROS]
    assert len(codes) == len(set(codes))


def test_every_rubro_has_a_default_option():
    for rubro in DEFAULT_RUBROS:
        option_ids = {o[0] for o in rubro["options"]}
        assert rubro["default_option"] in option_ids, rubro["code"]


def test_every_rubro_has_at_least_two_options():
    for rubro in DEFAULT_RUBROS:
        assert len(rubro["options"]) >= 2, rubro["code"]


def test_default_line_items_match_catalog_length():
    assert len(default_line_items()) == len(DEFAULT_RUBROS)


# ────────────────────────────────────────────────────────────────────────────
# Engine behavior — edge cases and recomputation rules.
# ────────────────────────────────────────────────────────────────────────────

def test_empty_budget_is_pure_labor_plus_margins():
    """Zero materials still computes a real total from labor + margins."""
    inputs = BudgetInputs(
        line_items=[],
        labor=LaborParams(2953, 1477, 4.0, 1.0, 75.8),
        areas=ProjectAreas(107, 131),
        contingency_pct=10,
        margin_pct=30,
        fx_uyu_per_usd=41.5,
    )
    totals = compute(inputs)
    assert totals.materials_usd == 0.0
    assert totals.subtotal_usd == approx(totals.mo_total_usd)
    expected_total = totals.mo_total_usd * 1.10 * 1.30
    assert totals.total_usd == approx(expected_total)


def test_zero_labor_collapses_to_materials_plus_margins():
    inputs = BudgetInputs(
        line_items=[LineItem("a", "Test", "u", qty=10, unit_price_usd=100)],
        labor=LaborParams(0, 0, 0, 0, 0),
        areas=ProjectAreas(100, 0),
        contingency_pct=10,
        margin_pct=30,
        fx_uyu_per_usd=41.5,
    )
    totals = compute(inputs)
    assert totals.materials_usd == 1000.0
    assert totals.mo_total_usd == 0.0
    assert totals.subtotal_usd == 1000.0
    assert totals.contingency_usd == 100.0
    assert totals.margin_usd == approx(1100 * 0.30)
    assert totals.total_usd == approx(1430.0)


def test_contingency_and_margin_are_multiplicative_not_additive():
    """Margin is taken on subtotal+contingency, not on subtotal alone."""
    inputs = BudgetInputs(
        line_items=[LineItem("a", "T", "u", qty=1, unit_price_usd=1000)],
        labor=LaborParams(0, 0, 0, 0, 0),
        areas=ProjectAreas(1, 0),
        contingency_pct=10,
        margin_pct=20,
        fx_uyu_per_usd=41.5,
    )
    totals = compute(inputs)
    assert totals.margin_usd == approx(1000 * 1.10 * 0.20)  # 220, not 200
    assert totals.total_usd == approx(1000 * 1.10 * 1.20)   # 1320


def test_cost_per_m2_handles_zero_area():
    inputs = BudgetInputs(
        line_items=[LineItem("a", "T", "u", qty=1, unit_price_usd=1000)],
        labor=LaborParams(0, 0, 0, 0, 0),
        areas=ProjectAreas(0, 0),
        contingency_pct=0,
        margin_pct=0,
        fx_uyu_per_usd=41.5,
    )
    totals = compute(inputs)
    assert totals.cost_per_m2_casa == 0.0
    assert totals.cost_per_m2_total == 0.0


def test_fx_rate_only_affects_labor_conversion():
    """Doubling FX should halve the USD value of labor but leave materials untouched."""
    base = default_inputs()
    doubled = BudgetInputs(
        line_items=base.line_items,
        labor=base.labor,
        areas=base.areas,
        contingency_pct=base.contingency_pct,
        margin_pct=base.margin_pct,
        fx_uyu_per_usd=base.fx_uyu_per_usd * 2,
    )

    base_t = compute(base)
    doubled_t = compute(doubled)

    assert base_t.materials_usd == doubled_t.materials_usd
    assert doubled_t.mo_total_usd == approx(base_t.mo_total_usd / 2)


def test_jornales_total_equals_components():
    totals = compute(default_inputs())
    assert totals.jornales_total == approx(totals.jornales_casa + totals.jornales_deck)


def test_total_uyu_round_trip():
    totals = compute(default_inputs())
    assert totals.total_uyu == approx(totals.total_usd * DEFAULT_FX_UYU_PER_USD)


# ────────────────────────────────────────────────────────────────────────────
# LineItem invariants
# ────────────────────────────────────────────────────────────────────────────

def test_line_item_total_is_qty_times_price():
    li = LineItem("x", "Test", "ml", qty=3.5, unit_price_usd=42.0)
    assert li.total_usd == approx(147.0)
