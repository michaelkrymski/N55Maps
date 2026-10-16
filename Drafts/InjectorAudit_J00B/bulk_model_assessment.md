# Bulk injector model: isolated numerical comparison

Read-only, 2026-10-16. No calibration changed. Reproducible calculation: `compare_bulk_injector_model.py`; source hashes and full results: `bulk_injector_model_comparison.json`.

## What is now established

The retained N55 forward/inverse curve pair is internally consistent: the 30 forward input points exactly equal the inverse outputs, and the 30 forward outputs exactly equal the inverse inputs. In an ideal linear-interpolation round trip, representative inputs recover the original input. This is a positive consistency check, not proof that the curves describe the installed injectors or that the complete forward/reverse algorithms cancel every correction.

The normal MK2TE raw word is 8803. The matched N63 reference raw word is 5800, read directly from donor HEX using its A2L address. Their ratio is **1.5177586**, so with the other factors held equal the retained normal conversion produces **51.78% more linear-time input** for the same requested fuel mass. The old transfer copied neither this donor conversion constant nor an active donor forward-curve representation.

The copied donor KLHDEV axis and correction outputs match the donor HEX exactly. The located N55 normal duration routine selects its retained KLTELIN path instead of the copied additive KLHDEV path. Thus provenance of the transferred KLHDEV does not establish that its shape is applied by that routine.

## Controlled comparison of two model stages

This experiment compares:

```text
retained N55 stage = KLTELIN(mass * N55_MK2TE)
N63 reference stage = mass * donor_MK2TE + KLHDEV(mass * donor_MK2TE)
```

Pressure and density factors are set to exactly one for both. Delay, FKKVS, coding, CVO, pause corrections, clamps, pulse splitting and scheduling are excluded. Interpolation is floating point, not bit-exact ECU arithmetic. Fuel masses below are illustrative and are not recovered from a logged injection event. The donor expression describes a comparison curve using the documented additive convention; the N63 executable's full branch selection and duration calculation are not asserted reconstructed here.

| Illustrative mass | Retained N55 stage | Donor reference stage | Difference relative to donor |
|---:|---:|---:|---:|
| 5 mg | 0.5015 ms | 0.2346 ms | +113.8% |
| 10 mg | 0.9615 ms | 0.5957 ms | +61.4% |
| 20 mg | 1.8076 ms | 1.2928 ms | +39.8% |
| 40 mg | 3.6217 ms | 2.4832 ms | +45.8% |
| 60 mg | 5.5019 ms | 3.6531 ms | +50.6% |

These are differences between isolated calibration-model stages, **not delivered-fuel, richness, lambda or engine-risk percentages**. Hardware applicability of the donor is still unconfirmed. An actual differential-pressure factor of one is not assigned to an arbitrary logged rail pressure in this experiment.

The nonlinear shape differences are significant at small pulse quantities. A single bulk rescaling cannot make the entire two-curve shapes identical. A load/RPM scalar may compensate differently as pulse quantities and modes vary, but this experiment does not establish which scalar values are physically correct.

## What this changes in priorities

The bulk conversion and selected curve deserve priority over further injector-code decoding. The donor pressure-table resampling repairs the identified indexing mismatch, but it leaves the normal N55 base conversion and selected N55 forward/inverse pair in place. That is a credible mechanism for substantial scalar compensation if the donor model applies to the installed injectors. It is not sufficient evidence to prescribe donor MK2TE alone or switch CWKLTELIN.

Neither scalar unity nor any particular non-unity value is an acceptance criterion. A satisfactory model must produce consistent fueling over pulse quantity, pressure and operating mode, while maintaining agreement with the monitoring calculation. The current evidence does not yet establish that agreement for the installed hardware.

## Work remaining

The code-structure investigation is substantially complete for choosing the main calibration targets. Three substantive items remain before calling the injector issue resolved:

1. **Calibration decision:** establish an injector characterization appropriate to Bosch 0261500136 and a coherent way to represent it in the active N55 forward/reverse/adaptation calculations. The reference comparison is not hardware verification.
2. **Monitor consistency:** finish enough of the monitor reference/trim calculation to assess why the large scalar compensation changes fault margin. DTC routing is already confirmed; fault-direction reconstruction is not.
3. **Operating validation:** assess the corrected model on the fixed pump-gas mixture, with known ethanol and adaptation history, progressing from low load. Existing logs cannot establish the post-correction outcome or injection duration where that channel was absent.

More general CVO and per-injector coding reverse engineering can be deferred unless those items identify a material dependency. There is no defensible percentage-complete estimate for hardware characterization and operating validation, and no basis to promise that another table edit alone will resolve the fault.
