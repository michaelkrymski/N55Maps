# Provisional KLTIKRPR resampling review

This is the separate review copy requested by the user. Donor hardware applicability remains unconfirmed. It is not a validated flash-ready calibration.

Base: `FlexFuelv4(FuelScalar-93).bin`. Candidate: `FlexFuelv4_KLTIKRPR_resampled_PROVISIONAL.bin`.
Only 37 bytes changed, in all 20 KLTIKRPR output words at `0x1D19EE`. Every byte outside that 40-byte array is identical to the base.

## Method and endpoint assumptions

Both 8AC4543B and 8AC4600B master A2L/HEX pairs were decoded independently. Their pressure axes and factor arrays agree exactly. The base output array equals their donor output array before resampling.

Within donor coverage (4–200 bar differential pressure), interpolate the donor curve linearly at each retained N55 axis point and round to the nearest representable factor (1/4096).

For the three axis points below 4 bar, use donor(4) × stock_N55(p) / stock_N55(4). For the 250-bar point, use donor(200) × stock_N55(250) / stock_N55(200). Stock values at coverage boundaries are themselves linearly interpolated on the stock axis.

This preserves the stock N55 curve's relative shape outside donor coverage, anchored to the donor at each boundary. It is an explicit modeling assumption, not donor data or verified injector characterization. The supplied HEX does not establish donor behavior at those four points.

The extended reference is continuous at 4 and 200 bar. Its representation on the retained, differently spaced N55 axis is an approximation; the reconstructed ECU curve does not pass through every donor knot or necessarily exactly through those boundary anchors.

## Values

| Differential pressure (bar) | Existing factor | Proposed factor | Proposed raw | Basis |
|---:|---:|---:|---:|---|
| 2 | 5.00000000 | 6.57763672 | 26942 | Endpoint assumption |
| 2.7 | 4.47216797 | 6.02539062 | 24680 | Endpoint assumption |
| 3.25 | 4.08251953 | 5.59155273 | 22903 | Endpoint assumption |
| 4.05 | 3.77954102 | 4.97363281 | 20372 | Donor interpolation |
| 5.25 | 3.33325195 | 4.37475586 | 17919 | Donor interpolation |
| 6.8 | 2.67260742 | 3.84008789 | 15729 | Donor interpolation |
| 8.8 | 2.00000000 | 3.37792969 | 13836 | Donor interpolation |
| 11.45 | 1.82568359 | 3.00952148 | 12327 | Donor interpolation |
| 15 | 1.58105469 | 2.61157227 | 10697 | Donor interpolation |
| 19.75 | 1.41430664 | 2.32104492 | 9507 | Donor interpolation |
| 26.05 | 1.29101562 | 1.96337891 | 8042 | Donor interpolation |
| 34.3 | 1.19531250 | 1.72045898 | 7047 | Donor interpolation |
| 45.25 | 1.11791992 | 1.49340820 | 6117 | Donor interpolation |
| 59.65 | 1.05419922 | 1.29541016 | 5306 | Donor interpolation |
| 78.75 | 1.00000000 | 1.12768555 | 4619 | Donor interpolation |
| 104.5 | 0.91015625 | 0.97973633 | 4013 | Donor interpolation |
| 139.35 | 0.84204102 | 0.84423828 | 3458 | Donor interpolation |
| 155 | 0.78710938 | 0.80078125 | 3280 | Donor interpolation |
| 186.35 | 0.74194336 | 0.72973633 | 2989 | Donor interpolation |
| 250 | 0.70361328 | 0.62573242 | 2563 | Endpoint assumption |

## Reconstructed-curve comparison

These compare one correction factor, not final fueling or lambda error.

| Differential pressure (bar) | Existing factor | Proposed factor | Donor factor | Proposed vs donor |
|---:|---:|---:|---:|---:|
| 4 | 3.79847717 | 5.01225281 | 5.00000000 | +0.2451% |
| 10 | 1.92106427 | 3.21110333 | 3.20112305 | +0.3118% |
| 25 | 1.31156413 | 2.02298991 | 2.00000000 | +1.1495% |
| 50 | 1.09690094 | 1.42809635 | 1.41430664 | +0.9750% |
| 100 | 0.92585710 | 1.00559153 | 1.00000000 | +0.5592% |
| 150 | 0.80465942 | 0.81466529 | 0.81457520 | +0.0111% |
| 180 | 0.75109182 | 0.74412661 | 0.74194336 | +0.2943% |
| 200 | 0.73372332 | 0.70743227 | 0.70361328 | +0.5428% |
| 250 | 0.70361328 | 0.62573242 | Outside coverage | Unverified |

Maximum absolute candidate/reference relative deviation within 4–200 bar is 1.9106% at 14 bar. This includes axis-spacing/interpolation effects and integer quantization. Extrema were checked at the union of both curves' breakpoints.

## Verification and limits

- Shared N55 axis and pressure-dependent delay outputs remain byte-identical.
- MK2TE, KLTELIN, KLHDEV, scalar maps, selector bytes and monitor parameters remain byte-identical.
- Proposed outputs are monotonic decreasing and fit unsigned 16-bit storage.
- Input hashes, output hash, every changed byte offset, exact raw words and donor provenance are recorded in `manifest.json`.
- ECU checksums/signatures were not recalculated or validated. This copy must not be described as ready to flash.
- This corrects the donor indexing in the stated approximation; it does not validate the full injector model or establish a fix for richness or 1F0525.

Base SHA-256: `d9cf1757971ab83804d532ff9eb46c1ce2c3f5e4bbb77a5090698905614dac14`
Candidate SHA-256: `1b815f9b5e7c39a043c236db17fbae899f3c0b565efc5eae9f066566eac28f17`
