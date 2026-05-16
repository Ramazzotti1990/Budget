"""
Construction-budget calculation engine.

Pure functions — no DB, no Flask — so the logic is trivially testable.
Inputs are plain dicts (serialized from SQLAlchemy or JSON); outputs are
dataclasses.

Currency model mirrors the HTML calculator:
  - Material option prices are denominated in USD per unit.
  - Labor parameters (jornal, viático) are in UYU.
  - A single FX rate (`fx_uyu_per_usd`) converts labor → USD for the
    subtotal.
  - All percentages (AUC, contingency, margin) are expressed as
    percentages (e.g. 75.8, not 0.758) for editor friendliness.

Source of defaults: ``cotizacion_lapedrera-1.html`` (Estudio Sarachaga
La Pedrera 2026 baseline). See ``DEFAULT_*`` constants below.
"""
from __future__ import annotations

from dataclasses import dataclass

# ────────────────────────────────────────────────────────────────────────────
# Defaults — taken verbatim from the HTML calculator. Treated as seed data;
# every value is editable per studio / per budget version once persisted.
# ────────────────────────────────────────────────────────────────────────────

DEFAULT_FX_UYU_PER_USD: float = 41.5

DEFAULT_LABOR: dict[str, float] = {
    "jornal_uyu": 2953.0,        # Laudo Cat V abril 2025 (MTSS Grupo 9 Sub 01)
    "viatico_uyu": 1477.0,       # 50% jornal · Décima Ronda 2023 zona costera
    "j_per_m2_casa": 4.0,        # Rango BPS construcción: 3.5–5
    "j_per_m2_deck": 1.0,        # Solo colocación deck: rango 0.8–1.5
    "auc_pct": 75.8,             # 71.8% BPS + 4% Caja Prof. Arquitectura
}

DEFAULT_PROJECT_AREAS: dict[str, float] = {
    "casa_m2": 107.0,
    "deck_m2": 131.0,
}

DEFAULT_CONTINGENCY_PCT: float = 10.0
DEFAULT_MARGIN_PCT: float = 30.0

# 17 rubros, each with default qty + 2-4 material options (USD per unit).
# Tuple of (code, category, name, unit, default_qty, default_option_id, options).
# Each option is (id, label, description, price_usd).
DEFAULT_RUBROS: list[dict] = [
    {
        "code": "mamp_ext", "category": "Estructura",
        "name": "Mampostería exterior", "unit": "ml",
        "default_qty": 54, "default_option": "a",
        "options": [
            ("a", "Bloque hormigón 20cm", "Bloque 20×20×40 c/ MO", 85),
            ("b", "Steel Frame", "Steel frame galv. c/ aislación", 110),
            ("c", "Bloque cerámico 20cm", "Cerámico hueco c/ MO", 72),
        ],
    },
    {
        "code": "mamp_int", "category": "Estructura",
        "name": "Mampostería interior", "unit": "ml",
        "default_qty": 35, "default_option": "a",
        "options": [
            ("a", "Bloque hormigón 15cm", "Bloque 15×20×40 c/ MO", 65),
            ("b", "Steel Frame interior", "Tabique steel frame + placa yeso", 80),
            ("c", "Bloque cerámico 12cm", "Cerámico hueco c/ MO", 58),
        ],
    },
    {
        "code": "cubierta", "category": "Cubierta",
        "name": "Cubierta 4 aguas", "unit": "m2",
        "default_qty": 120, "default_option": "a",
        "options": [
            ("a", "Chapa galvanizada N°27", "Ondulada + estructura metálica", 55),
            ("b", "Chapa prepintada color", "Trapezoidal prepintada + estructura", 68),
            ("c", "Zinc standing seam", "Zinc natural alta gama", 95),
        ],
    },
    {
        "code": "pergola", "category": "Cubierta",
        "name": "Pérgolas Norte + Sur", "unit": "m2",
        "default_qty": 32, "default_option": "a",
        "options": [
            ("a", "Policarbonato 6mm", "Ondulado + alfajías pino", 45),
            ("b", "Policarbonato 10mm", "Alveolar + estructura aluminio", 62),
            ("c", "Madera + tejuela", "Estructura madera + tejuela asfáltica", 55),
        ],
    },
    {
        "code": "fachada", "category": "Fachada Exterior",
        "name": "Revestimiento fachada", "unit": "m2",
        "default_qty": 134, "default_option": "a",
        "options": [
            ("a", "Cladding pino autoclave", "Machihembrado + lasur protector", 83),
            ("b", "Chapa metálica prepintada", "Panel trapezoidal acero prepintado", 71),
            ("c", "Revoque + pintura", "Revoque exterior + elastomérico", 38),
            ("d", "Cladding Ipê / Cumaru", "Madera dura tropical + aceite", 115),
        ],
    },
    {
        "code": "rev_int", "category": "Revestimiento Interior",
        "name": "Revoque + pintura interior", "unit": "m2",
        "default_qty": 175, "default_option": "a",
        "options": [
            ("a", "Yeso proyectado + látex", "Yeso + 2 manos látex lavable", 25),
            ("b", "Revoque cal + pintura", "Cal-portland + látex", 22),
            ("c", "Microcemento", "2mm con sellador", 55),
        ],
    },
    {
        "code": "rev_bano", "category": "Revestimiento Interior",
        "name": "Revestimiento baños", "unit": "m2",
        "default_qty": 45, "default_option": "a",
        "options": [
            ("a", "Porcelanato 30×60", "Rectificado piso a techo", 35),
            ("b", "Porcelanato 60×60", "Gran formato fragüe fino", 48),
            ("c", "Cerámico estándar", "20×40 cm esmaltado", 22),
        ],
    },
    {
        "code": "piso_hum", "category": "Pisos",
        "name": "Pisos baños + cocina", "unit": "m2",
        "default_qty": 25, "default_option": "a",
        "options": [
            ("a", "Porcelanato 60×60", "Antideslizante c/ adhesivo", 32),
            ("b", "Cerámico antideslizante", "40×40 cm", 20),
            ("c", "Microcemento piso", "Pigmentado con sellador epoxi", 58),
        ],
    },
    {
        "code": "piso_seco", "category": "Pisos",
        "name": "Pisos living + dormitorios", "unit": "m2",
        "default_qty": 82, "default_option": "a",
        "options": [
            ("a", "Madera ingeniería 12mm", "Flotante c/ zócalo", 45),
            ("b", "Vinílico SPC 5mm", "100% impermeable rígido", 28),
            ("c", "Madera maciza 18mm", "Eucaliptus o Roble", 72),
            ("d", "Porcelanato 90×90", "Gran formato rectificado", 52),
        ],
    },
    {
        "code": "deck", "category": "Deck Exterior",
        "name": "Deck perimetral", "unit": "m2",
        "default_qty": 131, "default_option": "a",
        "options": [
            ("a", "Cumaru / Teca 19mm", "Madera dura, tornillería inox", 95),
            ("b", "Pino autoclave H4", "Tratado H4, tornillería galv.", 58),
            ("c", "Deck composite WPC", "Sin mantenimiento, anti-UV", 78),
            ("d", "Ipê natural", "Máxima durabilidad costera", 110),
        ],
    },
    {
        "code": "ventanas", "category": "Aberturas",
        "name": "Ventanas (est. 10 un.)", "unit": "u",
        "default_qty": 10, "default_option": "a",
        "options": [
            ("a", "Aluminio DVH", "Corredizas + doble vidriado", 380),
            ("b", "Aluminio vidrio simple", "Corredizas + vidrio simple", 220),
            ("c", "Carpintería madera", "Madera dura c/ herrajes inox", 480),
        ],
    },
    {
        "code": "puertas_int", "category": "Aberturas",
        "name": "Puertas interiores (7 un.)", "unit": "u",
        "default_qty": 7, "default_option": "a",
        "options": [
            ("a", "Placa HDF", "0.80×2.05m c/ marco y herrajes", 180),
            ("b", "Madera maciza", "Pino/cedro c/ marco y herrajes", 290),
            ("c", "Corredera embutida", "Flush c/ riel embutido", 350),
        ],
    },
    {
        "code": "puerta_ext", "category": "Aberturas",
        "name": "Puerta exterior principal", "unit": "u",
        "default_qty": 1, "default_option": "a",
        "options": [
            ("a", "Madera pivotante", "Madera dura + vidrio lateral", 650),
            ("b", "Chapa + vidrio", "Metálica prepintada + vidrio", 480),
            ("c", "Aluminio + DVH", "Aluminio c/ doble vidriado", 750),
        ],
    },
    {
        "code": "sanitaria", "category": "Instalaciones",
        "name": "Instalación sanitaria", "unit": "gl",
        "default_qty": 1, "default_option": "a",
        "options": [
            ("a", "PVC estándar", "Cañería PVC + accesorios + MO", 3500),
            ("b", "PPR alta calidad", "PPR termofusión + accesorios", 4800),
        ],
    },
    {
        "code": "electrica", "category": "Instalaciones",
        "name": "Instalación eléctrica", "unit": "gl",
        "default_qty": 1, "default_option": "a",
        "options": [
            ("a", "Monofásica estándar", "Tablero + cañería + bocas", 3200),
            ("b", "Bifásica + domótica", "Bifásica + módulos domótica", 5500),
        ],
    },
    {
        "code": "sanitarios", "category": "Instalaciones",
        "name": "Sanitarios y griferías (3 baños)", "unit": "jgo",
        "default_qty": 3, "default_option": "a",
        "options": [
            ("a", "Línea básica", "WC, lavatorio, ducha, grifería", 850),
            ("b", "Línea media", "WC rimless, bacha embutida", 1400),
            ("c", "Línea premium", "WC suspendido, vessel, diseño", 2200),
        ],
    },
    {
        "code": "parrillero", "category": "Parrillero / Lavadero",
        "name": "Parrillero", "unit": "u",
        "default_qty": 1, "default_option": "a",
        "options": [
            ("a", "Ladrillo refractario", "Tradicional c/ cámara y chimenea", 1200),
            ("b", "Módulo acero inox", "Prefabricado inox c/ instalación", 1800),
        ],
    },
]


# ────────────────────────────────────────────────────────────────────────────
# Computation dataclasses
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LineItem:
    """A single rubro selection in a budget version.

    ``unit_price_usd`` is the snapshotted price at the moment the budget
    references this option, so re-pricing the catalog never silently
    changes a sent budget.
    """
    code: str
    name: str
    unit: str
    qty: float
    unit_price_usd: float

    @property
    def total_usd(self) -> float:
        return self.unit_price_usd * self.qty


@dataclass(frozen=True)
class LaborParams:
    jornal_uyu: float
    viatico_uyu: float
    j_per_m2_casa: float
    j_per_m2_deck: float
    auc_pct: float

    @property
    def jornada_uyu(self) -> float:
        return self.jornal_uyu + self.viatico_uyu


@dataclass(frozen=True)
class ProjectAreas:
    casa_m2: float
    deck_m2: float


@dataclass(frozen=True)
class BudgetInputs:
    """All inputs the engine needs to produce a quote.

    ``line_items`` is the materials section.
    ``labor`` + ``areas`` drive the MO+BPS section.
    ``contingency_pct`` and ``margin_pct`` close out the final total.
    ``fx_uyu_per_usd`` converts UYU labor to USD for the subtotal.
    """
    line_items: list[LineItem]
    labor: LaborParams
    areas: ProjectAreas
    contingency_pct: float
    margin_pct: float
    fx_uyu_per_usd: float


@dataclass(frozen=True)
class BudgetTotals:
    materials_usd: float
    jornales_casa: float
    jornales_deck: float
    jornales_total: float
    nomina_uyu: float
    auc_uyu: float
    mo_total_uyu: float
    mo_total_usd: float
    subtotal_usd: float
    contingency_usd: float
    base_with_contingency_usd: float
    margin_usd: float
    total_usd: float
    total_uyu: float
    cost_per_m2_casa: float
    cost_per_m2_total: float


# ────────────────────────────────────────────────────────────────────────────
# Engine
# ────────────────────────────────────────────────────────────────────────────

def compute(inputs: BudgetInputs) -> BudgetTotals:
    """Produce a full set of totals for one budget version.

    Formulas mirror ``cotizacion_lapedrera-1.html`` exactly:

      materials_usd      = Σ qty × unit_price_usd
      jornales_casa      = j_per_m2_casa × casa_m2
      jornales_deck      = j_per_m2_deck × deck_m2
      nomina_uyu         = (j_casa + j_deck) × (jornal + viático)
      auc_uyu            = nomina_uyu × auc_pct / 100
      mo_total_uyu       = nomina_uyu + auc_uyu
      mo_total_usd       = mo_total_uyu / fx
      subtotal_usd       = materials_usd + mo_total_usd
      contingency_usd    = subtotal_usd × contingency_pct / 100
      base_with_cont     = subtotal_usd + contingency_usd
      margin_usd         = base_with_cont × margin_pct / 100
      total_usd          = base_with_cont + margin_usd
    """
    materials_usd = sum(li.total_usd for li in inputs.line_items)

    j_casa = inputs.labor.j_per_m2_casa * inputs.areas.casa_m2
    j_deck = inputs.labor.j_per_m2_deck * inputs.areas.deck_m2
    j_total = j_casa + j_deck

    nomina_uyu = j_total * inputs.labor.jornada_uyu
    auc_uyu = nomina_uyu * inputs.labor.auc_pct / 100.0
    mo_total_uyu = nomina_uyu + auc_uyu
    mo_total_usd = mo_total_uyu / inputs.fx_uyu_per_usd

    subtotal_usd = materials_usd + mo_total_usd
    contingency_usd = subtotal_usd * inputs.contingency_pct / 100.0
    base_with_contingency = subtotal_usd + contingency_usd
    margin_usd = base_with_contingency * inputs.margin_pct / 100.0
    total_usd = base_with_contingency + margin_usd
    total_uyu = total_usd * inputs.fx_uyu_per_usd

    casa = inputs.areas.casa_m2
    casa_plus_deck = casa + inputs.areas.deck_m2

    return BudgetTotals(
        materials_usd=materials_usd,
        jornales_casa=j_casa,
        jornales_deck=j_deck,
        jornales_total=j_total,
        nomina_uyu=nomina_uyu,
        auc_uyu=auc_uyu,
        mo_total_uyu=mo_total_uyu,
        mo_total_usd=mo_total_usd,
        subtotal_usd=subtotal_usd,
        contingency_usd=contingency_usd,
        base_with_contingency_usd=base_with_contingency,
        margin_usd=margin_usd,
        total_usd=total_usd,
        total_uyu=total_uyu,
        cost_per_m2_casa=total_usd / casa if casa > 0 else 0.0,
        cost_per_m2_total=total_usd / casa_plus_deck if casa_plus_deck > 0 else 0.0,
    )


def default_line_items() -> list[LineItem]:
    """Return the La Pedrera baseline: every rubro at default qty + option 'a'."""
    items: list[LineItem] = []
    for rubro in DEFAULT_RUBROS:
        default_opt_id = rubro["default_option"]
        option = next(o for o in rubro["options"] if o[0] == default_opt_id)
        _opt_id, label, _desc, price_usd = option
        items.append(LineItem(
            code=rubro["code"],
            name=f"{rubro['name']} — {label}",
            unit=rubro["unit"],
            qty=float(rubro["default_qty"]),
            unit_price_usd=float(price_usd),
        ))
    return items


def default_inputs() -> BudgetInputs:
    """The exact La Pedrera baseline that the HTML calculator computes on load."""
    return BudgetInputs(
        line_items=default_line_items(),
        labor=LaborParams(**DEFAULT_LABOR),
        areas=ProjectAreas(**DEFAULT_PROJECT_AREAS),
        contingency_pct=DEFAULT_CONTINGENCY_PCT,
        margin_pct=DEFAULT_MARGIN_PCT,
        fx_uyu_per_usd=DEFAULT_FX_UYU_PER_USD,
    )
