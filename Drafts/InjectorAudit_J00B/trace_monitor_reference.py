"""Read-only evidence extraction for the current J00B monitor reference branch."""
from pathlib import Path
import hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ['TEMP'])/'codex-n55-analysis-tools'))
import capstone as cs
paths=[ROOT/p for p in ['E85/Revisions/E85v6(InjectorsFix).bin',
 'E85/Revisions/E85v11(FuelHoning).bin','E85/Revisions/E85v12(FuelHoning).bin',
 'FlexFuel/Revisions/FlexFuelv4(FuelScalar-93).bin']]
ranges=[(0x62052,0x62800,'Input selection, reference arithmetic and first-bank bound checks'),
 (0x616A6,0x61914,'Upstream base-input preparation'),
 (0xA4E08,0xA4F70,'Charge and additive-input interfaces'),
 (0xA8A62,0xA8A8A,'Base fuel input conversion'),
 (0xA8B9C,0xA8BC2,'Learned adaptation interface'),
 (0xA8D46,0xA8D98,'Pre-scalar charge/correction interface'),
 (0x362916,0x3629DA,'Additional fuel-term interface and complement check'),
 (0x28DF16,0x28E2EC,'Normal scalar calculation for comparison')]
b=paths[0].read_bytes();md=cs.Cs(cs.CS_ARCH_TRICORE,cs.CS_MODE_TRICORE_131)
lines=[str(paths[0]),hashlib.sha256(b).hexdigest(),
 'CALLA address segments need reconstruction; ST.T value rendering is unreliable.']
for lo,hi,label in ranges:
 lines += ['',label]
 for i in md.disasm(b[lo:hi],0x80000000+lo):
  lines.append(f'{i.address:08X} {i.bytes.hex():10} {i.mnemonic:12} {i.op_str}')
(OUT/'monitor_reference_code_evidence.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
checks=[]
for p in paths:
 d=p.read_bytes()
 checks.append({'path':str(p),'sha256':hashlib.sha256(d).hexdigest(),
  'examined_code_identical_to_v6':all(d[a:z]==b[a:z] for a,z,_ in ranges),
  'CWLASP_UM':d[0x1B84BA],'CWLRADP_UM':d[0x1B84BB],'CW_VARTE_UM':d[0x1B84BD],
  'reference_final_additive_raw':int.from_bytes(d[0x1B88BA:0x1B88BC],'little',signed=True),
  'bounds_raw':[d[0x1B84BF],d[0x1B84C0],d[0x1B88AD]],
  'base_consistency_tolerance_raw':d[0x1B84BE]})
(OUT/'monitor_reference_checks.json').write_text(json.dumps({'ranges':ranges,'files':checks},indent=2)+'\n')
print(json.dumps(checks,indent=2))
