"""
merge_lks25_hpfp.py
Direct byte-level merge of the 9 HPFP/MSV changes from Stock_N55LKS25.bin
into E85v2.bin, producing E85v2_hpfp.bin.

These are the exact 9 byte ranges the WinOLS tuner changed. Copying them
directly bypasses any XDF address alignment issues.

Usage:
    py merge_lks25_hpfp.py
"""

import sys, struct, shutil, os

DONOR  = r"C:\Users\Michael Krymski\Downloads\Stock_N55LKS25.bin"
BASE   = r"C:\Users\Michael Krymski\Documents\N55Maps\E85v2.bin"
OUTPUT = r"C:\Users\Michael Krymski\Documents\N55Maps\E85v2_hpfp.bin"

# The 9 exact byte ranges confirmed by diff analysis.
# Format: (start_addr, length_bytes, description)
HPFP_REGIONS = [
    (0x1C9F52,  2,  "MSV Maximum Delivery Angle"),
    (0x1CD46C,  8,  "Max relative fuel mass for HPFP plausibility"),
    (0x1D0B4C, 12,  "HPFP P-Factor + I-Factor PID gains"),
    (0x1D4070,  8,  "MSV Opening Delay (Battery Voltage)"),
    (0x1D4224,  1,  "MSV Minimum Hold Current"),
    (0x1D4235, 30,  "MSV Pull-in Current Lower Limit"),
    (0x1D427E,  1,  "MfVD Codeword (bit 0 cleared)"),
    (0x1D6CE0, 95,  "MSV Feedforward Offset"),
    (0x1D6D66, 16,  "MSV Feedforward Gain"),
]

# ── Load files ────────────────────────────────────────────────────────────────
donor = bytearray(open(DONOR, "rb").read())
base  = bytearray(open(BASE,  "rb").read())

assert len(donor) == len(base), "BIN size mismatch!"

print(f"Donor : {DONOR}")
print(f"Base  : {BASE}")
print(f"Output: {OUTPUT}")
print()

# ── Apply each region ─────────────────────────────────────────────────────────
total_bytes = 0
for (addr, length, desc) in HPFP_REGIONS:
    donor_bytes = donor[addr : addr + length]
    base_bytes  = base[addr  : addr + length]

    changed = sum(1 for a, b in zip(donor_bytes, base_bytes) if a != b)

    base[addr : addr + length] = donor_bytes
    total_bytes += length

    status = f"({changed}/{length} bytes changed)" if changed else "(already matched)"
    print(f"  [0x{addr:06X}]  {length:3d}B  {desc}")
    print(f"             base : {bytes(base_bytes)[:8].hex()}")
    print(f"             donor: {donor_bytes[:8].hex()}  {status}")

# ── Verify ────────────────────────────────────────────────────────────────────
print()
print("Verifying all HPFP regions match donor...")
all_ok = True
for (addr, length, desc) in HPFP_REGIONS:
    if base[addr:addr+length] == donor[addr:addr+length]:
        print(f"  [PASS] {desc}")
    else:
        print(f"  [FAIL] {desc}  <-- mismatch!")
        all_ok = False

# ── Write output ──────────────────────────────────────────────────────────────
print()
if all_ok:
    with open(OUTPUT, "wb") as f:
        f.write(base)
    print(f"Written: {OUTPUT}")
    print(f"Total bytes patched: {total_bytes}")
    print()
    print("This file contains:")
    print("  - All E85v2.bin content (your E85 tune in progress)")
    print("  - + LKS25 HPFP/MSV recalibration for Dorch DS25 + 38% lift kit")
    print()
    print("Next step: use E85v2_hpfp.bin as your base for build_e85_maps.py")
else:
    print("Verification failed — output NOT written. Check errors above.")
    sys.exit(1)
