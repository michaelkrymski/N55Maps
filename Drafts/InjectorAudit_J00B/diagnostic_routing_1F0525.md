# Confirmed J00B routing to 1F0525

Read-only analysis, 2026-10-16. No BIN, HEX, XDF or saved calibration draft was changed. This resolves the diagnostic-routing uncertainty in `scalar_monitor_trace.md` and `ols_broad_review.md`.

## Result

The monitor branch associated with internal reaction identifier `0x3032` routes through status bit `D0000B11.2` to diagnostic handle `0x8494`, event index `0x494` (1172). J00B's actual diagnostic tables and assembly code turn that event into **1F0525**.

The adjacent `0x3031` branch instead routes through `D0000B63.1` to handle `0x848F`, event index `0x48F` (1167), and **1F0521**. These are distinct branches and must not be combined.

| Monitor branch | Failure counter RAM | Status bit | Diagnostic handle | Event index | Assembled DTC |
|---|---|---|---|---|---|
| Rlc (older-definition name) / reaction 3032 | `D0016255` | `D0000B11.2` | `8494` | `494` / 1172 | **1F0525** |
| Gkc (older-definition name) / reaction 3031 | `D0016254` | `D0000B63.1` | `848F` | `48F` / 1167 | **1F0521** |

The branch names are supported by the older definitions and surrounding calibration usage. The numeric event-to-DTC mapping is established directly from J00B executable references and data, without applying an assumed global address offset from the older A2L.

## Instruction-level route

1. The upper-bound comparison at `8006278C–8006279A` writes scratch field `D0016850 + 26` when the normal-side quantity exceeds its upper bound. The lower-bound comparison at `800627EE–800627FC` writes the same field when the quantity is below its lower bound. The written nonzero marker is `69` hex. Other plausibility checks also write this field.
2. At `80062DCE–80062DE0`, the reaction stage tests that field and the release bit `D0000B3B.4`. An eligible nonzero failure enters the Rlc counter branch; pass/inhibit handling starts at `80062E6E`.
3. `80062DEA–80062DF6` reads failure counter `D0016255` and its tolerance from the mixture-monitor group at displacement `3EE`, file `1B88A8`. This tolerance is 13 in the examined tunes. Below tolerance, the branch increments the counter; at/above tolerance, it enters the reaction/latch stage. Scheduler period and complete timing remain unresolved, so this is not a 13 ms finding.
4. The reaction/latch stage includes an optional internal system reaction using identifier `3032` at `80062E32–80062E3A`, then status-latching instructions including `80062E54`, which sets `D0000B11.2`.
5. Diagnostic reporting routine `800771BA` reads that exact status bit at `800771BC–800771C0`. With the bit set, it supplies `d5=15`, `d6=1`, `d7=15`, loads handle `8494` from flash `80030868`, and calls `8008AD1C` at `80077206`.
6. `8008AD1E` extracts the handle's low 12 bits, yielding event index `494`. The reporter processes that indexed diagnostic state and inhibit settings. It does not treat `3032` as the externally reported DTC.

### Internal reaction is separate from diagnostic reporting

The previously identified `800B612A` target captures reaction context, including the identifier and its inverse, disables interrupts and accesses debug/system-reaction registers. It is not the ordinary event-to-DTC lookup routine.

The monitor's reset/reaction limits at file `1B88A9` and `1B88AA` are both zero in the examined tunes. In the ordinary initial-count case, the shared reset/reaction counter is incremented to one, so the zero limit makes the code skip this internal system-reaction call and continue to latch the fault status. This is why following only the `3032` call target would miss the ordinary diagnostic reporting path. No settings were altered for this investigation.

## Direct proof of DTC construction

J00B's default calibration pointer table is at file `114EA4`. Its pointer at displacement `20C` selects the manufacturer DTC word array at file `1C2064`; displacement `22C` selects the fault-type byte array at file `1C61B0`.

For event `494`:

```text
manufacturer word address = 1C2064 + 2 * 494 = 1C298C
stored bytes              = 05 1F   (little endian word 1F05)
fault-type byte address   = 1C61B0 + 494     = 1C6644
stored byte               = 25
assembled DTC             = (1F05 << 8) | 25 = 1F0525
```

This assembly is explicit in the executable:

- `800D79DC–800D79EE` selects manufacturer table `[A9+20C]` for format selector 3, otherwise the OBD word table `[A9+220]`.
- `800D7B88–800D7BA0` fetches the event's fault-type byte through `[A9+22C]`.
- `800DF41E–800DF436` explicitly selects format 3, reads the indexed word, shifts it left eight and ORs in the byte. The result is subsequently stored in the output array at `800DF454`.
- `8008D84A–8008D862` contains the equivalent word-plus-byte assembly for a stored event, and `8008D778–8008D792` compares against DTCs constructed in the same way.

For event `48F`, the word is also `1F05`, but the fault-type byte at file `1C663F` is `21`, giving `1F0521`.

This also explains why searching for contiguous bytes `1F 05 25` or `25 05 1F` found no match: the word and final byte reside in separate indexed arrays.

## What this establishes for the scalar investigation

The earlier trace established that the normal scalar affects the normal-side fuel-mass input through the normal output-selection branch. This trace now establishes that the monitor's upper/lower fuel-mass comparisons feed a failure flag whose filtered reaction can report **1F0525**. The scalar-to-monitor-to-DTC relationship therefore has a confirmed executable path.

However, **1F0525 does not identify the direction of the discrepancy**: both upper and lower bound failures reach this path. Other plausibility checks also share its flag. This does not prove which check caused the logged event, reconstruct the internal reference or counter history, or independently map the logging channel value 2048 to this diagnostic.

The remaining operating question is whether April v11 crossed one of these bounds, or another check feeding this flag, while v12 did not. Resolving that requires the full reference/trim calculation and branch conditions. Neither a safe scalar minimum nor a recommendation to modify monitor protections follows from the routing result.

## Verification and reproducibility

`trace_diagnostic_routing.py` reads the four local BINs and writes only analysis artifacts. All examined routing code ranges are byte-identical across v6, April v11, April v12 and FlexFuelv4. The diagnostic handles, table bases, DTC entries, failure tolerances (13/13) and internal reset/reaction limits (0/0) also agree across those four files.

- `diagnostic_routing_checks.json`: hashes, code comparisons and exact per-file event/table reads.
- `diagnostic_routing_code_evidence.txt`: byte-annotated instructions.

Decoder caveat: Capstone's printed ST.T value operand is unreliable in this build. For example, the distinct bytes at `80062CFE` and `80062D04` print the same operands despite different encoded bit values. Preserve raw instructions and do not infer set/clear behavior from that printed operand alone. The relevant latched-failure stores retain their raw bytes in the evidence file.
