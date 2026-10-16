"""Read-only BIN analysis; writes evidence files only, never calibration files."""
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(os.environ['TEMP']) / 'codex-n55-analysis-tools'))
import capstone as cs

paths = [
    ROOT / 'E85/Revisions/E85v6(InjectorsFix).bin',
    ROOT / 'E85/Revisions/E85v11(FuelHoning).bin',
    ROOT / 'E85/Revisions/E85v12(FuelHoning).bin',
    ROOT / 'FlexFuel/Revisions/FlexFuelv4(FuelScalar-93).bin',
]
ranges = [
    (0x214A2, 0x21510, 'RAM helper C000501A: signed multiply/divide and saturation'),
    (0x2264FE, 0x226514, 'Default scalar pointer initialization'),
    (0x28DF16, 0x28E2EC, 'Normal fuel calculation and scalar multiplication'),
    (0x28F036, 0x28F1D0, 'Normal output selection and overrides'),
    (0xA85F0, 0xA86B0, 'Normal output conversion to monitor interface'),
    (0xA8B9C, 0xA8BC2, 'Learned-correction interface conversion'),
    (0x62080, 0x62210, 'Monitor normal input and adaptation selection'),
    (0x624F8, 0x62804, 'Monitor correction selection, reference and bounds'),
]
data = paths[0].read_bytes()
md = cs.Cs(cs.CS_ARCH_TRICORE, cs.CS_MODE_TRICORE_131)
lines = ['J00B scalar-to-monitor evidence', f'Source: {paths[0]}',
         f'SHA256: {hashlib.sha256(data).hexdigest()}',
         'Flash addresses = 80000000 + file offset.',
         'CALLA segment must be reconstructed from instruction bytes.',
         'RAM helper file 214A2 is relocated to C000501A.']
for lo, hi, label in ranges:
    lines += ['', f'{label}; file {lo:06X}..{hi-1:06X}']
    for ins in md.disasm(data[lo:hi], 0x80000000 + lo):
        lines.append(f'{ins.address:08X} {ins.bytes.hex():10} {ins.mnemonic:12} {ins.op_str}')
(OUT / 'scalar_monitor_code_evidence.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
checks = []
for path in paths:
    other = path.read_bytes()
    checks.append({'path': str(path), 'sha256': hashlib.sha256(other).hexdigest(),
                   'code_ranges_identical_to_v6': all(other[a:b] == data[a:b] for a,b,_ in ranges),
                   'selectors': {hex(a): other[a] for a in (0x194A83, 0x19510D, 0x1B84BB)}})
stock_path = Path.home() / 'Downloads/WBA1J9C5XGV696132_000021571DAA01.bin'
stock = stock_path.read_bytes()
ff = paths[-1].read_bytes()
changed = [i for i,(a,b) in enumerate(zip(stock, ff)) if a != b]
result = {'files': checks, 'ranges': ranges,
          'stock_path': str(stock_path), 'stock_sha256': hashlib.sha256(stock).hexdigest(),
          'stock_and_ff_lengths': [len(stock), len(ff)],
          'ff_vs_stock_changed_bytes': len(changed),
          'ff_vs_stock_changed_bytes_outside_180000_1fffff': sum(not 0x180000 <= i < 0x200000 for i in changed)}
(OUT / 'scalar_monitor_checks.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
