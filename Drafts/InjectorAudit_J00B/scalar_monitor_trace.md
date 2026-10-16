# J00B normal scalar to fuel-mass monitor: confirmed data path

Read-only executable analysis, 2026-10-16. This extends `ols_broad_review.md` and supersedes its statement that the scalar-to-normal-monitor-input chain remained untraced. No calibration file or draft was edited.

Follow-up: `diagnostic_routing_1F0525.md` now resolves the routing item below. The Rlc branch reports 1F0525; the adjacent Gkc branch reports 1F0521. Complete trigger reconstruction and scheduler timing remain unresolved.

## Main result

The normal fuel scalar is incorporated into the normal fuel-mass quantity that feeds one side of the located monitor comparison, through the normal output-selection branch. It is not confined to a later injector-duration conversion. This establishes a mechanism by which changing the scalar can change the monitor comparison input. It does not establish the logged fault's exact cause or a safe scalar boundary.

The examined code ranges are byte-identical in April v11, April v12, v6 and the supplied FlexFuelv4 BIN. Source hashes, selector bytes and ranges are in `scalar_monitor_checks.json`; byte-annotated instructions are in `scalar_monitor_code_evidence.txt`. The script `trace_scalar_monitor.py` reproduces those checks.

## Confirmed chain

Addresses beginning `80` are executable flash addresses; `D000...` are RAM. The default global A0 is `D0009000`.

| Stage | Evidence | Result |
|---|---|---|
| Default scalar record | `802264FE–8022650C` initializes pointer slot `D0005098` to `801942B0` | Default record for the normal scalar; its values start at file `1942F2` |
| Scalar lookup | `8028E266–8028E27A` reads that pointer and calls `8027E3D8` | Two-dimensional lookup; returned value stored at `D0005F3C` |
| Scalar application | `8028E2BE–8028E2D0` multiplies a corrected mass intermediate by the lookup result and shifts by 15, with signed truncation handling | Q15 multiplicative use of the scalar |
| Normal mass result | `8028E2D8–8028E2E8` adds further terms and stores `D0005F68` | Scalar is one component of the resulting mass calculation |
| Normal output selection | `8028F13A–8028F14A` copies `D0005F68` to `D0006050` | Selected when runtime alternate flag bit 0 is clear and manual override is disabled |
| Monitor interface | `800A8684–800A86A2` reads `D0006050`, calls relocated helper `C000501A`, stores `D0002730` | Signed multiply by 25 / divide by 24, with helper saturation |
| Monitor input | `800620B6–800620C6` reads `D0002730` into scratch frame field `+4` | This is the normal-side quantity used by the previously located bound comparison |

Helper `C000501A` is stored at file `214A2` and relocated at startup. Its integer arithmetic and saturation matter near limits; the conversion should not be treated as unrestricted floating-point multiplication. CALLA disassembly omits the address segment, so the helper's full destination must be reconstructed from its instruction bytes.

### Branch limits

The copy above is conditional. If runtime byte `D0007A0C` bit 0 is set, `8028F0E4–8028F0FC` copies alternate source `D0005EEE` instead. If manual calibration byte `19510D` is nonzero, the other branch uses calibration `1836FA`. The manual selector is zero in all four examined tunes. The runtime alternate flag has not been reconstructed from the logs; the normal branch must not be asserted active in every logged sample solely from static code.

Likewise, initialization of the default scalar pointer does not resolve MHD custom map or flex-fuel selection. This trace proves the calculation's treatment of its selected scalar, not which custom table was selected at each instant.

## Shared learned-correction source

The normal calculation's selector at file `194A83` is 2 in all four examined tunes. Its selected branch at `8028E148–8028E184` reads signed RAM word `D000653E`, forms a mass-scaled correction and stores it at `D0005F60`. That term joins the upstream mass calculation before the scalar application. Selector 1 instead uses `D0005B28`; other values zero this term.

Independently, interface function `800A8B9C–800A8BBE` reads the same `D000653E` word, arithmetic-shifts it right by two, adds `0x4000`, and stores the result at `D00028AE` and `D00028B0`. The monitor's adaptation selector `CWLRADP_UM` at file `1B84BB` is 1. The branch at `8006214C` enables adaptation and chooses the `D00028AE` source rather than the alternative `C00020A4` source.

This establishes shared input data, with different arithmetic on the normal and monitoring paths. It does not establish that the effects cancel, that this is the only learned correction, or that its exact value can be reconstructed from an LTFT channel without verifying that channel's conversion and source. Older definitions suggest additive adaptation naming, but the shared-RAM conclusion does not depend on those names.

## Interpretation for April v11/v12

The earlier operating comparison found scalar increases of approximately 2.83% and 4.51% at the selected v11 pre-cut RPM/load points. The traced multiplication provides a concrete sensitivity mechanism: a small scalar change can move the normal-side comparison quantity while monitor bounds and learned state also affect the outcome.

However, the final normal-side quantity is not simply the scalar multiplied by the monitor reference. Additional terms, truncation, branch selection and adaptation intervene. The monitor's internal reference and counter state are not logged. Consequently these instructions do not numerically reconstruct the v11 threshold crossing, prove the whole output changed by exactly 2.83–4.51%, or demonstrate v12's margin.

The previously established bound stage remains:

```text
upper_raw = trunc(reference_raw * 170 / 128) + 224
lower_raw = trunc(reference_raw * 113 / 128) - 224
```

These are bounds on a fuel-mass comparison quantity, with other checks and counters around them. Neither `FRKMAX_UM = 1.328125` nor `FRKMIN_UM = 0.8828125` is a direct scalar-cell limit. Nothing here establishes 0.85 as a safe minimum.

## Executable coverage and remaining work

The supplied FlexFuelv4 and vehicle-named stock reference are both 4 MiB. All 48,179 differing bytes lie within file `180000–1FFFFF`; no differences were found outside that calibration region. Thus this local comparison does not expose a distinct custom executable implementation for MHD map/FF selection. It does not establish what an external flasher may do at runtime or during programming.

Remaining high-value tasks:

1. Trace the alternate output flag and all trim-source writers, especially `D000653E`, to distinguish learned adaptation from instantaneous control and establish release conditions.
2. Complete the monitor reference's calculation and scaling, including enabled correction and adaptation paths; then assess expected sensitivity of both sides to a scalar change.
3. Trace the monitor reaction identifiers through diagnostic routing to establish whether the located path produces 1F0525 and how its counters map to time. Counter tolerance 13 is not evidence of 13 milliseconds.
4. Keep April whole-pull STFT/adaptation evidence separate from the later injector-table transfer and flex-fuel selection questions.

No replacement calibration values or flash-safety conclusion follow from this code trace.
