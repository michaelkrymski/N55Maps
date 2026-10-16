"""Read the WinOLS CSV and compare selected local mappings without editing inputs."""
import base64
import csv
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CSV = ROOT / "Tools/WinOLS (BMW 2er (Original) - 544859).csv"
DRAFT = ROOT / "Drafts/FlexFuelDrafts.json"
STOCK = Path.home() / "Downloads/WBA1J9C5XGV696132_000021571DAA01.bin"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode_values(data, row, address):
    count = int(row["Columns"]) * int(row["Rows"])
    width = {"eByte": 1, "eLoHi": 2, "eLoHiLoHi": 4}[row["DataOrg"]]
    factor, offset = float(row["Fieldvalues.Factor"]), float(row["Fieldvalues.Offset"])
    values = [int.from_bytes(data[address+i*width:address+(i+1)*width], "little",
                             signed=row["bSigned"] == "1") * factor + offset
              for i in range(count)]
    return values, width


def physical_csv_values(row):
    values = [float(x) for x in row["Fieldvalues.Values"].split()]
    columns, rows = int(row["Columns"]), int(row["Rows"])
    assert len(values) == columns * rows
    if row["Type"] == "eZweiInv":
        return [values[c*rows+r] for r in range(rows) for c in range(columns)]
    return values


def main():
    csv_bytes, draft_bytes, stock = CSV.read_bytes(), DRAFT.read_bytes(), STOCK.read_bytes()
    payload = json.loads(draft_bytes)
    draft = base64.b64decode(payload["working_bin_b64"])
    entries = list(csv.DictReader(csv_bytes.decode("cp1252").splitlines(), delimiter=";"))
    by_symbol = {}
    for line, row in enumerate(entries, 2):
        row = {**row, "source_line": line}
        by_symbol.setdefault(row["IdName"], row)

    # These are separately checked local mappings. FRMAX/FRMIN have a different
    # shift from the preceding injector block and were located by raw fingerprints.
    selected = [
        ("CWKLTELIN", 0x1D16D5, "code-referenced selector"),
        ("CWBMWINJAD", 0x1D16D4, "code-referenced correction configuration"),
        ("MK2TE", 0x1D1A8C, "code-referenced conversion factor"),
        ("KLTELIN", 0x1D19B2, "code-referenced selected curve outputs"),
        ("InjVvG_tiIvsCvo_T", 0x1D180E, "inverse curve; local layout and value fingerprint"),
        ("FKKVS", 0x1D1702, "code-referenced map outputs"),
        ("KLTIKRTP", 0x1D1A24, "pause correction; local layout and value fingerprint"),
        ("KLTIKRTPB", 0x1D1A3E, "ballistic pause correction; local layout and value fingerprint"),
        ("InjSys_tiOpenInjCvo_M", 0x1D1582, "CVO opening-time model; local layout and value fingerprint"),
        ("IVGdiCtl_CvoAdpn_DftVal_tantot_GM", 0x1D144C, "code-referenced default opening-delay table"),
        ("InjVvG_CvoAdpn_enable_dti_C", 0x1D13D8, "code-referenced CVO correction enable"),
        ("IVGdiCtl_CvoAdpn_enable_OnlineCtrl_C", 0x1D1475, "code-referenced online control enable"),
        ("IVGdiCtl_CvoAdpn_enable_ReAdpn_C", 0x1D1476, "code-referenced readaptation gate"),
        ("IVGdiCtl_CvoAdpn_Lim_dtiTotNeg_C", 0x1D1484, "CVO block lower total correction bound"),
        ("IVGdiCtl_CvoAdpn_Lim_dtiTotPos_C", 0x1D1486, "CVO block upper total correction bound"),
        ("KL_INJAD_KLTIKRPR", 0x194B48, "separate adaptation curve; local layout and value fingerprint"),
        ("KL_INJAD_KLHDEV", 0x194BC2, "separate adaptation curve; local layout and value fingerprint"),
        ("KL_INJAD_KLFDTFUEL", 0x194C2C, "separate adaptation density curve; local layout and value fingerprint"),
        ("S_LRADAP_MDRK", 0x194A83, "BMW learned-trim incorporation setting; local value candidate"),
        ("KFFKKORRF_UM", 0x1B8526, "code-selected 8x8 monitor correction outputs"),
        ("KFRKMIN_UM", 0x1B8578, "monitor minimum-mass map; local layout and value fingerprint"),
        ("MoFAirFl_rkCorFacMst_MAP", 0x1B8685, "alternate 16x16 monitor correction outputs"),
        ("KLFRAMX_UM", 0x1B8660, "monitor adaptation allowance"),
        ("FRMAX", 0x1D3A56, "separately located raw-value fingerprint"),
        ("FRMIN", 0x1D3A58, "separately located raw-value fingerprint"),
    ]
    checks = []
    for name, address, basis in selected:
        row = by_symbol[name]
        original_values, width = decode_values(stock, row, address)
        current_values, _ = decode_values(draft, row, address)
        reference = physical_csv_values(row)
        tolerance = .5 * 10 ** (-max(int(row["Precision"]), 0)) + 1e-6
        matches = sum(abs(a-b) <= tolerance for a, b in zip(original_values, reference))
        length = len(original_values)*width
        checks.append({"symbol": name, "description": row["Name"],
                       "source_line": row["source_line"],
                       "ols_output_address": row["Fieldvalues.StartAddr"],
                       "j00b_output_address": hex(address), "mapping_basis": basis,
                       "count": len(original_values), "stock_values_matching_csv": matches,
                       "stock_range": [min(original_values), max(original_values)],
                       "draft_range": [min(current_values), max(current_values)],
                       "stock_to_draft_changed_bytes": sum(a != b for a, b in
                           zip(stock[address:address+length], draft[address:address+length]))})

    useful = []
    for row in by_symbol.values():
        symbol, folder = row["IdName"], row["FolderName"]
        group = None
        if folder.startswith("InjDDGdi_icl:"):
            group = "selected injector calculation and pause corrections"
        elif folder.startswith("IVGdiCtl_CvoAdpn:"):
            group = "CVO learned opening-delay and correction model"
        elif folder.startswith("es_injad:"):
            group = "separate injector-adaptation model"
        elif folder.startswith("es_md_rkrf_h:"):
            group = "normal fuel mass, learned trim and transient fuel"
        elif folder.startswith("MoFAirFl_MixCtl:"):
            group = "mixture monitor"
        elif re.search(r"^FRM(?:AX|IN)|^KF_FLRADAP_|^InjSys_tiOpenInjCvo_M$", symbol):
            group = "additional correction limits and opening-time model"
        if group:
            useful.append({"group": group, **row})

    # The checked map's raw temperature bytes reproduce the exported pressure
    # values, and its raw pressure bytes reproduce the exported temperature
    # values. Record both the mismatch and the proper J00B axis reconstruction.
    pressure_raw = list(draft[0x1D1B11:0x1D1B16])
    temperature_raw = list(draft[0x1D1B1E:0x1D1B22])
    axis_example = {
        "symbol": "IVGdiCtl_CvoAdpn_DftVal_tantot_GM",
        "csv_axis_x_values": by_symbol["IVGdiCtl_CvoAdpn_DftVal_tantot_GM"]["AxisX.Values"],
        "csv_axis_y_values": by_symbol["IVGdiCtl_CvoAdpn_DftVal_tantot_GM"]["AxisY.Values"],
        "j00b_pressure_axis_raw": pressure_raw,
        "j00b_temperature_axis_raw": temperature_raw,
        "j00b_pressure_bar": [x*1.28 for x in pressure_raw],
        "j00b_temperature_celsius": [x*.75-48 for x in temperature_raw],
        "exported_x_reproduced_from_wrong_raw_temperature": [x*.128 for x in temperature_raw],
        "exported_y_reproduced_from_wrong_raw_pressure": [x*.75-48 for x in pressure_raw],
    }
    summary = {
        "source_csv": str(CSV), "source_csv_sha256": digest(csv_bytes),
        "row_count": len(entries),
        "unique_nonempty_symbols": len({r["IdName"] for r in entries if r["IdName"]}),
        "source_encoding": "cp1252", "delimiter": ";",
        "draft_sha256": digest(draft_bytes), "working_bin_sha256": digest(draft),
        "useful_unique_definitions": len(useful), "checked_local_mappings": checks,
        "axis_export_mismatch_example": axis_example,
        "monitor": {"a9_entry_offset": "0x50", "default_group": "0xA01B84BA",
                    "master_slave_configuration_address": "0x1B8468",
                    "master_slave_configuration": draft[0x1B8468],
                    "selected_curve": "KFFKKORRF_UM 8x8 on located bank-1 branch",
                    "FRKMAX_UM": draft[0x1B84BF]/128,
                    "FRKMIN_UM": draft[0x1B84C0]/128,
                    "RKO_UM_relative_mass_units": draft[0x1B88AD]*.75,
                    "MoF_ctGkc_C": draft[0x1B88A7], "MoF_ctRlc_C": draft[0x1B88A8]},
    }
    (OUT/"ols_useful_definitions.json").write_text(json.dumps(useful, indent=2)+"\n")
    (OUT/"ols_review_checks.json").write_text(json.dumps(summary, indent=2)+"\n")
    assert digest(CSV.read_bytes()) == digest(csv_bytes)
    assert digest(DRAFT.read_bytes()) == digest(draft_bytes)
    print(json.dumps({"rows": len(entries), "useful_unique_definitions": len(useful),
                      "checks": [{k: x[k] for k in ("symbol", "stock_values_matching_csv", "count", "stock_to_draft_changed_bytes")}
                                 for x in checks], "axis_example": axis_example}, indent=2))


if __name__ == "__main__":
    main()
