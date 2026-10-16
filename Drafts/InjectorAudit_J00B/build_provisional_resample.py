"""Build the explicitly requested provisional review copy; never edit inputs.

Uses only the Python standard library. Run from any directory. Output files
are created beside this script under Resampling_PROVISIONAL. Existing outputs
are accepted only when their contents are identical.
"""

from bisect import bisect_right
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import struct


WORKSPACE = Path(__file__).resolve().parents[2]
SOURCE = WORKSPACE / "FlexFuel/Revisions/FlexFuelv4(FuelScalar-93).bin"
STOCK = Path.home() / "Downloads/WBA1J9C5XGV696132_000021571DAA01.bin"
DONOR_ROOT = Path.home() / "Documents/BMW/MEVD 17.2.H/N63-F"
OUT = Path(__file__).resolve().parent / "Resampling_PROVISIONAL"
TABLE = 0x1D19EE
AXIS = 0x1D1A94
COUNT = 20
SOURCE_HASH = "d9cf1757971ab83804d532ff9eb46c1ce2c3f5e4bbb77a5090698905614dac14"
STOCK_HASH = "29913adc8a323e58d9ee4064f163fcb18c8894a7c8d32ec2d41a80735e4fd0a2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_hex(path):
    memory, base, eof = {}, 0, False
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        assert line.startswith(":"), (path, line_number)
        record = bytes.fromhex(line[1:])
        n, kind = record[0], record[3]
        assert len(record) == n + 5 and sum(record) % 256 == 0
        offset = int.from_bytes(record[1:3], "big")
        payload = record[4:4+n]
        if kind == 0:
            for i, value in enumerate(payload):
                address = base + offset + i
                assert address not in memory or memory[address] == value
                memory[address] = value
        elif kind == 1:
            eof = True
        elif kind == 2:
            base = int.from_bytes(payload, "big") << 4
        elif kind == 4:
            base = int.from_bytes(payload, "big") << 16
        else:
            assert kind in (3, 5), kind
    assert eof
    return memory


def get_bytes(memory, address, length):
    for alias in (address, address ^ 0x20000000, address & 0x0FFFFFFF):
        if all(alias + i in memory for i in range(length)):
            return bytes(memory[alias+i] for i in range(length))
    raise ValueError(f"Missing HEX address {address:#x}")


def donor(identifier):
    candidates = [p for p in DONOR_ROOT.rglob("*master.a2l") if identifier in str(p)]
    assert len(candidates) == 1
    a2l = candidates[0]
    definition = a2l.read_text(errors="replace")
    value_address = int(re.search(
        r'/begin CHARACTERISTIC\s+KLTIKRPR\s+"[^"\n]*"\s+CURVE\s+(0x\w+)',
        definition)[1], 16)
    axis_address = int(re.search(
        r'/begin AXIS_PTS\s+SDP20ESUW\s+"[^"\n]*"\s+(0x\w+)',
        definition)[1], 16)
    candidates = [p for p in a2l.parent.glob("*.hex") if "_Data" not in p.name]
    assert len(candidates) == 1
    hex_path = candidates[0]
    memory = read_hex(hex_path)
    assert struct.unpack("<H", get_bytes(memory, axis_address, 2))[0] == COUNT
    x = list(struct.unpack("<20H", get_bytes(memory, axis_address+2, 40)))
    y = list(struct.unpack("<20H", get_bytes(memory, value_address, 40)))
    return x, y, {
        "identifier": identifier, "a2l": str(a2l), "a2l_sha256": sha(a2l.read_bytes()),
        "hex": str(hex_path), "hex_sha256": sha(hex_path.read_bytes()),
        "factor_address": hex(value_address), "axis_record_address": hex(axis_address),
    }


def interpolate(x, y, pressure):
    pressure = F(pressure)
    assert x[0] <= pressure <= x[-1], pressure
    i = min(max(bisect_right(x, pressure)-1, 0), len(x)-2)
    return F(y[i]) + (pressure-x[i]) * F(y[i+1]-y[i], x[i+1]-x[i])


def nearest_unsigned(value):
    assert value >= 0
    rounded = (2*value.numerator + value.denominator) // (2*value.denominator)
    assert 0 <= rounded <= 65535
    return rounded


def write_once(path, data):
    if path.exists():
        assert path.read_bytes() == data, f"Refusing to overwrite different output: {path}"
    else:
        path.write_bytes(data)


def main():
    source, stock = SOURCE.read_bytes(), STOCK.read_bytes()
    assert sha(source) == SOURCE_HASH and sha(stock) == STOCK_HASH
    assert len(source) == len(stock) == 4*1024*1024
    dx, dy, donor_one = donor("8AC4543B")
    dx2, dy2, donor_two = donor("8AC4600B")
    assert (dx, dy) == (dx2, dy2), "Donors do not agree"
    x = list(struct.unpack_from("<20H", source, AXIS))
    before = list(struct.unpack_from("<20H", source, TABLE))
    stock_x = list(struct.unpack_from("<20H", stock, AXIS))
    stock_y = list(struct.unpack_from("<20H", stock, TABLE))
    assert x == stock_x and before == dy
    assert all(a < b for a, b in zip(x, x[1:]))
    assert all(a < b for a, b in zip(dx, dx[1:]))
    assert (dx[0], dx[-1]) == (800, 40000)  # 4 and 200 bar, raw pressure units

    proposed, rows = [], []
    for i, pressure in enumerate(x):
        if pressure < dx[0]:
            exact = F(dy[0]*stock_y[i]) / interpolate(stock_x, stock_y, dx[0])
            method = "assumed: stock shape normalized to donor at 4 bar"
        elif pressure > dx[-1]:
            exact = F(dy[-1]*stock_y[i]) / interpolate(stock_x, stock_y, dx[-1])
            method = "assumed: stock shape normalized to donor at 200 bar"
        else:
            exact = interpolate(dx, dy, pressure)
            method = "linear interpolation within donor coverage"
        raw = nearest_unsigned(exact)
        assert abs(F(raw)-exact) <= F(1, 2)
        proposed.append(raw)
        rows.append({
            "index_1_based": i+1, "offset": hex(TABLE+2*i),
            "differential_pressure_bar": pressure/200,
            "before_raw": before[i], "proposed_raw": raw,
            "before_factor": before[i]/4096, "proposed_factor": raw/4096,
            "change_percent": (raw/before[i]-1)*100,
            "method": method,
        })
    assert all(a >= b for a, b in zip(proposed, proposed[1:])), "Non-monotonic result"

    # Both functions are piecewise linear; extrema of their ratio occur at
    # the union of their breakpoints. Include the donor domain boundaries.
    checkpoints = sorted({*dx, *(v for v in x if dx[0] <= v <= dx[-1])})
    residuals = []
    for pressure in checkpoints:
        reference = interpolate(dx, dy, pressure)
        candidate = interpolate(x, proposed, pressure)
        current = interpolate(x, before, pressure)
        residuals.append({"differential_pressure_bar": pressure/200,
                          "candidate_vs_donor_percent": float((candidate/reference-1)*100),
                          "current_vs_donor_percent": float((current/reference-1)*100)})
    worst = max(residuals, key=lambda r: abs(r["candidate_vs_donor_percent"]))
    worst_before = max(residuals, key=lambda r: abs(r["current_vs_donor_percent"]))
    comparison = []
    for pressure_bar in (4, 10, 25, 50, 100, 150, 180, 200, 250):
        pressure = pressure_bar*200
        reference = interpolate(dx, dy, pressure) if dx[0] <= pressure <= dx[-1] else None
        result = interpolate(x, proposed, pressure)
        comparison.append({"differential_pressure_bar": pressure_bar,
                           "current_factor": float(interpolate(x, before, pressure)/4096),
                           "proposed_factor": float(result/4096),
                           "donor_factor": float(reference/4096) if reference is not None else None,
                           "candidate_vs_donor_percent": float((result/reference-1)*100) if reference is not None else None})

    candidate = bytearray(source)
    struct.pack_into("<20H", candidate, TABLE, *proposed)
    candidate = bytes(candidate)
    changes = [i for i, (a, b) in enumerate(zip(source, candidate)) if a != b]
    assert changes and all(TABLE <= i < TABLE+40 for i in changes)
    assert source[:TABLE] == candidate[:TABLE]
    assert source[TABLE+40:] == candidate[TABLE+40:]
    assert candidate[AXIS:AXIS+40] == source[AXIS:AXIS+40]
    assert list(struct.unpack_from("<20H", candidate, TABLE)) == proposed

    filename = "FlexFuelv4_KLTIKRPR_resampled_PROVISIONAL.bin"
    manifest = {
        "status": "PROVISIONAL REVIEW COPY; donor hardware applicability unconfirmed; not validated for flashing",
        "base": str(SOURCE), "base_sha256": sha(source),
        "stock_reference": str(STOCK), "stock_sha256": sha(stock),
        "candidate_filename": filename, "candidate_sha256": sha(candidate),
        "donors": [donor_one, donor_two],
        "scope": "KLTIKRPR output array only, 20 unsigned little-endian 16-bit values",
        "pressure_input": "rail-to-combustion-chamber differential pressure",
        "pressure_units": "raw / 200 = bar", "factor_units": "raw / 4096",
        "rounding": "nearest representable unsigned integer, exact half rounded upward",
        "endpoint_policy": "N55 stock shape outside 4–200 bar, normalized to donor at each coverage boundary",
        "checksum_status": "ECU checksums/signatures were not recalculated or validated",
        "changed_bytes": len(changes), "changed_byte_offsets": [hex(i) for i in changes],
        "changed_words": sum(a != b for a, b in zip(before, proposed)),
        "rows": rows, "comparison": comparison, "residuals_at_all_breakpoints": residuals,
        "worst_candidate_residual_within_4_200_bar": worst,
        "worst_current_residual_within_4_200_bar": worst_before,
        "preserved": "all bytes outside 0x1D19EE–0x1D1A15 inclusive; shared axis, delay curve, scalar, MK2TE, KLHDEV, KLTELIN, switches and monitors",
    }

    report = ["# Provisional KLTIKRPR resampling review", "",
              "This is the separate review copy requested by the user. Donor hardware applicability remains unconfirmed. It is not a validated flash-ready calibration.", "",
              f"Base: `{SOURCE.name}`. Candidate: `{filename}`.",
              f"Only {len(changes)} bytes changed, in all 20 KLTIKRPR output words at `0x1D19EE`. Every byte outside that 40-byte array is identical to the base.", "",
              "## Method and endpoint assumptions", "",
              "Both 8AC4543B and 8AC4600B master A2L/HEX pairs were decoded independently. Their pressure axes and factor arrays agree exactly. The base output array equals their donor output array before resampling.", "",
              "Within donor coverage (4–200 bar differential pressure), interpolate the donor curve linearly at each retained N55 axis point and round to the nearest representable factor (1/4096).", "",
              "For the three axis points below 4 bar, use donor(4) × stock_N55(p) / stock_N55(4). For the 250-bar point, use donor(200) × stock_N55(250) / stock_N55(200). Stock values at coverage boundaries are themselves linearly interpolated on the stock axis.", "",
              "This preserves the stock N55 curve's relative shape outside donor coverage, anchored to the donor at each boundary. It is an explicit modeling assumption, not donor data or verified injector characterization. The supplied HEX does not establish donor behavior at those four points.", "",
              "The extended reference is continuous at 4 and 200 bar. Its representation on the retained, differently spaced N55 axis is an approximation; the reconstructed ECU curve does not pass through every donor knot or necessarily exactly through those boundary anchors.", "",
              "## Values", "",
              "| Differential pressure (bar) | Existing factor | Proposed factor | Proposed raw | Basis |",
              "|---:|---:|---:|---:|---|"]
    for row in rows:
        basis = "Endpoint assumption" if row["method"].startswith("assumed") else "Donor interpolation"
        report.append(f'| {row["differential_pressure_bar"]:g} | {row["before_factor"]:.8f} | {row["proposed_factor"]:.8f} | {row["proposed_raw"]} | {basis} |')
    report += ["", "## Reconstructed-curve comparison", "",
               "These compare one correction factor, not final fueling or lambda error.", "",
               "| Differential pressure (bar) | Existing factor | Proposed factor | Donor factor | Proposed vs donor |",
               "|---:|---:|---:|---:|---:|"]
    for row in comparison:
        donor_text = f'{row["donor_factor"]:.8f}' if row["donor_factor"] is not None else "Outside coverage"
        delta = f'{row["candidate_vs_donor_percent"]:+.4f}%' if row["candidate_vs_donor_percent"] is not None else "Unverified"
        report.append(f'| {row["differential_pressure_bar"]:g} | {row["current_factor"]:.8f} | {row["proposed_factor"]:.8f} | {donor_text} | {delta} |')
    report += ["", f'Maximum absolute candidate/reference relative deviation within 4–200 bar is {abs(worst["candidate_vs_donor_percent"]):.4f}% at {worst["differential_pressure_bar"]:g} bar. This includes axis-spacing/interpolation effects and integer quantization. Extrema were checked at the union of both curves\' breakpoints.', "",
               "## Verification and limits", "",
               "- Shared N55 axis and pressure-dependent delay outputs remain byte-identical.",
               "- MK2TE, KLTELIN, KLHDEV, scalar maps, selector bytes and monitor parameters remain byte-identical.",
               "- Proposed outputs are monotonic decreasing and fit unsigned 16-bit storage.",
               "- Input hashes, output hash, every changed byte offset, exact raw words and donor provenance are recorded in `manifest.json`.",
               "- ECU checksums/signatures were not recalculated or validated. This copy must not be described as ready to flash.",
               "- This corrects the donor indexing in the stated approximation; it does not validate the full injector model or establish a fix for richness or 1F0525.", "",
               f'Base SHA-256: `{sha(source)}`', f'Candidate SHA-256: `{sha(candidate)}`', ""]
    OUT.mkdir(exist_ok=True)
    write_once(OUT/filename, candidate)
    write_once(OUT/"manifest.json", (json.dumps(manifest, indent=2)+"\n").encode())
    write_once(OUT/"review.md", "\n".join(report).encode())
    write_once(OUT/"KLTIKRPR_raw_words.txt", (" ".join(map(str, proposed))+"\n").encode())
    assert sha(SOURCE.read_bytes()) == SOURCE_HASH and sha(STOCK.read_bytes()) == STOCK_HASH
    print(json.dumps({"output_directory": str(OUT), "candidate_sha256": sha(candidate),
                      "changed_bytes": len(changes), "changed_words": manifest["changed_words"],
                      "worst_residual": worst, "comparison": comparison}, indent=2))


if __name__ == "__main__":
    main()
