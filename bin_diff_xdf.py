"""
bin_diff_xdf.py
Byte-for-byte comparison of two N55 BIN files.
For each changed region, checks if it falls inside an XDF-defined table.
Unknown regions (no XDF coverage) are flagged for further research.

Usage:
    py bin_diff_xdf.py
"""

import sys, os, struct, json
sys.path.insert(0, r"C:\Users\Michael Krymski\Documents\TunerPro Converter")

from xdf_parser import parse_xdf
from bin_reader  import _file_address

# ── Paths ────────────────────────────────────────────────────────────────────
ORIG_BIN  = r"C:\Users\Michael Krymski\Documents\N55Maps\Tools\Stock.bin"
MOD_BIN   = r"C:\Users\Michael Krymski\Downloads\Stock_N55LKS25.bin"
XDF_PATH  = r"C:\Users\Michael Krymski\Documents\N55Maps\Tools\000021571DAA01.xdf"
REPORT    = r"C:\Users\Michael Krymski\Documents\N55Maps\Tools\LKS25_diff_report.txt"

MERGE_GAP = 4   # merge diff regions separated by ≤ this many identical bytes

# ── Load files ───────────────────────────────────────────────────────────────
print("Loading files...")
orig = open(ORIG_BIN, "rb").read()
mod  = open(MOD_BIN,  "rb").read()
xdf  = open(XDF_PATH, "rb").read()
assert len(orig) == len(mod), "BIN files are different lengths!"
size = len(orig)
print(f"  BIN size: {size:,} bytes ({size/1024/1024:.2f} MB)")

# ── Parse XDF — build address coverage map ───────────────────────────────────
print("Parsing XDF...")
table_defs, _ = parse_xdf(xdf)

def table_byte_ranges(tdef):
    """Return list of (start_byte, end_byte_exclusive, axis_label) for all axes."""
    ranges = []
    base_offset   = tdef.get("base_offset", 0)
    base_subtract = tdef.get("base_subtract", False)

    for axis_key in ("z_axis", "x_axis", "y_axis"):
        axis = tdef.get(axis_key)
        if not axis:
            continue
        emb = axis.get("embedded")
        if not emb:
            continue
        xdf_addr   = emb["address"]
        size_bits  = emb["element_size_bits"]
        size_bytes = max(size_bits // 8, 1)
        rows = max(emb.get("row_count", 1), 1)
        cols = max(emb.get("col_count", 1), 1)
        n_elements = rows * cols

        file_addr = (xdf_addr - base_offset) if base_subtract else (xdf_addr + base_offset)
        if file_addr < 0 or file_addr >= size:
            continue

        # Stride-aware length estimate (conservative: use element-packed layout)
        major_stride_b = emb.get("major_stride_bits", 0)
        minor_stride_b = emb.get("minor_stride_bits", 0)
        col_major = major_stride_b < 0

        natural_minor = size_bytes
        natural_major = (rows * size_bytes) if col_major else (cols * size_bytes)

        minor = natural_minor if minor_stride_b == 0 else max(abs(minor_stride_b)//8, natural_minor)
        if major_stride_b == 0:
            major = natural_major
        else:
            exp = abs(major_stride_b)//8
            major = exp if exp >= natural_major else natural_major

        if col_major:
            total_bytes = cols * major + (rows-1) * minor if cols > 0 else size_bytes
        else:
            total_bytes = rows * major + (cols-1) * minor if rows > 0 else size_bytes

        # Fallback: just use packed size
        total_bytes = max(total_bytes, n_elements * size_bytes)

        end = min(file_addr + total_bytes, size)
        ranges.append((file_addr, end, axis_key))
    return ranges

# Build a lookup: for each byte offset, which table(s) cover it?
# We store sparse coverage as sorted list of (start, end, table_title, axis)
print("Building XDF address coverage map...")
xdf_regions = []   # list of dicts
for tdef in table_defs:
    if tdef.get("is_autogen"):
        continue
    title = tdef.get("title", "?")
    for (start, end, axis_key) in table_byte_ranges(tdef):
        if end > start:
            xdf_regions.append({
                "start": start,
                "end":   end,
                "title": title,
                "axis":  axis_key,
            })

xdf_regions.sort(key=lambda r: r["start"])
print(f"  {len(xdf_regions):,} XDF regions mapped")

# Fast point-query: which XDF region covers byte offset b?
def find_xdf_coverage(addr):
    """Binary search into xdf_regions; return first matching region or None."""
    lo, hi = 0, len(xdf_regions) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        r = xdf_regions[mid]
        if addr < r["start"]:
            hi = mid - 1
        elif addr >= r["end"]:
            lo = mid + 1
        else:
            return r
    return None

# ── Byte diff → run-length encoded changed regions ───────────────────────────
print("Diffing bytes...")
diff_runs = []   # (start, end_excl)
i = 0
while i < size:
    if orig[i] != mod[i]:
        j = i + 1
        while j < size and mod[j] != orig[j]:
            j += 1
        diff_runs.append((i, j))
        i = j
    else:
        i += 1

# Merge nearby runs
merged = []
for run in diff_runs:
    if merged and run[0] - merged[-1][1] <= MERGE_GAP:
        merged[-1] = (merged[-1][0], run[1])
    else:
        merged.append(list(run))

print(f"  {len(diff_runs)} raw diff runs -> {len(merged)} merged regions")
print(f"  Total changed bytes: {sum(b-a for a,b in diff_runs):,}")

# ── Classify each region ─────────────────────────────────────────────────────
results = []
for (start, end) in merged:
    # Check multiple sample points inside the region for XDF coverage
    covered = {}
    for probe in range(start, end):
        r = find_xdf_coverage(probe)
        if r:
            key = r["title"]
            if key not in covered:
                covered[key] = r

    orig_bytes = orig[start:end]
    mod_bytes  = mod[start:end]

    # Build a hex summary (first 16 bytes each side)
    def hexstr(b, n=16):
        h = b[:n].hex()
        return " ".join(h[i:i+2] for i in range(0, len(h), 2)) + (" ..." if len(b) > n else "")

    results.append({
        "start": start,
        "end":   end,
        "len":   end - start,
        "orig_hex": hexstr(orig_bytes),
        "mod_hex":  hexstr(mod_bytes),
        "xdf_tables": list(covered.values()),
        "known": bool(covered),
    })

known   = [r for r in results if r["known"]]
unknown = [r for r in results if not r["known"]]

print(f"\n  Known (in XDF): {len(known)} regions")
print(f"  UNKNOWN (not in XDF): {len(unknown)} regions")

# ── Interpret scalar/simple changes ─────────────────────────────────────────
def try_interpret(orig_b, mod_b):
    """Try common data widths and return human-readable guess."""
    hints = []
    n = len(orig_b)
    for (fmt, label, conv) in [
        ("<H", "u16 LoHi", lambda x: x),
        (">H", "u16 HiLo", lambda x: x),
        ("<h", "i16 LoHi", lambda x: x),
        ("<f", "f32 LE",   lambda x: round(x, 4)),
    ]:
        sz = struct.calcsize(fmt)
        if n >= sz:
            try:
                ov = struct.unpack_from(fmt, orig_b)[0]
                mv = struct.unpack_from(fmt, mod_b)[0]
                hints.append(f"{label}: {ov} -> {mv}")
            except Exception:
                pass
    if n == 1:
        hints.append(f"u8: {orig_b[0]} -> {mod_b[0]}")
    return " | ".join(hints[:3]) if hints else ""

# ── Write report ─────────────────────────────────────────────────────────────
lines = []
def w(*args): lines.append(" ".join(str(a) for a in args))

w("=" * 72)
w("N55 WinOLS Diff Report")
w(f"Original : {ORIG_BIN}")
w(f"Modified : {MOD_BIN}")
w(f"XDF      : {XDF_PATH}")
w("=" * 72)
w(f"\nTotal changed regions : {len(results)}")
w(f"  XDF-mapped (known)  : {len(known)}")
w(f"  Unmapped (unknown)  : {len(unknown)}")
w(f"Total changed bytes   : {sum(r['len'] for r in results):,}")
w()

w("=" * 72)
w("SECTION 1 — CHANGES IN XDF-DEFINED TABLES")
w("=" * 72)
for r in known:
    w(f"\n  [0x{r['start']:06X}–0x{r['end']-1:06X}]  {r['len']} bytes")
    for t in r["xdf_tables"]:
        w(f"    XDF: {t['title']}  ({t['axis']})")
    w(f"    ORIG: {r['orig_hex']}")
    w(f"    MOD : {r['mod_hex']}")
    interp = try_interpret(orig[r["start"]:r["end"]], mod[r["start"]:r["end"]])
    if interp:
        w(f"    INTERP: {interp}")

w()
w("=" * 72)
w("SECTION 2 — UNKNOWN CHANGES (not in any XDF table)")
w("=" * 72)
for r in unknown:
    w(f"\n  [0x{r['start']:06X}–0x{r['end']-1:06X}]  {r['len']} bytes")
    w(f"    ORIG: {r['orig_hex']}")
    w(f"    MOD : {r['mod_hex']}")
    interp = try_interpret(orig[r["start"]:r["end"]], mod[r["start"]:r["end"]])
    if interp:
        w(f"    INTERP: {interp}")

# Write file
report_text = "\n".join(lines)
with open(REPORT, "w", encoding="utf-8") as f:
    f.write(report_text)
print(f"\nReport written to: {REPORT}")

# Also dump unknown addresses as JSON for web research
unknown_addrs = [{"addr_hex": f"0x{r['start']:06X}", "addr_dec": r["start"],
                  "len": r["len"],
                  "orig_hex": r["orig_hex"], "mod_hex": r["mod_hex"],
                  "interp": try_interpret(orig[r["start"]:r["end"]], mod[r["start"]:r["end"]])}
                 for r in unknown]
json_path = REPORT.replace(".txt", "_unknown.json")
with open(json_path, "w") as f:
    json.dump(unknown_addrs, f, indent=2)
print(f"Unknown addresses JSON: {json_path}")

# Console summary
print()
print("UNKNOWN REGIONS (need research):")
for r in unknown:
    interp = try_interpret(orig[r["start"]:r["end"]], mod[r["start"]:r["end"]])
    print(f"  0x{r['start']:06X}  {r['len']:4d}B  {interp}")
