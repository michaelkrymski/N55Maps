# J00B injector calculation: read-only static audit

Date: 2026-10-16. No calibration, XDF, injector coding, adaptation or vehicle settings were changed. Resampling is deferred.

## Main finding

The available BIN contains J00B identifiers and relevant executable code. The older 75Q2G00B A2L can be used to name this particular injector-calibration block after checking its layout against the J00B instructions. It is not a matching J00B definition set, and the offset established here must not be applied globally.

The XDF has an apparent CWKLTELIN address error. It points to file offset `0x1D1ADB`, which contains zero. The located J00B injector-duration routine instead reads the selector at `0x1D16D5`, which contains **1** in Stock.bin, v5, v6 and FlexFuelv4.

In that routine, a nonzero selector chooses **KLTELIN**. Zero chooses the **KLHDEV additive-correction branch**. Consequently, the stored calibrations select KLTELIN in this path. The earlier statement that the tune selects KLHDEV because the XDF displays zero must be withdrawn.

This is a static result for the supplied files and the located routine. It is not a live ECU execution trace, proof of the contents actually flashed by MHD, or a proof that no other code path can reference KLHDEV.

## Source and executable coverage

Primary source: `E85/Revisions/E85v6(InjectorsFix).bin`, 4,194,304 bytes.

SHA-256: `29f19577dfd6054637879e7b121af305b3eec308c1496f3c92b3012e0f81e821`.

Repeated identity strings read `75Q9J00B`, including file offsets `0x17FB22`, `0x1FFB22`, `0x1FFE01`, and `0x3FFDAA`. Identity strings alone do not establish code coverage. Relevant coherent TriCore instructions, cross-function calls, calibration pointer loads and curve lookups were also located.

The older A2L describes code segments at `0x80020000` and `0x80220000`, and data at `0x80180000`. The located J00B routines use the corresponding flash mapping, `address = 0x80000000 + file offset`.

The following examined byte ranges are identical in v5, v6, FlexFuelv4 and the vehicle-named reference `Downloads/WBA1J9C5XGV696132_000021571DAA01.bin`:

| File range, end exclusive | Purpose | SHA-256 in v6 |
|---|---|---|
| `0x2F2330–0x2F2F92` | Differential pressure and injector-duration routines | `a2f416b0b90cfab23333396ca4cd50f34c5e47a0e2068d823a4ef8a3b413b86a` |
| `0x0A4080–0x0A417C` | Related inverse/reference calculation | `e78222bc4ac367d1d8ea55f27af8b66f5da614245c83c526663e65690f55ed0f` |
| `0x020E08–0x022FD8` | Helpers copied into executable RAM | `a77bf7f644b09b8ef4dbb48e00ba49196e2e8636a8402d74991592726461c4f0` |
| `0x114EA4–0x11587C` | Examined calibration pointer table | `e4416cbbbae05752a42a0f9e2dc416a5ef8956799181396423e70a38ce7491c9` |
| `0x0DE576–0x0DEA54` | Calibration pointer management | `ee31c6bca3c708c082302f22c8390db55b00cd948549a0ebd26dd66e993e4313` |

These comparisons establish agreement for the examined ranges, not complete byte-for-byte equivalence of the BINs or equivalence to a live flash.

## Calibration pointer resolution

1. File offset `0x533E0` contains the pointer `0x80114EA4` and a following table count of `0x276`.
2. The initialization code at `0x800DE694–0x800DE6B4` loads that default pointer into its calibration-management state. `0x800DE5EC–0x800DE5F0` copies the selected default into the pointer slots.
3. `0x800DEA14–0x800DEA48` selects a pointer slot and loads address register A9, with handling of the flash cached/uncached alias bit.
4. Pointer-table entry `0x80114EA4 + 0x6B8 = 0x8011555C` contains `0x801D16D4`.
5. The injector routine loads `[A9 + 0x6B8]` into A12. Its relative accesses resolve multiple independently recognizable calibration objects correctly.

This supports the default static pointer mapping. The code also supports redirected pointer slots; a live RAM capture would be needed to exclude every possible runtime overlay. No evidence in this audit establishes such an overlay during the logs.

## Locally verified calibration layout

The corresponding older A2L injector block is displaced by `+0x4FC` in this J00B layout. This is a **local block relationship**, not a global software-version translation.

| Object | J00B file offset | Evidence |
|---|---:|---|
| CWBMWINJAD | `0x1D16D4` | Group base; current byte 2; correction-selection branches read it |
| CWKLTELIN | **`0x1D16D5`** | Group +1; current byte 1; explicit curve-selection branch |
| FKKVS record | `0x1D16D6` | Group +2/+4 dimensions and group +6 axis data |
| KLHDEV record/count | `0x1D186A` | Group +0x196 |
| KLHDEV input axis | `0x1D186C` | Group +0x198 |
| KLHDEV signed outputs | `0x1D18CC` | Group +0x1F8 |
| KLOFSAG record | `0x1D192C` | Group +0x258 |
| KLPBR record | `0x1D1942` | Group +0x26E |
| KLTELIN record/count | `0x1D1974` | Group +0x2A0; 30 points |
| KLTELIN axis | `0x1D1976` | Group +0x2A2 |
| KLTIKRPR outputs | `0x1D19EE` | Group +0x31A |
| KLTIKRTP outputs | `0x1D1A16` | Group +0x342 |
| KLTVTSV outputs | `0x1D1A4A` | Group +0x376 |
| MK2TE | `0x1D1A8C` | Group +0x3B8; raw 8803 |
| Shared pressure-axis count | `0x1D1A92` | Group +0x3BE; 20 points |
| Shared pressure-axis data | `0x1D1A94` | Group +0x3C0 |

The old A2L identifies CWKLTELIN as selecting KLTELIN versus KLHDEV. The J00B branch independently establishes which values select which curve. This is stronger than inferring behavior from an XDF label.

## Reconstructed calculation sequence

The located duration routine starts at `0x802F2764`. Only its established stages are described here; this is not a complete executable model or a calibrated physical prediction.

### Pressure input and shared axis

The helper at `0x802F2330` reads the rail-pressure quantity, computes a combustion-pressure-related term using the KLOFSAG/KLPBR region, subtracts it from rail pressure and limits the result to nonnegative values. Its result is stored at `0xC0001DF4` by the caller.

This is consistent with the older A2L's `dprpbrx` definition, "Differenzdruck Rail-Brennraum" (rail-to-combustion-chamber differential pressure). The older A2L identifies the source rail variable as filtered actual absolute rail pressure. The exact full combustion-pressure model and every input scaling were not reconstructed here.

Therefore, logged rail pressure is a useful proxy but is **not the exact pressure-axis input**. The earlier equal-pressure interpolation examples describe the table function at specified axis coordinates; pairing them with logged rail pressure requires this qualification, particularly at low pressure.

At `0x802F27C2–0x802F27D4`, the caller calculates an index/fraction from the shared 20-point pressure axis at `0x1D1A94`.

That same index/fraction is then used for:

- KLTVTSV signed delay lookup, `0x802F27D8–0x802F27E2`.
- KLTIKRPR unsigned factor lookup, `0x802F27E6–0x802F27F0`.

This independently confirms that changing the shared pressure axis changes both lookups' pressure coordinates.

### Pressure factor, MK2TE and fuel density

At `0x802F27F4–0x802F2802`, KLTIKRPR's lookup result is multiplied by MK2TE with a 14-bit right shift. The temperature-dependent fuel-density factor is looked up next and included with a 7-bit shift.

The routine then multiplies the composite factor by its incoming fuel-mass argument, applies fixed-point scaling and stores the resulting linear-time intermediate at `0xC0001DE8`.

Thus KLTIKRPR is a multiplicative part of the **pre-curve mass-to-duration calculation** in this routine. Its percentage difference is not automatically the final pulse-width, delivered-fuel or lambda percentage difference.

### KLTELIN versus KLHDEV

At `0x802F2884`, the routine reads `[A12 + 1]`, resolving to `0x1D16D5`.

- **Nonzero:** execution proceeds through the KLTELIN lookup at `0x802F2894–0x802F28AC`, subject to an upper input guard.
- **Zero:** execution enters `0x802F28B0`. It searches the 48-point KLHDEV input axis, interpolates the signed correction outputs, and adds that correction to the duration intermediate at `0x802F2954–0x802F2958`.

The stored value is **1**, selecting KLTELIN for this path. The XDF location `0x1D1ADB` contains zero, but that byte does not establish the selector used here.

### Following corrections

The next common stages include the FKKVS map, followed by addition of the KLTVTSV delay result (`0x802F2992–0x802F299E`). The routine then changes duration scaling and enters conditional correction/adaptation branches governed in part by CWBMWINJAD and runtime flags. Those branches read cylinder-indexed RAM correction data and apply additional interpolated factors/offsets. A later factor is applied at `0x802F2A6C–0x802F2A7E`.

The complete relationship of these RAM values to ISTA-entered injector codes, CVO learning, reset history, pause corrections, minimum-duration enforcement and final output scheduling remains unresolved. Entering injector codes does not by itself prove which corrections were active in a particular log sample.

## RAM helper decoding check

The initialization descriptor at file offset `0x51888` specifies destination `0xC0004980`, source `0x80020E08` and length `0x21D0`. This resolves the arithmetic helpers called in the duration routine.

For example, full CALLA target `0xC0004D0E` maps to file offset `0x21196`. The helper multiplies its two data inputs and performs a requested fixed-point right shift with saturation handling. Its body supports the multiply/shift interpretation above.

The decoder displays CALLA targets without their segment in this environment. The accompanying evidence file annotates the full targets reconstructed from instruction bytes; these calls must not be mistakenly followed into the boot-region bytes at file offset `0x4D0E`.

## Effect on the operating-impact assessment

1. **The pressure-index mismatch remains confirmed and relevant.** The compiled routine uses the copied KLTIKRPR outputs on the retained shared N55 axis.
2. **The copied KLHDEV curve must no longer be assumed active in this located path.** Its provenance is still N63, but provenance and selection are separate questions.
3. **The v5/v6 comparison needs revised attribution.** The effective MHD toggle behavior and likely adaptation reset remain unknown. The severe logged v6 richness cannot be assigned jointly to the copied HDEV curve and pressure factor on the old assumption that CWKLTELIN was zero.
4. **Rail-pressure correlation needs differential-pressure qualification.** This matters most where modeled combustion pressure is appreciable relative to rail pressure.
5. **Resampling is still a correction to review, not yet a selected fix.** Donor hardware applicability, outside-coverage endpoints and the remaining injector model must be resolved. No replacement values were generated in this step.

## Remaining work

- Trace the source and active selection of the cylinder-specific correction/adaptation RAM data.
- Resolve pause-time handling, minimum-duration enforcement and the final scheduled duration.
- Trace the normal-fueling quantity into the fuel-mass monitor, including normal fuel scalar incorporation, monitor correction selection and 1F0525 filtering/debounce.
- Do not globally translate older A2L RAM/calibration addresses or claim a live execution result from static analysis alone.

The available J00B executable is sufficient to continue; a matching J00B A2L would simplify the task, but its absence did not prevent the findings above.

Evidence: `j00b_disassembly_evidence.txt` in this directory contains source hash, byte-annotated instruction excerpts, pointer records and selected calibration bytes.
