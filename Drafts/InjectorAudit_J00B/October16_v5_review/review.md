# October 16 v5 operating review

The logs support persistent fueling deviations and a changing correction state. They do not support declaring the injector model resolved, attributing all deviations to pressure, or applying one fuel-scalar reduction across the map.

## Calibration and logged configuration

Direct 4 MiB comparison of FlexFuelv5(InjectorFix-FuelMassFloor).bin against v4 finds **38 changed bytes**:

- 37 within the 20-word KLTIKRPR output array, matching the previously reviewed resampling.
- One at file `1B84C0`: FRKMIN_UM raw 113 to 109, **0.8828125 to 0.8515625**.
- No other differences. The shared pressure axis, normal scalar, MK2TE, curve selector and remaining models are unchanged. The 2-bar axis point already existed; this export did not add/change it.

V5 SHA256: `e6312c01a2316fe35ec5169f11db3d3da0c519e37c6de210dbaf448431252d7e`.

Both logs report Map 1 throughout, Ethanol CAN equal to Active, Fuel Interpolation 0 and Fuel Scalar Interpolation 0. The first log reports E12 throughout; the second switches between E12 and E13. This supports the intended fixed running-fuel calibration in these logs. It does not establish that ethanol-dependent start/warmup compensation is inactive.

The log filenames identify v5; a filename is not an independent live BIN readback. All stated calibration changes are verified in the local v5 BIN.

## First log: cold start, warm idle and late idle

The 14_26_27 log has 7,045 samples from 0.737–812.710 seconds. Median sample spacing is 0.110 s, but its longest gap is 19.034 s. No inference is made about behavior in missing intervals.

Near-idle filters use 600–900 RPM, pedal below 1%, and AFR target 14–15.5. Vehicle speed and torque-converter state are absent, so "near-idle" does not establish a stationary vehicle. The rows below describe filtered operating samples within the stated windows, not every sample in the window.

| Window | Samples | RPM median | RAM load median | STFT median | LTFT median | AFR actual / target medians | Rail actual / target medians |
|---|---:|---:|---:|---:|---:|---|---|
| 10–35 s | 192 | 741 | 31.2% | -30.0% | +0.01% | 14.43 / 14.71 | 1310.6 / 1309.3 psi |
| 35–90 s | 468 | 750 | 34.9% | -6.5% | -20.61% | 14.71 / 14.70 | 1311.0 / 1309.1 psi |
| 400–500 s, qualifying samples begin at 447.796 s | 484 | 707 | 30.3% | -19.55% | +0.01% | 14.50 / 14.71 | 1309.3 / 1309.1 psi |
| 700–813 s | 735 | 712 | 27.6% | +13.1% | +0.01% | 14.57 / 14.71 | 1310.5 / 1309.9 psi |

Your warm-idle and late-idle observations are confirmed. The sign reversal also survives a narrower 680–740 RPM / 27–31% RAM-load screen: STFT medians are **-19.4% versus +13.0%**, while LTFT remains +0.01% in both. These are comparable ranges, not perfectly identical conditions: load medians are 30.1% and 27.9%, coolant about 201 versus 205 F, and IAT about 97 versus 104 F.

An offline interpolation of the unchanged Map 1 scalar at logged RPM/RAM load estimates roughly 1.040 in the earlier warm screen and 1.037 in the later screen. The lookup estimate changes by far less than the trim reversal. This estimate is not a logged ECU scalar, and the exact internal load input may differ from the RAM channel.

Cold-idle STFT returning toward zero is not itself a recovery of the base model. For example, the unfiltered 40–60 s window has median STFT -16.5% and LTFT -14.85%; at 60–80 s they are -4.7% and -22.8%. A substantial reported correction remains as the split between the two channels changes. This is not proof of a reset or a complete reconstruction of the learning strategy. Initial cold-start AFR also needs sensor-readiness qualification.

Cruise-like samples also vary. A screen of 1,300–3,000 RPM, pedal 3–40%, load 20–90% and near-stoichiometric target gives STFT ranges **-17.8 to +15.6%** in the first log and **-10.7 to +30.8%** in the second. Those screens include transitions and different conditions; their extrema are not steady-cell tuning instructions. In the second log, median LTFT in this screen is -13.66%, so positive STFT must not be interpreted alone as a positive total correction.

## Second log: pull and shifts

The 14_50_23 log has 3,373 samples from 0.628–375.736 s, median spacing 0.108 s and maximum gap 4.129 s. The pull is a **part-throttle, multi-shift acceleration**, not a sustained full-throttle single-gear sweep. In the enriched/high-load screen below, pedal is about 62–76% and RPM peaks at 4,202. It does not recreate the April 4,800–5,200 RPM / higher-load event conditions.

Logged gear changes occur at **290.331, 291.467 and 292.627 s**. AFR targets and torque states also change during the shifts, so shift-adjacent actual/target comparisons are not sufficient for a steady fueling correction.

Nevertheless rich readings occur away from the exact gear-change samples:

| Time | Gear | RPM | Actual AFR | Target AFR | Rail actual / target | STFT | Cylinder 6 correction |
|---:|---:|---:|---:|---:|---|---:|---:|
| 291.047 | 3 | 3350 | 11.99 | 13.74 | 2842.1 / 2900 psi | 0% | -4.2 deg |
| 292.217 | 4 | 3469 | 10.97 | 13.04 | 2881.5 / 2900 psi | 0% | -3.0 deg |
| 292.327 | 4 | 3520 | 10.96 | 12.84 | 2895.9 / 2900 psi | 0% | -3.0 deg |
| 292.527 | 4 | 3646 | 10.75 | 12.79 | 2897.7 / 2900 psi | 0% | -2.7 deg |

The screen `289–293 s, pedal >50%, RAM load >100%, AFR target 12–14.3` selects 21 samples. Median actual/target AFR ratio is **0.854**; 17 samples are below 0.90. Those are AFR-ratio observations, not calibrated delivered-fuel percentages or recommended scalar multipliers.

Excluding samples within +/-0.35 s of each logged gear change leaves only five qualifying samples; three remain below 0.90 of target. That supports investigating more than an exact-shift artifact, but the small count and sensor/transport/control delays prevent a steady-state diagnosis. A richer-than-target sequence is visible from 292.109–292.527 s while the target returns from a shift excursion.

Most rich pull samples report STFT 0 and LTFT approximately 0.01, with Fuel Mode 2. At 292.627/292.738 s STFT briefly becomes -18.4/-18.1%. **Zero reported STFT does not prove correct fueling or closed-loop inactivity**; the precise release/hold/reporting behavior needs investigation. Fuel Mode numbers are reported without assigning unsupported meanings.

### Rail pressure and HDP factors

For the 21 enriched/high-load samples, rail error is -59.3 to +83.9 psi, median -18.5 psi against 2,900 psi requested. At 292.327 and 292.527 s it is within about 4 psi of request while AFR remains far below target. Sustained rail-pressure starvation is therefore not supported as the explanation for those rich samples.

The full 289–293 s window also contains a brief larger transient: **2731.7 versus 2900 psi at 292.007 s** (-168.3 psi, about -5.8%), during the target-AFR excursion to 17.7. This should not be hidden by the enriched-target filter, but it is not the sustained pressure collapse proposed in earlier hypotheses.

HDP I-factor reaches **1.6 at 292.217 and 292.327 s**. Neither the channel's implementation nor its permissible range has been established. The maximum observed value is not proof of saturation, spare capacity or pump failure. The logs contain no low-side-pressure channel or injector-duration/pulse-count channel.

## Timing corrections: pull versus low-RPM episodes

In the selected pull screen, cylinder 6 reaches **-4.2 degrees** (median -3.0), cylinder 4 reaches -2.7 (median -1.2), and cylinders 1/2/3/5 remain zero. Cylinder 6 deserves attention in this operating region.

However, the large low-RPM corrections are **not exclusive to cylinder 6**:

- First log, around **566.775 s, 1,296 RPM, 27.5% pedal and -0.1 psi reported boost**: cylinders 2/4/6 reach -7.5 degrees; cylinders 1/3/5 also show substantial corrections. Cylinder 6 has separate <=-6 degree runs around 90.304–93.088, 566.665–568.083 and 597.403–597.608 s.
- Second log, around **179.217 s, 1,178 RPM and 16.5% pedal**: cylinders 1/2/5 reach -7.5 degrees; cylinder 4 reaches -7.5 shortly afterward. Cylinder 6's minimum in this entire log is -5.7, not -7.5.

Consecutive corrected samples are not independent knock-event counts. These channels alone cannot distinguish combustion knock, learned correction, noise sensitivity, or cylinder/hardware causes, and do not establish damage. They justify a separate low-RPM/light-load investigation rather than treating every event as the same high-load cylinder-6 issue. Rich bank-average AFR does not establish equal fueling of all cylinders.

## What the pressure resampling can and cannot explain

At fixed **differential-pressure axis coordinates**, the changed factor alone is approximately +10.65% at 90 bar, +8.61% at 100 bar, +1.24% at 150 bar and -3.58% at 200 bar relative to v4. These are correction-factor changes, not final duration or AFR predictions.

Near-idle logged rail pressure is roughly 90 bar and pull pressure roughly 200 bar, but the ECU indexes rail-minus-modeled-chamber pressure, so these are only pressure proxies. The resampling could materially alter the previous idle calibration, while its high-pressure change is smaller and opposite in direction. It does not explain the sign reversal at essentially the same idle rail pressure by itself.

## Fault outcome and attribution

No torque-limit channel contains 2048 in either file. Other states, including 1, 4 and 8, are present. This does not establish all torque intervention is absent.

The user reports 1F0525 did not return. There is no October 16 diagnostic-code read supplied to independently establish its current/pending/history status. In addition, the lower allowance changed at the same time as the pressure table, and this pull did not match the April operating points. Thus no recurrence is encouraging but **cannot establish that Ti resampling fixed the original monitor mismatch** or that the relaxed threshold has validated margin.

## Recommended next actions

1. **Do not apply a blanket scalar reduction or change MK2TE from this evidence.** First separate cold/startup, warm near-idle, cruise and enrichment/shift behavior. The opposite trim directions and changing LTFT contribution make one global adjustment poorly supported.
2. **Resolve the rich load response before further high-load validation.** Use repeatable moderate-load, single-gear samples after warm-up, without lugging or shift transitions, only within a region already behaving acceptably. The present pull is useful evidence, but not a suitable basis for a direct target/actual-ratio edit.
3. **Repeat comparable warm near-idle conditions with accessory loads recorded and adaptation history preserved.** Record engine-off/restart events and compare temperature/heat-soak history. Investigate purge contribution, injector correction-route changes, pulse-mode/temperature effects and air/fuel measurement consistency as hypotheses, not established causes.
4. **Investigate low-RPM timing corrections separately.** Avoid deliberately provoking them. Check available misfire/rough-running and knock-related diagnostics and basic ignition/injector installation evidence before assuming one defective cylinder or increasing load.
5. **Read and save current/pending/shadow codes before clearing anything.** Keep the present monitor setting documented; do not widen it further to manage the fueling symptoms. No automatic recommendation to restore or further alter it is made by this review.

No calibration edits, fault clearing or adaptation resets were performed.

## Reproducibility

`review_oct16_v5.py` reads the two original CSVs and the local v4/v5 BINs, writes `analysis.json`, and plots `first_log.png` and `pull.png`. Source hashes are retained in the JSON. Median summaries are sample based, not time-weighted; coverage estimates exclude gaps over 0.5 s. Filters and shift exclusions are explicit in the script. Target-AFR extremes during overrun and transitions are not treated as steady mixture targets for tuning.
