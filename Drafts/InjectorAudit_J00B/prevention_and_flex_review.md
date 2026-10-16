# Prevention priorities and saved flex-fuel configuration

Read-only follow-up, 2026-10-16. No calibration or saved draft was edited.

## Pressure-table correction

The current saved draft working BIN still hashes to `1b815f9b5e7c39a043c236db17fbae899f3c0b565efc5eae9f066566eac28f17` and matches the provisional resampling candidate byte-for-byte. Its only changes from the embedded base are 37 bytes within KLTIKRPR's 20 output words. This verifies the saved values, not a complete injector-model fix or the prevention of 1F0525.

The retained N55 shared axis is intentional. The donor pressure function was resampled onto it, with documented provisional endpoint assumptions. Do not confuse entering physical scaled factors with entering raw unsigned storage words.

## Injector-model question

The original transfer changed only KLHDEV input/output and KLTIKRPR output. The audited normal duration path selects KLTELIN, while MK2TE and other model components remained N55. This is an incomplete characterization transfer, although it does not prove that every retained N55 parameter is wrong for the installed injectors. Donor hardware applicability and the interaction with coding/CVO remain unresolved.

A scalar's distance from unity alone is not a fault test. The useful question is whether it is compensating for injector conversion, ethanol composition, or another model error. Those have different dependencies. Correcting lambda through the normal fuel-mass scalar can also change the monitor input; lambda tracking alone does not establish monitor consistency.

## Saved draft flex-fuel inspection

Read through the Converter's read-only session API and CLI using the XDF embedded in `Drafts/FlexFuelDrafts.json`. Selected values/descriptions are preserved in `flex_configuration_check.json`.

| Item | Saved value |
|---|---|
| Enable FlexFuel, slots 1–4 | 1, 0, 0, 0 |
| Sensor preset | 1, labelled MHD CAN ECA |
| Static ethanol, slots 1–4 | 0, 85, 85, 85 |
| Separate scalar interpolation enable | 0 |
| Fuel interpolation curves, all four slots | all zero |
| Load/timing/knock interpolation curves | all zero |
| FF / FF#2 scalar outputs | stock-shaped, approximately 1–1.05; unity at higher load |
| Unused separate scalar interpolation fields | repeated raw-looking 195 axis labels and approximately 1.5354 factors |

Under the embedded XDF's documented behavior, zero fuel interpolation selects the active slot's running-fuel tables, including its scalar when separate scalar interpolation is disabled. Therefore the saved file does not demonstrate a complete ethanol-dependent running-fuel blend. Static overrides on slots 2–4 are consistent with intentional fixed-E85 slots; they do not establish sensor-following flex operation in those slots. Startup/warmup compensation is a separate path.

The unusual unused fields also require caution about initialization/definition applicability. Prior executable comparison found no application-code differences outside the calibration region in the supplied FlexFuelv4 versus the vehicle stock reference. File inspection cannot determine all flash-time processing or the actual live MHD custom behavior. Do not conclude from these reads alone that runtime fuel compensation is absent, or that filling FF scalar maps with arbitrary ethanol multipliers is the solution.

MHD's public guide distinguishes Ethanol Content (CAN) from Ethanol Content (Active), and identifies Fuel/Load/Timing/Knock Interpolation logging channels. Those provide the direct check of sensor input, overrides and live blending: https://mhd-tuning.atlassian.net/wiki/spaces/MFS2/pages/11763743/MHD%2BSuite

## E10 baseline

An E10 pump-gas endpoint is reasonable if it is the explicitly chosen and validated composition baseline. It is distinct from an E13 tank composition. E10 to E13 is three ethanol percentage points, not automatically three percent additional fuel or three percent scalar. The necessary correction depends on the fuel model and must not be counted both in the base calibration and an active ethanol correction. Pump octane/location alone does not establish the exact tank composition.

## Recommended order

1. Establish a coherent injector mass-to-duration model for the installed hardware, including the active forward curve, inverse/adaptation model, pressure factor, base conversion and offsets. Do not transplant MK2TE alone.
2. Validate the pump-gas endpoint at measured composition using lambda target/actual, STFT/LTFT, actual/target rail pressure, RPM/load, fuel temperature if available, and injector duration if supported. Record adaptation-reset/relearn history. Start at low load and expand only after corrections and pressure behavior are understood; do not deliberately reproduce the cutoff.
3. Finish the monitor reference/trim trace to identify why scalar changes affect its margin. Keep monitor protections unchanged.
4. Verify CAN ethanol, active ethanol, selected map and interpolation channels together. Validate the ethanol endpoint and intermediate blends separately before relying on automatic flex operation. A live ethanol readout alone does not prove running-fuel compensation.

The April events predate flex fuel, so missing FF endpoint calibration cannot by itself explain those events. The current flex setup is a separate validation task.
