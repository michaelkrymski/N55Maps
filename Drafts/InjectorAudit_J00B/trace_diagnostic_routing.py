"""Read-only J00B monitor-to-DTC routing audit. Writes reports, never BINs."""
from pathlib import Path
import hashlib
import json
import os
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(os.environ['TEMP']) / 'codex-n55-analysis-tools'))
import capstone as cs

paths = [ROOT / p for p in [
    'E85/Revisions/E85v6(InjectorsFix).bin',
    'E85/Revisions/E85v11(FuelHoning).bin',
    'E85/Revisions/E85v12(FuelHoning).bin',
    'FlexFuel/Revisions/FlexFuelv4(FuelScalar-93).bin',
]]
ranges = [
    (0x62730, 0x62800, 'Bounds write failure flag in scratch field +26'),
    (0x62CCA, 0x62E8C, 'Monitor debounce, reaction and status bits'),
    (0x771BA, 0x77282, 'Status bits to diagnostic reporting handles'),
    (0x8AD1C, 0x8AF64, 'Diagnostic reporter masks handle to low 12-bit event index'),
    (0xB612A, 0xB622E, 'Internal reaction context capture and system/debug reaction'),
    (0xD79DC, 0xD79F0, 'Manufacturer/OBD two-byte DTC table selector'),
    (0xD7B88, 0xD7BA2, 'Fault-type byte getter'),
    (0x8D80A, 0x8D86A, 'Stored event to assembled 24-bit DTC'),
    (0xDF400, 0xDF46E, 'Explicit manufacturer DTC assembly and output array'),
]
b = paths[0].read_bytes()
md = cs.Cs(cs.CS_ARCH_TRICORE, cs.CS_MODE_TRICORE_131)
lines = [f'Source: {paths[0]}', f'SHA256: {hashlib.sha256(b).hexdigest()}',
         'CALLA destinations require segment reconstruction from bytes.',
         'Capstone ST.T immediate value display is unreliable: preserve raw bytes.',
         'For example 80062CFE / 80062D04 differ in the encoded value bit, despite identical printed operands.']
for lo, hi, label in ranges:
    lines += ['', f'{label}; file {lo:06X}..{hi-1:06X}']
    for ins in md.disasm(b[lo:hi], 0x80000000 + lo):
        lines.append(f'{ins.address:08X} {ins.bytes.hex():10} {ins.mnemonic:12} {ins.op_str}')
(OUT / 'diagnostic_routing_code_evidence.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

def u16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def ptr(data, displacement):
    return struct.unpack_from('<I', data, 0x114EA4 + displacement)[0] & 0x0FFFFFFF

checks = []
for path in paths:
    data = path.read_bytes()
    manufacturer_base = ptr(data, 0x20C)
    fault_type_base = ptr(data, 0x22C)
    events = []
    for name, handle_offset, reaction in [('Gkc', 0x30872, 0x3031), ('Rlc', 0x30868, 0x3032)]:
        handle = u16(data, handle_offset)
        index = handle & 0xFFF
        word_address = manufacturer_base + 2 * index
        byte_address = fault_type_base + index
        word = u16(data, word_address)
        fault_byte = data[byte_address]
        events.append({'branch_name_from_older_definitions': name, 'internal_reaction_id': hex(reaction),
                       'handle_file_offset': hex(handle_offset), 'handle': hex(handle),
                       'event_index': index, 'event_index_hex': hex(index),
                       'manufacturer_word_offset': hex(word_address), 'manufacturer_word': hex(word),
                       'fault_type_offset': hex(byte_address), 'fault_type_byte': hex(fault_byte),
                       'assembled_dtc': f'{((word << 8) | fault_byte):06X}'})
    checks.append({'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                   'all_examined_code_identical_to_v6': all(data[a:z] == b[a:z] for a,z,_ in ranges),
                   'manufacturer_table_base': hex(manufacturer_base), 'fault_type_table_base': hex(fault_type_base),
                   'gkc_rlc_debounce_and_reset_limit_bytes': list(data[0x1B88A7:0x1B88AB]),
                   'events': events})
result = {'files': checks, 'code_ranges': ranges,
          'dtc_assembly': '(manufacturer_word << 8) | fault_type_byte',
          'no_bin_files_modified': True}
(OUT / 'diagnostic_routing_checks.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(checks, indent=2))
