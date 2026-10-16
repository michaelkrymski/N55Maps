"""Read-only correction-routing evidence. Never writes calibration inputs."""
from pathlib import Path
import hashlib, json, os, sys

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
    (0x2F2764,0x2F2A84,'Forward conversion and factor/offset selection'),
    (0x2F2B5C,0x2F2C0E,'Two pause curves and duration-dependent weighting'),
    (0x2F2C9A,0x2F2CDA,'CVO correction calculated and stored separately'),
    (0x2F02AC,0x2F02F2,'Caller selects CVO contribution using same runtime mask'),
    (0x2F520C,0x2F5388,'CVO correction calculation, enable conditions and bounds'),
    (0x2F47B4,0x2F49B2,'CVO cylinder eligibility mask calculation and packed return'),
    (0x2F6CFA,0x2F6EDE,'CVO eligibility bitfield helpers'),
    (0x2F5C26,0x2F5C92,'Successful processing sets completion bit'),
    (0x2F5EF6,0x2F5F18,'Substitute flags clear path'),
    (0x2A295C,0x2A2A10,'Separate injector-adaptation mass/time conversion'),
    (0x2A306A,0x2A3224,'DMC correction calculation and factor/offset copies'),
    (0x2F68E8,0x2F6A4C,'Eligibility result transferred to duration-routing mask'),
    (0xA4080,0xA417C,'Reverse conversion shares pressure/MK2TE/density/delay'),
    (0x361CCA,0x361D5E,'Transfer of adaptation factor/offset arrays to interface'),
    (0x3766EA,0x376796,'Factor interface to final cylinder correction array'),
    (0x2A31DE,0x2A3224,'Manual factor/default and offset-source copies'),
]
b = paths[0].read_bytes()
md = cs.Cs(cs.CS_ARCH_TRICORE,cs.CS_MODE_TRICORE_131)
lines = [str(paths[0]),hashlib.sha256(b).hexdigest(),
         'CALLA segment reconstruction and relocated RAM helper mapping required.',
         'ST.T immediate rendering is unreliable in this decoder; retain raw bytes.']
for lo,hi,label in ranges:
    lines += ['',label]
    for i in md.disasm(b[lo:hi],0x80000000+lo):
        lines.append(f'{i.address:08X} {i.bytes.hex():10} {i.mnemonic:12} {i.op_str}')
(OUT/'injector_correction_code_evidence.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
checks=[]
stock=(Path.home()/'Downloads/WBA1J9C5XGV696132_000021571DAA01.bin').read_bytes()
for p in paths:
    d=p.read_bytes()
    checks.append({'path':str(p),'sha256':hashlib.sha256(d).hexdigest(),
                   'examined_code_identical_to_v6':all(d[a:z]==b[a:z] for a,z,_ in ranges),
                   'CWBMWINJAD':d[0x1D16D4],'CWKLTELIN':d[0x1D16D5],
                   'CVO_substitute_type':d[0x1D14B7],
                   'CVO_temperature_search_priorities':list(d[0x1D14B3:0x1D14B7]),
                   'DMC_manual_test_selector':d[0x194C3D],
                   'separate_conversion_raw_words':{
                       hex(a):int.from_bytes(d[a:a+2],'little') for a in (0x183624,0x18369C)},
                   'separate_conversion_constants_stock':all(d[a:a+2]==stock[a:a+2] for a in (0x183624,0x18369C)),
                   'KLTELIN_outputs_stock':d[0x1D19B2:0x1D19EE]==stock[0x1D19B2:0x1D19EE],
                   'inverse_outputs_stock':d[0x1D180E:0x1D184A]==stock[0x1D180E:0x1D184A]})
(OUT/'injector_correction_checks.json').write_text(json.dumps({'ranges':ranges,'files':checks},indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,indent=2))
