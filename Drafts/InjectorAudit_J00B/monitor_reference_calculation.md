# J00B monitor reference: reconstructed current branch

Read-only analysis, 2026-10-16. No calibration or draft edited. This extends the scalar-to-monitor and DTC-routing reports. Evidence: `monitor_reference_code_evidence.txt`, `monitor_reference_checks.json`; extraction script: `trace_monitor_reference.py`.

## Main result

The first-bank reference calculation has been followed from its input selection through to the upper/lower comparisons associated with 1F0525. Its arithmetic uses upstream charge/fuel intermediates, lambda-control mean, learned adaptation, purge contribution, enrichment and the selected monitor correction map. There is **no direct normal-scalar lookup, MK2TE lookup or injector-duration lookup in this reference calculation**.

Some inputs are shared with normal fueling. Therefore this is not proof of complete dynamic independence from scalar changes: closed-loop correction and learned state can respond to a calibration change, and several upstream producers are not fully reconstructed. It establishes the direct input/arithmetic distinction, not a vehicle-state reconstruction.

The examined instructions and branch-selecting calibration bytes are identical in v6, April v11, April v12 and FlexFuelv4.

## Stored branch choices

| Setting | File offset | Stored value | Effect in the located code |
|---|---|---:|---|
| CWLASP_UM | `1B84BA` | 1 | Enables the limited adjustment at `80062332`; bit 1 is clear |
| CWLRADP_UM | `1B84BB` | 1 | Enables learned correction through the `D00028AE` source |
| CW_VARTE_UM | `1B84BD` | 0 | Current purge-related input selection includes `C0002594` in the later subtraction |
| Master/slave configuration | `1B8468` | 0 | Selects 8x8 KFFKKORRF monitor map, not the alternative 16x16 map |
| Final reference additive calibration | `1B88BA` | 0 | No contribution from this constant |

## Input identities and sources

Scratch frame is `F = D0016850`. Names below distinguish code-derived roles from older-definition interpretations.

| Role in arithmetic | Actual source | Supporting instructions / qualification |
|---|---|---|
| Normal comparison quantity N | `D0002730` | `800620B6–800620C6`; previously traced from selected normal fuel mass `D0006050` after 25/24 conversion |
| Common factor E | `C0000304` | Read to F+2; normal scalar calculation also uses this source and the same /1024 factor convention. Total-enrichment interpretation is supported by surrounding normal code; full producer classification remains open |
| Lambda-control mean word | `C0002296` | Read at `800620F2–80062142`; local older-definition correspondence is `frm_w`, fast mean of the lambda-controller factor |
| Learned correction | `D00028AE` | Selected at `80062196–800621D8`; interface derives it from `D000653E >> 2` plus `4000` hex |
| Base input B | `D001624A` / `D00026E4` | `80061790–800617DE` copies the latter; interface derives it from a charge-related source `C000041E` with rescaling |
| Limited input U before clamping | `D0002C1C` | `8006222E–80062258`; copied from `D00028CC` in an interface path, with complement checking |
| Upstream source of U | `D0005F46` | `800A8D46–800A8D96` converts it to `D00028CC`; normal fueling calculates this source at `8028DFFC–8028E022`, **before** scalar lookup/multiplication |
| Base fuel term W | `D000275E` | Interface `800A8A62–800A8A86` reads `D0005F58` and converts 25/24. Older definition alignment supports base homogeneous relative fuel mass naming |
| Additional fuel term D | `D00028CE` | `80362916–803629D4` converts `D0005F4E` by 25/24 if its complement check passes; otherwise zeros it |
| Additive term A | `D00026EC` | `800A4F4A–800A4F6C` converts `D0005F4A` by 25/24. This normal RAM source is also added **after** scalar multiplication in normal fueling |
| Purge-related term P | `C0002594` | Input/selection at `800620B2–800620F0`; local older-definition correspondence is `rkte_w`, relative mixture contribution from tank ventilation |

Several physical names depend on locally checked older-definition alignment; the actual RAM-source links above are executable evidence. No global RAM-offset translation is assumed.

## Reference arithmetic

Let `trunc` mean signed truncation toward zero, as implemented by the code's sign-adjusted shifts. Saturations and signed-byte packing are material; this is explanatory pseudocode rather than a complete bit-exact ECU emulator.

### 1. Limit the upstream input

Under stored CWLASP_UM=1, `80062332–800623DE` forms an upper allowance using a load/RPM-indexed monitor limit, then limits U between B and that upper value. F+1C receives this limited quantity. The zero-denominator handling and signed saturation are explicit. The alternative branch that chooses a different F+1C source is not selected by stored bit 1.

### 2. Combine control and learned correction coefficients

The mean-controller coefficient is formed from the word's high byte plus 128, stored as a byte and later read signed. Unity `8000` hex therefore gives coefficient zero, not 128 or 256.

The enabled learned path truncates `D00028AE / 128`, then adds 128 and similarly packs/reads it signed. A unity source `4000` hex gives zero learned coefficient. This path also checks its adaptation limit and can set a separate failure flag.

At `8006247E–8006249C`, the two signed coefficients are added because learned correction is enabled. Call their sum C.

### 3. Form the pre-map mass reference

`800624A6–800624F4` implements:

```text
T = sat16(trunc((trunc(U_limited * C / 256) + W + D) * E / 1024))
```

The lambda-control mean is not necessarily identical to the instantaneous STFT value in a log. The learned-source conversion is also not established to be identical to a generic logged LTFT channel. Similar instantaneous lambda therefore cannot establish identical reference state.

### 4. Apply the monitor correction and additive term

The stored master/slave branch selects the 8x8 monitor map at `800624F8–80062558`. Its returned byte K uses a /128 convention, so 128 is unity. The later stages at `80062574–800625D6` produce:

```text
R = sat16(trunc((T - P) * K / 128) + A + final_additive_calibration)
```

The final calibration is zero in the examined tunes. The selected map is unity in its high-load columns, but is not uniformly unity across the entire map.

### 5. Compare normal quantity against the reference bounds

For the positive reference case, the identified bound stage is:

```text
upper = sat16(trunc(R * 170 / 128) + 224)
lower = sat16(trunc(R * 113 / 128) - 224)
```

The code clamps negative N to zero before these comparisons. R<=0 receives separate handling. It flags N above upper or below lower. These are fuel-mass bounds, not scalar-cell limits.

## A second check shares the 1F0525 failure flag

Before the two bounds, `800626C8–80062744` quantizes W by dividing by 32, derives another estimate using the limited/base inputs and a lambda-coordinator-related source at `C0002014`, and compares their discrepancy with raw tolerance 17 at file `1B84BE`. A discrepancy beyond that tolerance writes the same F+26 failure marker used by the two bounds.

Consequently 1F0525 can identify a failed monitor branch without establishing that the upper or lower multiplicative bound was responsible. It remains necessary to distinguish this base-consistency check from a scalar-driven bound crossing. The full physical scaling and logged observability of this additional estimate remain unresolved.

## Consequence for MK2TE versus scalar

The normal scalar changes the normal fuel-mass calculation upstream of N. Normal MK2TE instead acts in the subsequent fuel-mass-to-duration conversion. Neither MK2TE nor the normal scalar table is directly applied in the reference arithmetic above.

Thus lowering MK2TE and raising the scalar reciprocally can preserve a duration-model product while changing N relative to R, with upstream state held fixed. Subsequent closed-loop and learned-state changes can modify R as well. This supplies a mechanism for non-equivalence; it does not establish whether that redistribution would help this vehicle or which scalar has acceptable margin.

No MK2TE, scalar, curve selector or monitoring change follows automatically. The pressure-table-only logging remains the appropriate isolated operating comparison while reference/input classification continues.

## What remains after this step

- Fully classify all upstream producers and their physical scaling, especially the common enrichment and additional fuel terms.
- Reconstruct the extra base-consistency estimate and complete release/reset timing.
- Relate the internal mean/learned corrections to available logged channels, without assuming instantaneous STFT/LTFT equivalence.
- Use new logs for the pressure correction's operating effect; old logs lack the internal state needed to replay the exact April fault.

The reference's local arithmetic is now mapped through the bound comparisons. This should not be described as a complete executable model of the ECU or a numerical replay of the fault.
