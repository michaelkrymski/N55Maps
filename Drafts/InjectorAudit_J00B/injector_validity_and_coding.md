# Injector eligibility and coding: further J00B trace

Read-only analysis, 2026-10-16. No calibration, adaptation setting or saved draft changed. The expanded reproducible evidence is in `trace_injector_corrections.py`, `injector_correction_checks.json` and `injector_correction_code_evidence.txt`.

## Current CVO eligibility branch is now identified

The CVO group at file `1D13D8` has byte `+DF = 2`, file `1D14B7`. The older A2L identifies this field as `IVGdiCtl_CvoAdpn_SubValTyp_C`, use of a substitute value for valve-opening delay. J00B routine `802F47B4` explicitly branches on zero/nonzero; stored 2 selects its nonzero branch at `802F48AA`. The zero branch described previously is therefore an alternative, not the default path in these tunes.

The four temperature-search priority outputs at file `1D14B3` are **3, 1, 2, 4**. These are ranks, not temperatures. Code `802F48C8–802F4908` evaluates the temperature coordinates and priority table, chooses a remaining nonzero minimum rank, then tests that temperature region. It can try up to four regions.

For each chosen region, `802F4924–802F4974` checks five pressure-region enable bytes. For each enabled pressure region it obtains two cylinder masks:

- Completion mask from the pointer-selected flag table through `802F6EA4`.
- A secondary/substitute-related mask through `802F6D40`, from `D00043FC + 5*temperature_index + pressure_index`.

It requires their OR to equal `3F` (all six cylinder bits) for every enabled pressure region. At least one pressure region must be enabled. On success, it selects that temperature region and returns:

```text
eligible_cylinders = (~OR_of_secondary_masks_for_enabled_regions) & 0x3F
packed_result = eligible_cylinders | (selected_temperature_index << 8)
```

If no region qualifies, the initialized return has a zero cylinder mask and temperature index `FF`. The helper's final packing/return is at `802F49A2–802F49B0`. The caller preserves the low byte at `802F6908` and writes it into duration-routing mask `D000381C` at `802F6A4A`.

This establishes that the mask is not simply a per-cylinder permanent switch: complete coverage across the enabled pressure regions and the substitute-related state affect it. It also means that "CVO enabled" is not equivalent to "CVO duration correction active on every cylinder."

The interpretation of the two underlying flag families is supported by their use and the older CVO definitions; exact life-cycle semantics of every setter are not yet fully reconstructed. This is not a live record of completion or failure on the vehicle.

## Completion and clearing are separate from lambda trims

The completion-bit setter `802F6E26` updates a cylinder bit in a temperature/pressure-selected table. Its pointer list at file `33608` contains `D0018AEE`, `D0018B16`, `D0018B3E`, `D0018B66`. Code `802F5C6E–802F5C7E` calls that setter after correction processing in the CVO learning region.

The secondary mask has distinct read/write helpers: `802F6D40` reads it and `802F6D50` writes it, including an additional mirror selected through a pointer list. Code `802F5EF6–802F5F16` explicitly writes zero across its four-by-five cells. Another initialization path clears the final routing mask at `802F5FB2–802F5FB6`.

These are separate states from lambda-controller STFT/LTFT. The code found here does not establish that a particular MHD or ISTA reset command clears all of them; the external reset-command routing and persistence/reinitialization behavior still require tracing. Do not infer cleared CVO state from LTFT being near zero.

## Injector-code-derived offset calculation is now located

In the normal adaptation/coding region, `802A306A–802A31DA` loops over the requested cylinder bits. It reads a per-cylinder input word at `D000A396 + 2*cylinder_index`, with a manual/test override controlled at file `194C3D`. That override is zero in the examined tunes. When the input is zero, or the test selector is set, the code uses the manual coding-input array at file `183626` instead.

The older definitions identify the associated quantities as DMC injector coding and reference flow. The J00B instructions independently establish the per-cylinder input, reference subtraction, mass-to-time conversion, curve use and offset output; exact decoding of the ISTA-entered code into this upstream input has not yet been traced.

Key J00B constants in that calculation are:

| Object, named by local older-definition alignment | File offset | Raw word | Evidence |
|---|---|---:|---|
| DMC reference flow | `183698` | 17777 | Subtracted from the coding input at `802A30E0–802A30E4` |
| DMC reference rail pressure | `18369A` | 19661 | Passed into the adaptation pressure curve at `802A3104–802A310E` |
| DMC mass-to-time conversion, K_DMC_MK2TE | **`18369C`** | **11534** | Multiplies the coding-input deviation at `802A30EE–802A30F2` |
| Separate K_INJAD_MK2TE | **`183624`** | **1137** | Loaded and multiplied in `802A29B4–802A29C0` |

This local constant block differs from the older A2L by **+4**, whereas nearby calibration records previously required +58. The provisional locations `183678` and `1836F0` in the previous report are withdrawn. The reference-flow, reference-pressure, temperature, offset limits and conversion sequence provide the local cross-check; no global address translation is used.

The DMC path also references separate adaptation curves, including pressure record `194B2E`, density record `194C22` and HDEV record `194B60`. These are not the normal KLTIKRPR/KLTELIN records.

The computed per-cylinder output is stored at `D001DE36 + 2*cylinder_index`. Code `802A3210–802A321E` duplicates it into both offset words for that cylinder at `D0005FD8`; the previously traced interface then copies that array to `C000204E`, which the normal duration route reads. This closes the source link for one contributor to the cylinder-characteristic offsets. It does not prove that all offset contributions or code parsing have been reconstructed.

The same copy stage loads the factor array at `D0005F8A` from manual/default calibration `194C54` (unity words in the inspected file). Subsequent factor normalization and any other writers remain separate questions. This is not proof that the final applied factor is always unity.

## Meaning for model consistency

The normal forward/reverse conversion and the DMC/adaptation calculations have different calibration families and conversion constants. Therefore adjusting the normal pressure curve or MK2TE alone does not automatically update the injector-code-derived correction calculation. Conversely, the separate constants have different representations and roles; their raw values must not be copied between families.

All newly examined executable ranges match in v6, April v11, April v12 and FlexFuelv4. Their CVO substitute mode, temperature priorities, manual DMC selector, separate conversion constants, and selected forward/inverse stock curves also agree. The separate conversion constants remain byte-identical to the vehicle-named stock reference.

This provides a concrete model-consistency question, not proof that these retained constants are incorrect for Bosch 0261500136. The remaining priorities are the upstream injector-code decoding, correction scaling and bounds, and physical applicability of the donor characterization. No replacement value or selector change is justified by this step alone.
