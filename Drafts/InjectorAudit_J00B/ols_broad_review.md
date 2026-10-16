# WinOLS export: broader injector and fuel-monitor review

2026-10-16. This investigation reads the supplied export, the older A2L, stock J00B reference, v6 executable and saved FlexFuel draft. No calibration, draft, XDF or monitor setting was changed. The user's established flashing workflow is outside this review.

## Findings that change the investigation

The useful model is broader than KLTIKRPR and KLHDEV. There are at least three distinct sets of calculations to distinguish:

1. The selected injector-duration conversion, including KLTELIN, its inverse, MK2TE, FKKVS, pressure and pause corrections.
2. Injector coding and adaptation, including CVO opening-time/delay models and a separate BMW `KL_INJAD_*` family.
3. An independently calculated mixture-monitor reference, including its correction-map selection, learned-trim treatment, multiplicative bounds, additive tolerance and error counters.

The pressure-table resampling addresses one confirmed indexing problem in the first set. It does not establish agreement among all three sets.

The new export contains **9,476 definitions and 8,664 distinct nonempty symbols**. A targeted screen selected **95 unique definitions** in relevant families. Twenty-five local J00B mappings were checked against the vehicle-named stock reference; every output value in those checked definitions matches the CSV to its stated precision after correcting the exported value traversal order where applicable. This is a targeted check, not a validation of every definition or every CSV axis.

## Important source-format issue

The CSV uses semicolons and Windows-1252 encoding. It must not be treated as an immediately usable J00B map pack.

For the checked `eZweiInv` maps, exported field values traverse columns before rows. Reordering them into physical BIN order is necessary before comparing the complete grid. A direct flattened comparison produces false differences.

More importantly, some exported axis-value fields use raw values from the opposite axis with the current axis's scaling. A concrete example is `IVGdiCtl_CvoAdpn_DftVal_tantot_GM`:

| Quantity | Correct J00B coordinates recovered from mapped bytes and A2L scaling |
|---|---|
| Pressure | 75.52, 99.84, 154.88, 170.24, 199.68 bar |
| Temperature | 20.25, 87.75, 142.50, 143.25 degrees C |

Its CSV pressure-value field instead contains `11.648 23.168 32.512 32.640`: these are exactly the temperature-axis raw bytes multiplied by the pressure factor 0.128. Its CSV temperature-value field contains `-3.75 10.50 42.75 51.75 69.00`: these are exactly the pressure-axis raw bytes multiplied by 0.75 and offset by -48.

The field values for this map do match the stock J00B data after transposition. The axis-value fields therefore need separate validation. This is a source interpretation issue, not evidence that the ECU's actual pressure or temperature axes are corrupt. The CSV's scalar dummy axes displaying 48 are also not operating breakpoints.

## Tables previously receiving too little attention

| Priority | Tables | J00B finding | Why useful |
|---|---|---|---|
| 1 | KLTELIN, InjVvG_tiIvsCvo_T, MK2TE | Selected forward curve, inverse curve and conversion factor remain stock N55 | These describe the active conversion more directly than an unselected KLHDEV curve |
| 2 | InjSys_tiOpenInjCvo_M; IVGdiCtl_CvoAdpn_DftVal_tantot_GM | Both complete output arrays match stock N55 | Separate CVO opening-time and default valve-opening-delay models can influence adaptation behavior |
| 3 | CWBMWINJAD; InjVvG_CvoAdpn_enable_dti_C; IVGdiCtl_CvoAdpn_enable_OnlineCtrl_C; IVGdiCtl_CvoAdpn_enable_ReAdpn_C | Stored values are respectively 2, 1, 1, 0 | A selector or enable is not proof that a live operating condition activated the branch; these are concrete gates to trace |
| 4 | KL_INJAD_KLTIKRPR, KL_INJAD_KLHDEV, KL_INJAD_KLFDTFUEL; K_INJAD_MK2TE, K_DMC_MK2TE | The first three arrays are separately mapped and remain stock N55; the two conversion constants are additional A2L leads, not yet mapped here | Injector adaptation has its own conversion/model tables; these are distinct from normal KLTIKRPR and KLHDEV |
| 5 | KLTIKRTP, KLTIKRTPB, FKKVS | All remain stock N55; FKKVS is not uniformly 1 | Pause-dependent and duration-dependent corrections can matter even with nearly constant rail pressure |
| 6 | S_LRADAP_MDRK; FRMAX/FRMIN; KF_FLRADAP_MX/MN | S_LRADAP_MDRK remains 2; FRMAX/FRMIN remain approximately 1.329987/0.670013; adaptation-limit maps need further mapping checks | Separate learned-trim routing and controller limits from the fuel-mass monitor's limits |
| 7 | KFFKKORRF_UM, MoFAirFl_rkCorFacMst_MAP, Mo_cwMstSlave_C, FRKMAX_UM, FRKMIN_UM, RKO_UM, MoF_ctGkc_C/MoF_ctRlc_C | The located static branch selects the 8x8 monitor map; bounds include an additive allowance and counter logic | Gives a concrete monitor calculation to investigate without modifying protection |

The selected-model and CVO/adaptation findings are reasons to investigate consistency, not instructions to copy every donor table. A separate table can serve a different operating mode or a different injector-control architecture. Its name alone does not establish when it is used.

### Selected forward/inverse model

J00B locations checked:

- KLTELIN outputs: `0x1D19B2`, 30 values.
- Inverse linear curve outputs: `0x1D180E`, 30 values.
- MK2TE: `0x1D1A8C`, raw 8803.
- CWKLTELIN: `0x1D16D5`, value 1.

These match the stock J00B reference. The CSV independently reports CWKLTELIN=1 at its older-software location. The prior executable audit establishes that the located duration routine selects KLTELIN for that stored value.

The examined N63 donor A2L exposes KLHDEV and MK2TE but does not expose the same named KLTELIN/CVO model set. That absence in the definition file does not prove hardware incompatibility or absence of all equivalent donor logic. It does mean that treating the donor data as a complete replacement for the N55's selected calculation is unsupported.

### CVO is a separate learned correction system

The J00B CVO calibration group is reached through `[A9 + 0x6A8]`, whose default pointer resolves to `0x801D13D8`. The code references the online-control enable at group offset `0x9D` (`0x1D1475`) and the default opening-delay table at group offset `0x74` (`0x1D144C`).

Verified stored values include:

| Parameter | Value |
|---|---:|
| CVO duration-correction enable | 1 |
| Online-control enable | 1 |
| Readaptation enable | 0 |
| Total duration-correction lower/upper bounds | -150 / +150 microseconds |
| Integrator lower/upper bounds | -80 / +80 microseconds |
| Default valve-opening delay outputs | 430–447 microseconds |

These are distinct from lambda STFT/LTFT. The logs do not expose the active learned CVO values, so a near-zero LTFT does not establish that every injector-related correction is zero.

The duration routine reads cylinder-indexed multiplicative correction data at `0xC0002434` and additive offset data at `0xC000204E` in conditional branches. Their local correspondence to older A2L `fakkorteall_w` and `tiofsinjad_w` is supported by the same neighboring injector-variable layout. The complete origin, coding contribution, live enable conditions and learning/reset sequence are not yet resolved.

### Separate adaptation curves

The distinct BMW adaptation family includes:

| Output array | J00B address | Count | Draft versus stock |
|---|---:|---:|---|
| KL_INJAD_KLTIKRPR | `0x194B48` | 12 | Identical |
| KL_INJAD_KLHDEV | `0x194BC2` | 48 | Identical |
| KL_INJAD_KLFDTFUEL | `0x194C2C` | 4 | Identical |

These tables were not changed by the v5-to-v6 transfer or the current KLTIKRPR resampling. They provide a concrete possible source of disagreement between normal commanded fueling and an adaptation calculation. Whether that disagreement is active and significant must be established from execution paths, not inferred from retained stock values alone.

The older A2L also describes `K_DMC_MK2TE` as a Data Matrix Code mass-to-time conversion constant and includes `K_INJAD_MK2TE`. They are not present under those symbols in this CSV and were not assigned J00B addresses by assumption.

## Monitor map selection resolved for the located static path

The default `[A9 + 0x50]` pointer resolves to `0xA01B84BA` (uncached flash alias of `0x801B84BA`). This supplies the monitor's mixture-control calibration group.

At `0x800624F8`, the code reads a separate master/slave configuration through `[A9 + 0x0C]`. Its default byte is `Mo_cwMstSlave_C` at file offset `0x1B8468`, value **0** in the inspected BINs.

For this value, the bank-1 reference branch passes the 8x8 KFFKKORRF record at group offset `0x5A` to the map lookup. Its outputs are at **`0x1B8526`**. The 16x16 master/slave maps are alternatives selected by other configuration branches, not the selected path for the stored configuration.

The selected 8x8 map ranges from 1.0 to 1.046875 and is unity across its high-load columns. This does not by itself establish the full monitor reference or reproduce a logged fault. It does resolve why the existence of all-ones 16x16 monitor maps was not sufficient to identify the active correction.

The original CSV's lack of FRKMAX_UM, FRKMIN_UM and several monitor counters does not mean those calibrations are absent. They are defined by the older A2L and their locally translated locations are referenced by J00B code.

## Monitor bounds and counters

The located comparison stage uses the following stored parameters:

| Parameter | J00B file offset | Value |
|---|---:|---:|
| FRKMAX_UM | `0x1B84BF` | 1.328125 |
| FRKMIN_UM | `0x1B84C0` | 0.8828125 |
| RKO_UM | `0x1B88AD` | raw 14, equivalent to 10.5 relative-fuel-mass units under the A2L conversion |
| MoF_ctGkc_C | `0x1B88A7` | 13 |
| MoF_ctRlc_C | `0x1B88A8` | 13 |

For positive comparison quantities, the identified upper/lower-bound stage is represented by:

```text
upper_bound_raw = trunc(reference_raw * 170 / 128) + 224
lower_bound_raw = trunc(reference_raw * 113 / 128) - 224
```

The code also performs clamping, saturation, sign checks, redundant-storage checks and operating-condition checks. This pseudocode isolates the two multiplicative bounds plus their additive allowance; it is not the complete fault condition. It bounds a fuel-mass comparison quantity, not a scalar table cell. No safe minimum scalar follows from FRKMIN_UM.

The later reaction logic uses byte error counters and compares them with the configured tolerances before incrementing or taking a reaction. At least one pass/inhibit branch explicitly resets its counter. Consequently, a single instantaneous pre-cut lambda observation cannot reconstruct the internal monitoring history. The scheduler period, all release conditions and exact mapping to diagnostic 1F0525 remain unresolved; 13 must not be reported as 13 milliseconds.

The normal-function side is copied/scaled into the monitor's scratch inputs; one traced source path copies a word from `0xD0006050` through a fixed-point conversion into `0xD0002730`. The exact full chain from KF_FRKKORRF_1, all trims and normal fuel-mass outputs into that source still needs end-to-end tracing. No claim is made here that the scalar has been excluded from, or proven fully included in, every monitored quantity.

## Updated priorities

1. Trace the source of the cylinder-specific factor/offset arrays and the live conditions selecting CVO, coding and fallback branches.
2. Trace the selected KLTELIN/inverse pair and separate `KL_INJAD_*` model through normal and adaptation calculations. Determine whether those retained stock models are consistent with the installed injectors.
3. Complete the normal scalar/trim-to-monitor input chain and identify which monitor reaction corresponds to 1F0525. Use the April v11/v12 scalar-only comparison as the controlled operating evidence.
4. Account for normal transient-fuel and learned-trim routing when interpreting whole-pull STFT/LTFT differences. Do not replace those tables merely because they differ from a donor.

No additional calibration edits follow automatically from this review. The current pressure-table correction remains exactly the previously checked draft change.

## Evidence files

- `ols_review_checks.json`: source hashes, all 25 local mapping/value comparisons, axis example and monitor parameters.
- `ols_useful_definitions.json`: the 95 relevant unique CSV definitions with original source line numbers, descriptions, values and metadata.
- `ols_code_evidence.txt`: source hash and byte-annotated J00B instructions supporting the monitor branch/bounds and selected CVO references.
- `review_ols_export.py`: repeatable read-only value and source-preservation checks.
