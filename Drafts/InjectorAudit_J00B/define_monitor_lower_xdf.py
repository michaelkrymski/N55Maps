"""Add the verified FRKMIN_UM definition without modifying calibration bytes."""
from pathlib import Path
import base64,copy,hashlib,json,os,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'XDF_definition_backup'
xdf_path=ROOT/'Tools/000021571DAA01.xdf'
draft_path=ROOT/'Drafts/FlexFuelDrafts.json'
xdf_before=xdf_path.read_bytes()
draft_before=draft_path.read_bytes()
payload=json.loads(draft_before)
assert base64.b64decode(payload['source_xdf_b64'])==xdf_before
root=ET.fromstring(xdf_before)
assert not any('FRKMIN_UM' in (n.findtext('title') or '') for n in root)
template=next(n for n in root if n.findtext('title')=='Max fuel scalar')
node=copy.deepcopy(template)
uid=max(int(n.get('uniqueid'),0) for n in root if n.get('uniqueid'))+1
node.set('uniqueid',hex(uid))
node.find('title').text='Fuel mass monitor lower multiplier (FRKMIN_UM)'
node.find('description').text=(
 'FRKMIN_UM: lower multiplier for the fuel-mass safety monitor. '
 'Verified in the supplied J00B code at file offset 0x1B84C0. '
 'Unsigned 8-bit storage, physical value = raw / 128. '
 'The positive-reference lower-bound stage is approximately '
 'trunc(reference_raw * raw / 128) - RKO_UM_raw * 16, with saturation and other checks. '
 'This is not a direct minimum for Fuel Scalar table cells. '
 'Lowering it widens the permitted lower deviation in the monitored fuel quantity; '
 'it does not repair injector characterization or directly command fueling. '
 'Current audited raw value 113 = 0.8828125. '
 'No threshold change has been validated by this definition. '
 'Resolution is 0.0078125; exactly 0.85 is not representable.')
z=node.find("XDFAXIS[@id='z']")
z.find('EMBEDDEDDATA').set('mmedaddress','0x1B84C0')
z.find('decimalpl').text='7'
z.find('min').text='0.0000000'
z.find('max').text='1.9921875'
z.find('MATH').set('equation','X/128')
ET.indent(node,space='  ',level=1)
addition=ET.tostring(node,encoding='unicode').replace('\n','\r\n').encode('utf-8')
xdf_after=xdf_before.replace(b'</XDFFORMAT>',b'  '+addition+b'\r\n</XDFFORMAT>')
newroot=ET.fromstring(xdf_after)
assert len(newroot)==len(root)+1
def without_tail(element):
 clone=copy.deepcopy(element)
 clone.tail=None
 return ET.tostring(clone)
assert all(without_tail(a)==without_tail(b) for a,b in zip(root,list(newroot)[:-1]))
payload['source_xdf_b64']=base64.b64encode(xdf_after).decode()
draft_after=json.dumps(payload,indent=2).encode('utf-8')
assert all(json.loads(draft_before)[k]==payload[k] for k in payload if k!='source_xdf_b64')
OUT.mkdir(exist_ok=True)
for name,data in [('000021571DAA01.before-FRKMIN.xdf',xdf_before),('FlexFuelDrafts.before-FRKMIN.json',draft_before)]:
 target=OUT/name
 if target.exists(): assert target.read_bytes()==data
 else: target.write_bytes(data)
assert xdf_path.read_bytes()==xdf_before and draft_path.read_bytes()==draft_before
for p,data in [(xdf_path,xdf_after),(draft_path,draft_after)]:
 tmp=p.with_name(p.name+'.frkmin-tmp')
 tmp.write_bytes(data)
 os.replace(tmp,p)
result={'definition_uniqueid':hex(uid),'definition_title':node.findtext('title'),
 'address':'0x1B84C0','equation':'X/128',
 'working_bin_unchanged':True,
 'working_bin_sha256':hashlib.sha256(base64.b64decode(payload['working_bin_b64'])).hexdigest(),
 'raw':base64.b64decode(payload['working_bin_b64'])[0x1B84C0],
 'only_draft_field_changed':'source_xdf_b64','backup_directory':str(OUT)}
(OUT.parent/'lower_monitor_definition_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
