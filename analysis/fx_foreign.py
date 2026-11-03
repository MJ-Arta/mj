"""Exploratory: does foreign-investor net buying separate good and bad FX first-buy signals?
Data available: Samsung+SK hynix daily foreign net buying value 2019-01..2024-12 (timesavingbee/google, pykrx-style
files) and all-KOSPI 20-day foreign net value snapshots 2026-08..2026-11 (james-brand/korea-market-data, CC BY 4.0).
Pre-declared flow conditions (fixed before computing): F20>0 = big-2 foreign net buying over the last 20 trading days > 0;
F5>0 = same over 5 days."""
import sys,os,glob,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
TSB=sys.argv[1]; KMD=sys.argv[2]
k=kospi(); px=k['Close']['1995-05-01':]; idx=px.index
b=breadth().reindex(idx); pct=b['pct200']
fx1=usdkrw().reindex(idx,method='ffill').shift(1)
ma200=px.rolling(200).mean(); ma50=px.rolling(50).mean(); hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
Z=(dd.rolling(126,min_periods=1).min()<=-0.20)|(pct.rolling(126,min_periods=1).min()<0.20)
fxcond=(fx1<=0.95*fx1.rolling(126,min_periods=63).max())&(px>ma50)
f252=px.shift(-252)/px-1; mx252=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
mn126=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
# big-2 foreign net value
flows=[]
for c in ('A005930','A000660'):
    d=pd.read_csv(f'{TSB}/{c}.csv'); d['날짜']=pd.to_datetime(d['날짜'])
    flows.append(d.set_index('날짜')['외국인합계_거래대금_순매수'].astype(float))
fb=(flows[0].add(flows[1],fill_value=0)).reindex(idx)
F20=fb.rolling(20,min_periods=20).sum(); F5=fb.rolling(5,min_periods=5).sum()
print('big-2 flow coverage:',fb.dropna().index.min().date(),'->',fb.dropna().index.max().date())
# 2026 snapshots
snap=[]
for p in sorted(glob.glob(f'{KMD}/archive/*/foreign-flows-aggregates.csv'))+[f'{KMD}/data/foreign-flows-aggregates.csv']:
    head=open(p,encoding='utf-8').readline(); asof=head.split('as of')[1].split('·')[0].strip()
    t=pd.read_csv(p,comment='#',dtype={'ticker':str}); kp=t[t.market=='KOSPI']
    big=kp[kp.ticker.isin(['005930','000660'])]
    snap.append(dict(asof=asof,kospi_f20_tn=kp.f_20d_val.sum()/1e12,kospi_f5_tn=kp.f_5d_val.sum()/1e12,big2_f20_tn=big.f_20d_val.sum()/1e12))
SN=pd.DataFrame(snap).drop_duplicates('asof').sort_values('asof'); SN['asof']=pd.to_datetime(SN['asof'])
print('\n2026 snapshots (trillion KRW, 20-day net foreign):'); print(SN.iloc[::5].round(2).to_string(index=False))
# events 2019-2026
def events(sig,cool=126,start='2019-02-01'):
    s=(sig&Z).fillna(False); s=s[s.index>=start]; out=[];last=None
    for d in s[s].index:
        if last is None or idx.get_loc(d)-idx.get_loc(last)>cool: out.append(d); last=d
    return out
print('\nFX first-buy signals since 2019 and foreign flows at the signal (big-2, trillion KRW):')
for d in events(fxcond):
    f20=F20.get(d,np.nan); f5=F5.get(d,np.nan)
    s=SN[SN['asof']<=d].tail(1)
    extra=f" | 2026 snapshot {s['asof'].iloc[0].date()}: KOSPI 20d {s.kospi_f20_tn.iloc[0]:+.1f}tn, big-2 20d {s.big2_f20_tn.iloc[0]:+.1f}tn" if len(s) and d.year==2026 else ''
    print(f"  {d.date()} KOSPI {px[d]:.0f}  big2 F20 {f20/1e12:+.2f}tn F5 {f5/1e12:+.2f}tn  -> 1y {('%+.0f%%'%(f252[d]*100)) if not np.isnan(f252[d]) else 'n/a'}  max1y {mx252[d]*100:+.0f}%  worst6m {mn126[d]*100:+.0f}%{extra}")
# FX & F20>0 variant events (2019-2024 coverage)
print('\nVariant FX & F20>0 (big-2) events:')
for d in events(fxcond&(F20>0)): print(f"  {d.date()} KOSPI {px[d]:.0f} 1y {('%+.0f%%'%(f252[d]*100)) if not np.isnan(f252[d]) else 'n/a'} max1y {mx252[d]*100:+.0f}% worst6m {mn126[d]*100:+.0f}%")
# day-level, zone days with flow data
D=pd.DataFrame({'f':f252,'mx':mx252,'mn':mn126,'fx':fxcond,'pos20':F20>0,'pos5':F5>0,'z':Z,'has':F20.notna()})
D=D[(D.z==True)&(D.has==True)].dropna(subset=['f'])
print('\nZone days 2019-2024 with flow data: n=%d'%len(D))
print(D.groupby(['fx','pos20']).agg(n=('f','size'),mean1y=('f','mean'),succ30=('mx',lambda x:(x>=0.3).mean()),worst6m=('mn','mean')).round(3).to_string())
print(D.groupby(['fx','pos5']).agg(n=('f','size'),mean1y=('f','mean'),succ30=('mx',lambda x:(x>=0.3).mean()),worst6m=('mn','mean')).round(3).to_string())
# FX days only: correlation of F20 (scaled by big-2 mcap proxy: use raw) with forward return
mcap=pd.read_parquet(S+'/work/mcap.parquet')[['005930','000660']].sum(axis=1).reindex(idx)
D2=pd.DataFrame({'f':f252,'flow_pct':F20/mcap*100,'fx':fxcond,'z':Z}).dropna()
D2=D2[(D2.fx)&(D2.z)]
print('\nFX-condition days with flow data: n=%d, Spearman(F20 as %% of big-2 mcap, 1y return)=%.2f'%(len(D2),D2[['flow_pct','f']].corr(method='spearman').iloc[0,1]))
SN.to_csv(S+'/work/foreign_snapshots_2026.csv',index=False)
