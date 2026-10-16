"""Read-only October 16 log review. Outputs analysis/plots, never calibration edits."""
from pathlib import Path
import hashlib,json,struct,os,sys
sys.path.insert(0,str(Path(os.environ['TEMP'])/'codex-n55-analysis-tools'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'October16_v5_review'
OUT.mkdir(exist_ok=True)
COL={'rpm':'RPM (rpm)','pedal':'Accel Ped. Pos. (%)','load':'Load actual RAM',
 'afr':'Lambda bank 1 (AFR)','target':'Lambda target (AFR)','stft':'STFT 1 (%)',
 'ltft':'LTFT 1 (%)','rail':'Rail pressure mean (PSI)','rail_req':'Rail pressure req. (PSI)',
 'coolant':'Coolant (*F)','iat':'IAT (*F)','hdi':'HDP I-Factor (-)','gear':'Gear (-)',
 'boost':'Boost (PSI)','mode':'Fuel Mode (-)','c6':'Cyl6 Timing Cor (*)'}
v4=(ROOT/'FlexFuel/Revisions/FlexFuelv4(FuelScalar-93).bin').read_bytes()
v5=(ROOT/'FlexFuel/Revisions/FlexFuelv5(InjectorFix-FuelMassFloor).bin').read_bytes()
diff=[i for i,(a,b) in enumerate(zip(v4,v5)) if a!=b]
checks={'v5_sha256':hashlib.sha256(v5).hexdigest(),'different_bytes':len(diff),
 'changed_outside_pressure_outputs':[hex(i) for i in diff if not 0x1D19EE<=i<0x1D1A16],
 'FRKMIN_before':v4[0x1B84C0]/128,'FRKMIN_after':v5[0x1B84C0]/128,
 'pressure_axis_unchanged':v4[0x1D1A92:0x1D1ABE]==v5[0x1D1A92:0x1D1ABE]}
sx=np.array(struct.unpack_from('<16h',v5,0x1942D2))/100
sy=np.array(struct.unpack_from('<16h',v5,0x1942B2))
sz=np.array(struct.unpack_from('<256H',v5,0x1942F2)).reshape(16,16)/32768
# Axis ordering/scales are checked against the embedded XDF before interpreting results.
def summary(d):
 if d.empty:return {'n':0}
 out={'n':len(d),'start':float(d.Time.min()),'end':float(d.Time.max()),
      'sample_duration_s':float(d['_dt'].sum())}
 for k,c in COL.items():out[k]={'min':float(d[c].min()),'median':float(d[c].median()),'max':float(d[c].max())}
 for c in ['afr_ratio','rail_error_psi','combined_trim_multiplier','scalar_lookup']:
  out[c]={'min':float(d[c].min()),'median':float(d[c].median()),'max':float(d[c].max())}
 out['AFR_below_90pct_target_samples']=int((d.afr_ratio<.9).sum())
 out['STFT_at_minus30_samples']=int((d[COL['stft']]<=-29.9).sum())
 out['modes']={str(k):int(v) for k,v in d[COL['mode']].value_counts().items()}
 return out

def runs(d,mask):
 starts=mask&~mask.shift(fill_value=False);ends=mask&~mask.shift(-1,fill_value=False)
 return [{'start':float(d.Time.iloc[a]),'end':float(d.Time.iloc[z]),
          'duration':float(d.Time.iloc[z]-d.Time.iloc[a]),'n':int(z-a+1)}
         for a,z in zip(np.flatnonzero(starts),np.flatnonzero(ends))]

results={'calibration':checks,'files':[]}
for p in sorted((ROOT/'DataLogging').glob('2026-10-16*v5*.csv')):
 raw=p.read_bytes();d=pd.read_csv(p,skiprows=4)
 for c in d:d[c]=pd.to_numeric(d[c],errors='coerce')
 d['_dt']=d.Time.shift(-1)-d.Time;d.loc[d.index[-1],'_dt']=d.Time.diff().median()
 d.loc[d['_dt']>.5,'_dt']=0  # Do not count unobserved logging gaps as measured coverage.
 d['afr_ratio']=d[COL['afr']]/d[COL['target']]
 d['rail_error_psi']=d[COL['rail']]-d[COL['rail_req']]
 d['combined_trim_multiplier']=(1+d[COL['stft']]/100)*(1+d[COL['ltft']]/100)
 d['scalar_lookup']=[float(np.interp(r,sy,[np.interp(l,sx,row) for row in sz]))
                     for r,l in zip(d[COL['rpm']],d[COL['load']])]
 idle=(d[COL['rpm']].between(600,900)&(d[COL['pedal']]<1)&d[COL['target']].between(14,15.5))
 # Near-idle operating mask: vehicle speed and torque-converter state are absent.
 cruise=(d[COL['rpm']].between(1300,3000)&d[COL['pedal']].between(3,40)&
         d[COL['load']].between(20,90)&d[COL['target']].between(14,15.5))
 f={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'rows':len(d),
    'start':float(d.Time.min()),'end':float(d.Time.max()),
    'median_dt':float(d.Time.diff().median()),'max_dt':float(d.Time.diff().max()),
    'configuration':{c:{str(k):int(v) for k,v in d[c].value_counts().items()} for c in
     ['Current Map (-)','Ethanol Content (Active) (%)','Ethanol Content (CAN) (%)',
      'Fuel Interpolation (-)','Fuel Scalar Interpolation (-)']},
    'torque_states':{c:{str(k):int(v) for k,v in d[c].value_counts().items()}
      for c in ['Torque lim. 1 (-)','Torque lim. 2 (-)','Torque lim. 3 (-)']},
    'idle_like_all':summary(d[idle]),'cruise_like':summary(d[cruise])}
 windows=[(10,35),(35,90),(400,500),(700,813)] if '14_26' in p.name else [(0,100),(100,250),(300,376)]
 f['idle_windows']={f'{a}-{z}':summary(d[idle&d.Time.between(a,z)]) for a,z in windows}
 f['matched_idle']={f'{a}-{z}':summary(d[idle&d.Time.between(a,z)&
  d[COL['rpm']].between(680,740)&d[COL['load']].between(27,31)]) for a,z in windows}
 low=d[COL['rpm']].between(1000,2500)&(d[COL['boost']]<5)&(d[COL['pedal']]>3)
 f['low_load_c6_below_minus6']=summary(d[low&(d[COL['c6']]<=-6)])
 f['cylinder_correction_minima']={f'cyl{i}':float(d[f'Cyl{i} Timing Cor (*)'].min()) for i in range(1,7)}
 f['c6_correction_runs_below_minus6']=runs(d,d[COL['c6']]<=-6)
 if '14_50' in p.name:
  shift_times=d.loc[(d[COL['gear']].diff()!=0)&d.Time.between(288,294),'Time'].tolist()
  f['pull_shift_times']=shift_times
  core=d.Time.between(289,293)&(d[COL['pedal']]>50)&(d[COL['load']]>100)&d[COL['target']].between(12,14.3)
  f['pull_enriched_core']=summary(d[core]);f['pull_core_rich_runs']=runs(d,core&(d.afr_ratio<.9))
  for margin in [.2,.35,.5]:
   keep=core.copy()
   for t in shift_times:keep&=abs(d.Time-t)>margin
   f[f'pull_excluding_shifts_{margin}s']=summary(d[keep])
  f['pull_by_gear']={str(g):summary(a) for g,a in d[core].groupby(COL['gear'])}
  for c in [f'Cyl{i} Timing Cor (*)' for i in range(1,7)]:
   f.setdefault('pull_cylinder_corrections',{})[c]={'min':float(d.loc[core,c].min()),'median':float(d.loc[core,c].median())}
  selected=['Time']+list(COL.values())+['afr_ratio','rail_error_psi','scalar_lookup',
   'Torque lim. 1 (-)','Torque lim. 2 (-)','Torque lim. 3 (-)']
  f['pull_samples']=d.loc[d.Time.between(289,293),selected].to_dict(orient='records')
  a=d[d.Time.between(288.8,293.1)]
  fig,ax=plt.subplots(4,1,figsize=(11,9),sharex=True,constrained_layout=True)
  ax[0].plot(a.Time,a[COL['afr']],label='Actual');ax[0].plot(a.Time,a[COL['target']],label='Target');ax[0].set_ylabel('AFR');ax[0].legend(loc='upper right')
  ax[1].plot(a.Time,a[COL['rail']],label='Actual');ax[1].plot(a.Time,a[COL['rail_req']],label='Target');ax[1].set_ylabel('Rail pressure (psi)');ax[1].legend(loc='lower right')
  ax[2].plot(a.Time,a[COL['rpm']],label='RPM');ax[2].set_ylabel('RPM')
  ax[3].plot(a.Time,a[COL['stft']],label='STFT (%)');ax[3].plot(a.Time,a[COL['c6']],label='Cylinder 6 timing correction (deg)');ax[3].legend(loc='lower right');ax[3].set_xlabel('Log time (s)')
  for x in ax:
   x.grid(alpha=.2)
   for t in shift_times:x.axvline(t,color='grey',linestyle=':',alpha=.6)
  fig.suptitle('October 16 v5 pull: dotted lines mark logged gear changes')
  fig.savefig(OUT/'pull.png',dpi=150);plt.close(fig)
 else:
  d=d.copy()
  d.loc[d.Time.diff()>.5,[COL['stft'],COL['ltft'],'afr_ratio',COL['coolant'],COL['rail']]]=np.nan
  fig,ax=plt.subplots(3,1,figsize=(11,8),sharex=True,constrained_layout=True)
  ax[0].plot(d.Time,d[COL['stft']],alpha=.5,label='STFT');ax[0].plot(d.Time,d[COL['ltft']],alpha=.7,label='LTFT');ax[0].scatter(d.loc[idle,'Time'],d.loc[idle,COL['stft']],s=3,label='Near-idle STFT');ax[0].set_ylabel('Trim (%)');ax[0].legend(loc='lower right')
  ax[1].plot(d.Time,d.afr_ratio);ax[1].set_ylim(.6,1.5);ax[1].axhline(1,color='black',linestyle=':');ax[1].set_ylabel('Actual / target AFR')
  ax[2].plot(d.Time,d[COL['coolant']],label='Coolant (F)');ax[2].plot(d.Time,d[COL['rail']]/10,label='Rail pressure / 10 (psi)');ax[2].set_xlabel('Log time (s)');ax[2].legend()
  for x in ax:x.grid(alpha=.2)
  fig.suptitle('October 16 v5 cold-start and driving log')
  fig.savefig(OUT/'first_log.png',dpi=150);plt.close(fig)
 results['files'].append(f)
 assert p.read_bytes()==raw
(OUT/'analysis.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
for f in results['files']:
 print('\nFILE',Path(f['path']).name)
 for k in ['idle_windows','matched_idle','pull_shift_times','pull_enriched_core','pull_excluding_shifts_0.35s','pull_by_gear','pull_cylinder_corrections','low_load_c6_below_minus6','cylinder_correction_minima']:
  if k in f:print(k,json.dumps(f[k]))
