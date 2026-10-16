# Saved FlexFuel draft: KLTIKRPR entry check

## Latest verification after full-precision import

The saved working BIN now matches the provisional proposal **byte-for-byte across all 4 MB**. All 20 KLTIKRPR raw words match exactly, with 37 changed bytes from the embedded original FlexFuelv4 base and no changes outside the output array. The shared pressure axis remains unchanged. The rounding differences described in the earlier inspection below have been resolved.

Latest draft JSON SHA-256: `ddeefd4465e48337236ca101c088026e89f8dfd0b1754952cfd6f5b48b2eaea2`.

Latest working BIN SHA-256: `1b815f9b5e7c39a043c236db17fbae899f3c0b565efc5eae9f066566eac28f17`.

This remains verification of file contents, not donor applicability, endpoint assumptions, checksum/signature validity or flash safety. The draft was not modified during verification.

## Earlier inspection, superseded where noted above

Read-only check of `Drafts/FlexFuelDrafts.json`, session `a2dc31cbd5b546e6b0dcc66710f260d1`.

The Converter CLI `show` command read the saved working table. An independent raw-byte comparison checked the embedded source/working BINs against the original FlexFuelv4 and the provisional proposal. No draft or calibration was changed.

- Embedded source equals `FlexFuel/Revisions/FlexFuelv4(FuelScalar-93).bin` exactly.
- Exactly 37 bytes changed from that base, all within the 40-byte KLTIKRPR output array.
- Shared pressure axis, delay table, scalar, MK2TE, KLTELIN, KLHDEV, selector bytes and monitors are byte-identical to the base.
- All 20 values are in their intended columns and remain monotonic decreasing.
- Eighteen values differ from the exact provisional proposal due to reduced decimal precision. Two match exactly.
- Maximum relative difference from the proposal is 0.2288704% at 45.25 bar differential pressure.
- The temporary erroneous edit at column 18 was subsequently corrected in the saved working bytes.

## Exact comparison

Pressure below is differential pressure in bar; the CLI axis is displayed in MPa (multiply by 10 for bar). Factors use exact raw / 4096 scaling; the XDF uses a slightly rounded scale constant.

| Column | Pressure (bar) | Saved factor | Proposed factor | Saved raw | Proposed raw | Difference |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 6.58007812 | 6.57763672 | 26952 | 26942 | +0.037117% |
| 2 | 2.7 | 6.03002930 | 6.02539062 | 24699 | 24680 | +0.076985% |
| 3 | 3.25 | 5.59008789 | 5.59155273 | 22897 | 22903 | -0.026197% |
| 4 | 4.05 | 4.96997070 | 4.97363281 | 20357 | 20372 | -0.073630% |
| 5 | 5.25 | 4.37011719 | 4.37475586 | 17900 | 17919 | -0.106033% |
| 6 | 6.8 | 3.84008789 | 3.84008789 | 15729 | 15729 | +0.000000% |
| 7 | 8.8 | 3.37988281 | 3.37792969 | 13844 | 13836 | +0.057820% |
| 8 | 11.45 | 3.01000977 | 3.00952148 | 12329 | 12327 | +0.016225% |
| 9 | 15 | 2.61010742 | 2.61157227 | 10691 | 10697 | -0.056090% |
| 10 | 19.75 | 2.32006836 | 2.32104492 | 9503 | 9507 | -0.042074% |
| 11 | 26.05 | 1.95996094 | 1.96337891 | 8028 | 8042 | -0.174086% |
| 12 | 34.3 | 1.71997070 | 1.72045898 | 7045 | 7047 | -0.028381% |
| 13 | 45.25 | 1.48999023 | 1.49340820 | 6103 | 6117 | -0.228870% |
| 14 | 59.65 | 1.29492188 | 1.29541016 | 5304 | 5306 | -0.037693% |
| 15 | 78.75 | 1.12988281 | 1.12768555 | 4628 | 4619 | +0.194847% |
| 16 | 104.5 | 0.97973633 | 0.97973633 | 4013 | 4013 | +0.000000% |
| 17 | 139.35 | 0.84399414 | 0.84423828 | 3457 | 3458 | -0.028918% |
| 18 | 155 | 0.80004883 | 0.80078125 | 3277 | 3280 | -0.091463% |
| 19 | 186.35 | 0.72900391 | 0.72973633 | 2986 | 2989 | -0.100368% |
| 20 | 250 | 0.62500000 | 0.62573242 | 2560 | 2563 | -0.117050% |

## Interpretation

The saved draft implements the intended resampling shape, with small additional manual-rounding differences. Use the full-precision proposal values to reproduce its exact raw words. No correction was made automatically because this request was to inspect the draft.

This confirms table placement and the scope of the saved edits. It does not validate donor applicability, the four modeled endpoints, the complete injector model, ECU checksums/signatures or flash safety. The CLI export_ready flag denotes application export state, not vehicle/calibration validation.

Saved draft file SHA-256: `1e7fc393dfa9128797a8802435d311d4c298ddd60760464ca73a475c53a7a7a0`
Working BIN SHA-256: `93fe8473e9fe842104fc9a277b11b1a933cd5e91b36d89675eadd0088d990ac3`
