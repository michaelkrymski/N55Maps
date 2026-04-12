"""
N55 E85 Tuning — 3-Map Build Script
BMW F22 M235i xDrive | MEVD17.2 | DAA01 XDF | Pure 750 | E85

Run with --audit to print current table values without modifying anything.
Run without --audit to apply all changes and export the next E85 revision.

Usage:
    py build_e85_maps.py --audit
    py build_e85_maps.py
"""

import sys
import os
import struct
from pathlib import Path

# Add TunerPro Converter to path
CONVERTER_DIR = r"C:\Users\Michael Krymski\Documents\TunerPro Converter"
sys.path.insert(0, CONVERTER_DIR)

XDF_PATH = r"C:\Users\Michael Krymski\Documents\N55Maps\Tools\000021571DAA01.xdf"
N55MAPS_ROOT = Path(r"C:\Users\Michael Krymski\Documents\N55Maps")
E85_REVISIONS_DIR = N55MAPS_ROOT / "E85" / "Revisions"


def find_latest_e85_revision() -> Path:
    """Return the newest active E85 revision from the current folder layout."""
    candidates = sorted(
        E85_REVISIONS_DIR.glob("*.bin"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No E85 revision BINs found in {E85_REVISIONS_DIR}")
    return candidates[0]


def next_e85_revision_path(latest_path: Path) -> Path:
    """Choose the next E85vN output name without overwriting an existing revision."""
    revision_numbers = []
    for path in E85_REVISIONS_DIR.glob("E85v*.bin"):
        stem = path.stem
        if stem.startswith("E85v"):
            number_text = ""
            for char in stem[4:]:
                if not char.isdigit():
                    break
                number_text += char
            if number_text:
                revision_numbers.append(int(number_text))

    next_revision = (max(revision_numbers) + 1) if revision_numbers else 2
    output_path = latest_path.with_name(f"E85v{next_revision}.bin")
    while output_path.exists():
        next_revision += 1
        output_path = latest_path.with_name(f"E85v{next_revision}.bin")
    return output_path


BIN_PATH = str(find_latest_e85_revision())
OUT_BIN  = str(next_e85_revision_path(Path(BIN_PATH)))

from xdf_parser import parse_xdf
from editor_core import EditSession

# ── Boost-zone load / RPM thresholds ────────────────────────────────────────
# We define "WOT / high boost zone" as the top N rows by load index.
# After auditing the actual Y-axis breakpoints we can tighten these.
WOT_LOAD_ROWS = 4   # top 4 rows of load axis = WOT zone
MID_LOAD_ROWS = 4   # next 4 rows = transition zone

# ── AFR targets (gasoline-display, with STEC=85 active) ─────────────────────
# Map 1 (15 psi): 12.5 AFR (lambda ~0.85)
# Map 2 (22 psi): 12.2 AFR (lambda ~0.83)
# Map 3 (27 psi): 12.0 AFR (lambda ~0.82)
AFR_MAP = {1: 12.5, 2: 12.2, 3: 12.0}

# Spool fuel target: slightly richer than main WOT target
SPOOL_AFR_ENRICH = 0.3   # e.g. Map1 spool WOT zone → 12.5 - 0.3 = 12.2

# ── Timing deltas vs stock (degrees, boost zone) ─────────────────────────────
TIMING_DELTA = {1: 4.0, 2: 3.0, 3: 2.0}   # added over stock under boost
TIMING_CRUISE_DELTA = 1.5   # add to low-load cells
TIMING_COLD_DELTA   = 2.0
TIMING_SPOOL_DELTA  = 1.0

# ── Torque limit flat target ─────────────────────────────────────────────────
TORQUE_TARGET_NM = 900.0   # Nm

# ── Spool Mode Max RPM ───────────────────────────────────────────────────────
SPOOL_MAX_RPM = 3000

# ── Cold start enrichment multiplier ─────────────────────────────────────────
COLD_START_ENRICH_FACTOR = 1.175   # +17.5% fueling for E85 cold start

# ── EGT ceiling raise ────────────────────────────────────────────────────────
EGT_RAISE_C = 60   # raise pre-cat EGT ceiling by 60°C

# ═══════════════════════════════════════════════════════════════════════════════

def load_session() -> EditSession:
    xdf_bytes = open(XDF_PATH, "rb").read()
    bin_bytes  = open(BIN_PATH, "rb").read()
    return EditSession(xdf_bytes=xdf_bytes, bin_bytes=bin_bytes,
                       xdf_name=os.path.basename(XDF_PATH), bin_name=os.path.basename(BIN_PATH))


def find_tables(session: EditSession) -> dict[str, str]:
    """Return {name_hint: table_id} for all relevant tables."""
    all_tables = session.list_tables()

    # Patterns we care about
    TARGETS = [
        "KF_LABAS_1", "KF_LABAS_2", "KF_UESP_LA",
        "KF_LAMIN_H", "KF_FRKKORRF_1", "FRKMAX_UM",
        "KF_ST_RKBAS_VVT", "KF_ST_RKBAS_COMF_VVT",
        "KF_ZW_PF1", "KF_ZW_PF2", "KF_ZW_PF3",
        "KF_ZW_S_PF1", "KF_ZW_UESP_PF1",
        "KF_RFMAXATL_KR", "KF_RFMAXATL_SK",
        "KF_MDKMAX_GANG_MOD1", "KF_MDKMAX_GANG_MOD2",
        "KF_MDIOP_1", "KF_MDIOP_2",
        "KF_F_MDMX_TANS",
    ]

    found = {}
    for t in all_tables:
        title = t.get("title", "")
        tid   = t.get("table_id", "")
        for pat in TARGETS:
            if pat in title:
                key = pat
                # disambiguate map-switching variants
                if "(Map 2)" in title:
                    key = pat + "_MAP2"
                elif "(Map 3)" in title:
                    key = pat + "_MAP3"
                elif "(Map 4)" in title:
                    key = pat + "_MAP4"
                found[key] = tid
                break
    return found


def fmt_grid(table_data: dict, label: str) -> str:
    """Format a table as an aligned grid string."""
    grid = table_data["grid"]
    x_labels = table_data.get("x_labels", [])
    y_labels = table_data.get("y_labels", [])
    rows = table_data["rows"]
    cols = table_data["cols"]
    units = table_data.get("units", "")

    lines = [f"\n{'='*60}", f"  {label}  ({rows}×{cols}) [{units}]", f"{'='*60}"]

    # Column headers
    if x_labels:
        hdr = "          " + "  ".join(f"{v:>8.1f}" for v in x_labels[:cols])
        lines.append(hdr)
        lines.append("          " + "-"*(cols*10))

    for r in range(rows):
        prefix = f"{y_labels[r]:>8.1f} |" if r < len(y_labels) else f"  row{r+1:>3} |"
        vals = "  ".join(f"{grid[r][c]:>8.3f}" for c in range(cols))
        lines.append(prefix + "  " + vals)

    return "\n".join(lines)


def audit(session: EditSession, table_map: dict[str, str]):
    print("\n" + "█"*60)
    print(f"  AUDIT — {os.path.basename(BIN_PATH)} current values")
    print("█"*60)

    if not table_map:
        print("  !! No tables found. Check XDF title matching.")
        return

    for name, tid in sorted(table_map.items()):
        try:
            data = session.get_table(tid)
            print(fmt_grid(data, name + f"  [id:{tid}]"))
        except Exception as e:
            print(f"\n  !! Could not read {name} ({tid}): {e}")

    # Also read Spool Mode Max RPM scalar directly
    print("\n" + "="*60)
    print("  Spool Mode Max RPM  [0x18980A]")
    print("="*60)
    try:
        spool_tables = [t for t in session.list_tables()
                        if "spool" in t.get("title","").lower() and "max" in t.get("title","").lower()
                        and "rpm" in t.get("title","").lower()]
        if spool_tables:
            for st in spool_tables[:3]:
                data = session.get_table(st["table_id"])
                print(f"  {st['title']}  [id:{st['table_id']}]")
                print(f"    value: {data['grid'][0][0]}")
        else:
            print("  (not found by title search — will need direct address write)")
    except Exception as e:
        print(f"  !! {e}")

    # Torque tables
    print("\n" + "="*60)
    print("  Torque-related tables search")
    print("="*60)
    torque_tables = [t for t in session.list_tables()
                     if any(kw in t.get("title","").lower() for kw in ["torque","mdkmax","mdiop","0x1a87"])]
    for t in torque_tables[:10]:
        print(f"  {t['title']}  [id:{t['table_id']}]  {t.get('rows',0)}×{t.get('cols',0)}")

    print("\n" + "█"*60)
    print("  AUDIT COMPLETE — no changes made")
    print("█"*60 + "\n")


def _rows_cols(session, tid):
    data = session.get_table(tid)
    return data["rows"], data["cols"], data["grid"]


def build_fuel_table(session: EditSession, tid: str, map_num: int, is_spool: bool = False):
    """Set WOT zone to AFR target, preserve lower load rows."""
    rows, cols, grid = _rows_cols(session, tid)
    wot_afr = AFR_MAP[map_num]
    if is_spool:
        wot_afr -= SPOOL_AFR_ENRICH

    # Top WOT_LOAD_ROWS rows = full WOT target
    for r in range(max(0, rows - WOT_LOAD_ROWS), rows):
        session.apply_operation(
            tid, "set_cells",
            {"row_start": r, "row_end": r, "col_start": 0, "col_end": cols - 1},
            {"value": wot_afr}
        )

    # Next MID_LOAD_ROWS rows = interpolate from cruise to WOT target
    mid_top_r    = max(0, rows - WOT_LOAD_ROWS - 1)
    mid_bottom_r = max(0, rows - WOT_LOAD_ROWS - MID_LOAD_ROWS)
    if mid_top_r > mid_bottom_r:
        # Use existing mid-load cell values as base, blend toward WOT target
        for r in range(mid_bottom_r, mid_top_r + 1):
            # blend factor: 0 at bottom of mid zone → 1 at top of mid zone
            frac = (r - mid_bottom_r) / max(mid_top_r - mid_bottom_r, 1)
            # Get current row average as cruise value
            cruise_afr = sum(grid[r]) / max(cols, 1)
            blended = cruise_afr + frac * (wot_afr - cruise_afr)
            session.apply_operation(
                tid, "set_cells",
                {"row_start": r, "row_end": r, "col_start": 0, "col_end": cols - 1},
                {"value": round(blended, 3)}
            )


def build_timing_table(session: EditSession, tid: str, boost_delta: float,
                       cruise_delta: float = None, rows_override: int = None):
    """Add timing delta to boost zone and optionally cruise zone."""
    rows, cols, grid = _rows_cols(session, tid)
    if rows_override:
        rows = min(rows, rows_override)

    # Add boost_delta to top WOT_LOAD_ROWS rows
    wot_start = max(0, rows - WOT_LOAD_ROWS)
    session.apply_operation(
        tid, "add_constant",
        {"row_start": wot_start, "row_end": rows - 1, "col_start": 0, "col_end": cols - 1},
        {"value": boost_delta}
    )

    # Add cruise_delta to lower rows if specified
    if cruise_delta and wot_start > 0:
        session.apply_operation(
            tid, "add_constant",
            {"row_start": 0, "row_end": max(0, wot_start - 1), "col_start": 0, "col_end": cols - 1},
            {"value": cruise_delta}
        )


def build_maps(session: EditSession, table_map: dict[str, str]):
    print("\n" + "█"*60)
    print("  BUILDING MAPS")
    print("█"*60)

    # ── FUEL: Map 1 (base tables) ────────────────────────────────────────────
    print("\n[FUEL] Map 1 (15 psi, 12.5 AFR target)...")
    if "KF_LABAS_1" in table_map:
        build_fuel_table(session, table_map["KF_LABAS_1"], 1)
        print("  KF_LABAS_1 done")
    if "KF_LABAS_2" in table_map:
        build_fuel_table(session, table_map["KF_LABAS_2"], 1)
        print("  KF_LABAS_2 done (mirror)")
    if "KF_UESP_LA" in table_map:
        build_fuel_table(session, table_map["KF_UESP_LA"], 1, is_spool=True)
        print("  KF_UESP_LA done (spool)")

    # ── FUEL: Map 2 ──────────────────────────────────────────────────────────
    print("\n[FUEL] Map 2 (22 psi, 12.2 AFR target)...")
    for key in ["KF_LABAS_1_MAP2", "KF_LABAS_2_MAP2"]:
        if key in table_map:
            build_fuel_table(session, table_map[key], 2)
            print(f"  {key} done")
    if "KF_UESP_LA_MAP2" in table_map:
        build_fuel_table(session, table_map["KF_UESP_LA_MAP2"], 2, is_spool=True)
        print("  KF_UESP_LA_MAP2 done")

    # ── FUEL: Map 3 ──────────────────────────────────────────────────────────
    print("\n[FUEL] Map 3 (27 psi, 12.0 AFR target)...")
    for key in ["KF_LABAS_1_MAP3", "KF_LABAS_2_MAP3"]:
        if key in table_map:
            build_fuel_table(session, table_map[key], 3)
            print(f"  {key} done")
    if "KF_UESP_LA_MAP3" in table_map:
        build_fuel_table(session, table_map["KF_UESP_LA_MAP3"], 3, is_spool=True)
        print("  KF_UESP_LA_MAP3 done")

    # ── LAMBDA LIMIT RICH — must be at least as rich as 12.0 ─────────────────
    if "KF_LAMIN_H" in table_map:
        print("\n[LAMBDA LIMIT] KF_LAMIN_H — setting floor to 12.0 AFR...")
        rows, cols, grid = _rows_cols(session, table_map["KF_LAMIN_H"])
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] > 12.0:
                    # Cell is currently leaner than 12.0 — bring it down to 12.0
                    session.apply_operation(
                        table_map["KF_LAMIN_H"], "set_cells",
                        {"row_start": r, "row_end": r, "col_start": c, "col_end": c},
                        {"value": 12.0}
                    )
        print("  KF_LAMIN_H done")

    # ── COLD START enrichment ─────────────────────────────────────────────────
    for key in ["KF_ST_RKBAS_VVT", "KF_ST_RKBAS_COMF_VVT"]:
        if key in table_map:
            print(f"\n[COLD START] {key} — +17.5% fueling...")
            rows, cols, _ = _rows_cols(session, table_map[key])
            session.apply_operation(
                table_map[key], "multiply",
                {"row_start": 0, "row_end": rows - 1, "col_start": 0, "col_end": cols - 1},
                {"value": COLD_START_ENRICH_FACTOR}
            )
            print(f"  {key} done")

    # ── TIMING: Map 1 ─────────────────────────────────────────────────────────
    print("\n[TIMING] Map 1 (15 psi, +4° boost, +1.5° cruise)...")
    if "KF_ZW_PF1" in table_map:
        build_timing_table(session, table_map["KF_ZW_PF1"], TIMING_DELTA[1], TIMING_CRUISE_DELTA)
        print("  KF_ZW_PF1 done")

    # ── TIMING: Map 2 ─────────────────────────────────────────────────────────
    print("\n[TIMING] Map 2 (22 psi, +3° boost, +1.5° cruise)...")
    if "KF_ZW_PF2" in table_map:
        build_timing_table(session, table_map["KF_ZW_PF2"], TIMING_DELTA[2], TIMING_CRUISE_DELTA)
        print("  KF_ZW_PF2 done")

    # ── TIMING: Map 3 ─────────────────────────────────────────────────────────
    print("\n[TIMING] Map 3 (27 psi, +2° boost, +1.5° cruise)...")
    if "KF_ZW_PF3" in table_map:
        build_timing_table(session, table_map["KF_ZW_PF3"], TIMING_DELTA[3], TIMING_CRUISE_DELTA)
        print("  KF_ZW_PF3 done")

    # ── TIMING: Cold ─────────────────────────────────────────────────────────
    if "KF_ZW_S_PF1" in table_map:
        print("\n[TIMING] Cold timing +2°...")
        build_timing_table(session, table_map["KF_ZW_S_PF1"], TIMING_COLD_DELTA)
        print("  KF_ZW_S_PF1 done")

    # ── TIMING: Spool ─────────────────────────────────────────────────────────
    if "KF_ZW_UESP_PF1" in table_map:
        print("\n[TIMING] Spool timing +1°...")
        build_timing_table(session, table_map["KF_ZW_UESP_PF1"], TIMING_SPOOL_DELTA)
        print("  KF_ZW_UESP_PF1 done")

    # ── LIMITS: Load ceiling ──────────────────────────────────────────────────
    # Raise top cells to 130% load (raw × 0.01 = %, so 13000 raw = 130%)
    # Current stock is typically ~110% (11000 raw)
    print("\n[LIMITS] Load ceilings...")
    if "KF_RFMAXATL_KR" in table_map:
        rows, cols, grid = _rows_cols(session, table_map["KF_RFMAXATL_KR"])
        # Raise the top 3 rows (highest boost/rpm zone)
        session.apply_operation(
            table_map["KF_RFMAXATL_KR"], "set_cells",
            {"row_start": max(0, rows - 3), "row_end": rows - 1, "col_start": 0, "col_end": cols - 1},
            {"value": 130.0}
        )
        print("  KF_RFMAXATL_KR top rows → 130%")
    if "KF_RFMAXATL_SK" in table_map:
        rows, cols, grid = _rows_cols(session, table_map["KF_RFMAXATL_SK"])
        session.apply_operation(
            table_map["KF_RFMAXATL_SK"], "set_cells",
            {"row_start": max(0, rows - 3), "row_end": rows - 1, "col_start": 0, "col_end": cols - 1},
            {"value": 120.0}
        )
        print("  KF_RFMAXATL_SK top rows → 120%")

    # ── LIMITS: Torque tables ─────────────────────────────────────────────────
    print("\n[LIMITS] Torque tables → flat 900 Nm...")
    for key in ["KF_MDKMAX_GANG_MOD1", "KF_MDKMAX_GANG_MOD2"]:
        if key in table_map:
            rows, cols, _ = _rows_cols(session, table_map[key])
            session.apply_operation(
                table_map[key], "set_cells",
                {"row_start": 0, "row_end": rows - 1, "col_start": 0, "col_end": cols - 1},
                {"value": TORQUE_TARGET_NM}
            )
            print(f"  {key} → 900 Nm")


def verify(session: EditSession, table_map: dict[str, str]):
    """Run consistency checks across the modified tables."""
    print("\n" + "█"*60)
    print("  CONSISTENCY CHECKS")
    print("█"*60)
    ok = True

    # 1. Bank 1 == Bank 2
    if "KF_LABAS_1" in table_map and "KF_LABAS_2" in table_map:
        d1 = session.get_table(table_map["KF_LABAS_1"])
        d2 = session.get_table(table_map["KF_LABAS_2"])
        if d1["grid"] == d2["grid"]:
            print("  [PASS] KF_LABAS_1 == KF_LABAS_2")
        else:
            print("  [FAIL] KF_LABAS Bank mismatch!")
            ok = False

    # 2. Lambda Limit Rich is rich enough
    if "KF_LAMIN_H" in table_map:
        d = session.get_table(table_map["KF_LAMIN_H"])
        min_cell = min(d["grid"][r][c] for r in range(d["rows"]) for c in range(d["cols"]))
        if min_cell <= 12.0:
            print(f"  [PASS] KF_LAMIN_H richest cell = {min_cell:.3f} AFR (≤12.0)")
        else:
            print(f"  [WARN] KF_LAMIN_H richest cell = {min_cell:.3f} AFR — may clip fuel target of 12.0!")
            ok = False

    # 3. Torque tables flat
    for key in ["KF_MDKMAX_GANG_MOD1", "KF_MDKMAX_GANG_MOD2"]:
        if key in table_map:
            d = session.get_table(table_map[key])
            all_vals = [d["grid"][r][c] for r in range(d["rows"]) for c in range(d["cols"])]
            if all(abs(v - TORQUE_TARGET_NM) < 1.0 for v in all_vals):
                print(f"  [PASS] {key} = 900 Nm flat")
            else:
                lo, hi = min(all_vals), max(all_vals)
                print(f"  [WARN] {key} range {lo:.0f}–{hi:.0f} Nm (not fully flat)")

    print(f"\n  Overall: {'OK' if ok else 'ISSUES FOUND — review above'}")
    return ok


def main():
    audit_only = "--audit" in sys.argv

    print(f"\nLoading XDF + BIN...")
    session = load_session()
    print(f"  BIN size: {len(session.source_bin):,} bytes")

    print(f"Scanning tables...")
    table_map = find_tables(session)
    print(f"  Found {len(table_map)} relevant tables:")
    for name, tid in sorted(table_map.items()):
        print(f"    {name:<35} → {tid}")

    audit(session, table_map)

    if audit_only:
        print("\nAudit-only mode. No changes written. Re-run without --audit to apply.\n")
        return

    build_maps(session, table_map)
    ok = verify(session, table_map)

    print(f"\nExporting to {OUT_BIN}...")
    result = session.export_bin_and_log(OUT_BIN)
    print(f"  Wrote: {result.get('bin_path', OUT_BIN)}")
    log_path = result.get("log_path") or OUT_BIN.replace(".bin", ".bin.changes.json")
    if os.path.exists(log_path):
        print(f"  Change log: {log_path}")

    diff = session.diff_summary()
    edited = diff.get("changed_tables", [])
    print(f"\n  Modified {len(edited)} tables, {len(session.pending_edits)} operations applied.")
    print(f"  {'Export successful.' if ok else 'Export done — review warnings above.'}")


if __name__ == "__main__":
    main()
