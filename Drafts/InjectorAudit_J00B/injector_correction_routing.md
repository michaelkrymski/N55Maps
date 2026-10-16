# Injector correction routing beyond the pressure table

Read-only J00B investigation, 2026-10-16. No calibration or draft changed. Evidence and reproducible checks: `injector_correction_code_evidence.txt`, `injector_correction_checks.json`, `trace_injector_corrections.py`.

## Main findings

1. Current CWBMWINJAD=2 does not unconditionally apply one correction method. It selects runtime-dependent routes using a cylinder bitmask at `D000381C`.
2. The normal mass-to-duration routine applies cylinder-characteristic factors/offsets on one route; its caller conditionally adds a separately computed CVO correction on another. An additional runtime condition can also permit the CVO contribution. These are not equivalent to lambda STFT/LTFT.
3. The reverse duration-to-mass helper uses the same normal KLTIKRPR, shared pressure axis, MK2TE and delay table as the forward path. The resampling therefore changes both calculations in a coordinated manner. A separate KL_INJAD model still exists and must not be conflated with this helper.
4. Both selected forward and inverse curves remain stock N55 in v6/v11/v12/FlexFuelv4. All examined executable ranges match across these four files.

## Current selector and factor/offset route

At `802F29AA`, the normal duration routine reads `[A12]`, resolving to CWBMWINJAD at file `1D16D4`.

For stored value 2, bit 0 is clear and bit 1 is set. It tests bit `cylinder_index` of RAM byte `A0-57E4 = D000381C`:

- Mask bit clear: enter the cylinder-characteristic factor/offset calculation at `802F29C6`.
- Mask bit set: skip that calculation via `802F2A6A`.

The factor route interpolates between unity and two per-cylinder factor words from `C0002434`, using linear duration to form the interpolation position (`802F29DA–802F2A3E`). The factor is applied with a 14-bit shift. It then interpolates two signed per-cylinder offset words from `C000204E`, with zero-valued endpoints, and adds the result (`802F2A42–802F2A66`). A further global factor from `C0002454` follows with a 12-bit shift.

Confirmed source transfers:

```text
D0005F8A (12 words)
    -> C0002034 (80361CCA–80361D14)
    -> C0002434 (803766EA–80376794; optional common normalization)

D0005FD8 (12 words)
    -> C000204E (80361D16–80361D5C)
```

The factor normalization is gated by `[A9+7E4]` bit 0; its default record is at file `1D5108`, whose byte is 1. Its common factor at `C0002432` comes from a separate curve lookup at `80376678–803766A0`. The complete purpose/scaling of this normalization remains to be resolved.

One initialization/default path at `802A31DE–802A3220` copies unity factor words from file `194C54` into `D0005F8A` and duplicates per-cylinder offset-source words from `D001DE36` into `D0005FD8`. Older definitions identify the factor calibration as a manual injector-adaptation factor array. This establishes a source path, not the value present in live RAM or the complete learned/coded contribution. Other writers and activation conditions remain under investigation.

## Separate CVO route and later addition

The forward conversion calls `802F520C` at `802F2CD0` and stores the returned correction at:

```text
D0002618 + 2 * (3 * cylinder_index + pulse_index)
```

This CVO function checks runtime release flags, CVO enable at file `1D13D8`, cylinder/pulse conditions and learned/integrator contributions. It compares the correction with bounds at group offsets AC/AE before converting its output scaling. It can return zero. Stored enable bytes alone do not prove it contributed to a particular pulse.

The caller's `802F02AC–802F02F0` reads CWBMWINJAD and the same `D000381C` mask. For CWBMWINJAD=2, a set mask bit enters the CVO-addition branch. With a clear mask bit, the code can still enter it if the cylinder runtime byte at `D000086A + cylinder_index` equals 1 and the current pulse flags have bit 3 set. When selected and pulse index is below three, the caller reads the correction array above and adds it to its duration accumulator.

Consequently it would be inaccurate to call CWBMWINJAD=2 simply "coding only" or "CVO only," or to assume that entering injector compensation codes in ISTA settles the runtime contribution. No recommendation to change this selector follows from these branches.

The mask writer is also located: `802F68FC` calls `802F47B4`, preserves its returned low byte, and `802F6A46–802F6A4A` stores it to `D000381C`. An initialization path at `802F5FB2–802F5FB6` clears it. The mask-calculation routine checks a CVO configuration at group offset DF, pressure-region selection and per-cylinder/per-region validity checks, including calls to `802F6E54` and `802F6CFA`. In one branch it starts with mask `3F` and removes cylinder bits when these checks fail. Thus selection can depend on validity across regions, rather than being solely a fixed global enable. Full meanings of the subordinate validity checks and their live history remain unresolved.

## Reverse conversion uses the resampled pressure table too

At `800A4080–800A4178`, the reverse helper:

- Computes rail-to-chamber differential pressure through `802F2330`.
- Indexes the same shared pressure axis at file `1D1A94`.
- Looks up normal KLTIKRPR at `1D19EE`, multiplies it by MK2TE at `1D1A8C`, then includes the density correction.
- Subtracts the pressure-dependent delay and applies the inverse linear curve (record at `1D17D0`, outputs at `1D180E`).
- Converts back toward a mass quantity using the composite factor.

This is concrete evidence that resampling KLTIKRPR is not solely a one-way change to commanded pulse width. It does not prove that every independent adaptation/reference calculation shares this table or that every forward correction is inverted. The helper has callers at `802F05D2` and `802F26DE`; their complete scheduling/monitoring roles remain to be classified.

## Pause correction

After the main factor/offset stages, `802F2B5C–802F2C0C` derives a duration-dependent weight and looks up both KLTIKRTP and KLTIKRTPB using the pause quantity. It interpolates between those signed outputs, rescales the resulting correction and adds it to the duration accumulator. Thus pressure alone cannot explain all duration changes; pulse spacing and operating mode can matter even at steady rail pressure. This does not establish that the retained pause calibrations are wrong.

## Implication for the next calibration decision

The active model is broader than a scalar plus a pressure correction. At this stage, there is no justified replacement value for MK2TE or the selector. The next useful result is the full eligibility criteria behind `D000381C`, followed by the full factor/offset writers and donor-versus-installed-hardware characterization. That will distinguish a bulk conversion mismatch from additive timing corrections and learned state.

Follow-up correction: the provisional constant-location candidates `183678` / `1836F0` are withdrawn. The subsequent local constant-block/code trace supports `K_INJAD_MK2TE` at `183624` and `K_DMC_MK2TE` at `18369C`, respectively. See `injector_validity_and_coding.md`. The normal MK2TE remains at `1D1A8C`. Their names do not make them interchangeable; full scaling and use must be established before treating them as calibration targets.
