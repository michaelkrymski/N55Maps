"""Isolated, read-only comparison of injector mass/time conversion stages.

Not a delivered-fuel simulation. Writes JSON/Markdown reports only.
"""
from pathlib import Path
import base64
import hashlib
import json
import re
import struct
from bisect import bisect_right
from build_provisional_resample import read_hex, get_bytes

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
session_path = ROOT / 'Drafts/FlexFuelDrafts.json'
session_bytes = session_path.read_bytes()
draft = base64.b64decode(json.loads(session_bytes)['working_bin_b64'])
manifest = json.loads((OUT/'Resampling_PROVISIONAL/manifest.json').read_text())
donor = manifest['donors'][0]
definition = Path(donor['a2l']).read_text(errors='replace')
memory = read_hex(Path(donor['hex']))

def address(symbol):
    match = re.search(r'/begin CHARACTERISTIC\s+' + re.escape(symbol) +
                      r'\s+"[^"\n]*"\s+\S+\s+(0x\w+)',definition)
    return int(match[1],16)

def words(data, offset, count, signed=False):
    return list(struct.unpack_from('<'+str(count)+('h' if signed else 'H'),data,offset))

def interp(x,y,t):
    assert x[0] <= t <= x[-1], (t,x[0],x[-1])
    j=min(max(bisect_right(x,t)-1,0),len(x)-2)
    return y[j]+(y[j+1]-y[j])*(t-x[j])/(x[j+1]-x[j])

fx,fy=words(draft,0x1D1976,30),words(draft,0x1D19B2,30)
ix,iy=words(draft,0x1D17D2,30),words(draft,0x1D180E,30)
ha=address('KLHDEV')
record=get_bytes(memory,ha,194)
assert int.from_bytes(record[:2],'little') == 48
hx,hy=words(record,2,48),words(record,98,48,True)
assert hx == words(draft,0x1D186C,48)
assert hy == words(draft,0x1D18CC,48,True)
mk_n55=words(draft,0x1D1A8C,1)[0]
mk_donor=int.from_bytes(get_bytes(memory,address('MK2TE'),2),'little')
rows=[]
for mass in (5,10,20,40,60):
    # The physical conversion supplied by the definitions is raw / 96000 ms/(mg/Hub).
    # Both pressure and fuel-density factors are fixed to unity in this experiment.
    n=mass*mk_n55/96000*1000
    d=mass*mk_donor/96000*1000
    normal=interp(fx,fy,n)
    donor_shape=d+interp(hx,hy,d)
    rows.append({'illustrative_mass_mg':mass,'n55_linear_ms':n/1000,
                 'n55_selected_curve_ms':normal/1000,'donor_linear_ms':d/1000,
                 'donor_additive_curve_ms':donor_shape/1000,
                 'n55_vs_donor_duration_percent':100*(normal/donor_shape-1)})
round_trip=[]
for t in (250,500,1000,2000,3000,5000):
    output=interp(fx,fy,t)
    recovered=interp(ix,iy,output)
    round_trip.append({'input_us':t,'forward_us':output,'inverse_recovered_us':recovered})
result={'draft_sha256':hashlib.sha256(draft).hexdigest(),
        'donor':donor,'donor_MK2TE_address':hex(address('MK2TE')),
        'donor_KLHDEV_address':hex(ha),'normal_MK2TE_raw':mk_n55,
        'donor_MK2TE_raw':mk_donor,
        'MK2TE_ratio_normal_over_donor':mk_n55/mk_donor,
        'reciprocal_ratio_donor_over_normal':mk_donor/mk_n55,
        'forward_inverse_axes_outputs_exact_swap':fx==iy and fy==ix,
        'assumptions':['Pressure factor fixed to 1 in both models',
                       'Fuel-density factor fixed to 1 in both models',
                       'Same illustrative fuel mass, not a logged injection mass',
                       'Donor stage evaluated as linear time + signed KLHDEV correction',
                       'No delay, FKKVS, coding, CVO, pause correction, clamps or scheduling',
                       'Floating-point linear interpolation, not bit-exact ECU arithmetic'],
        'comparison':rows,'round_trip':round_trip}
(OUT/'bulk_injector_model_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
assert session_path.read_bytes()==session_bytes
print(json.dumps(result,indent=2))
