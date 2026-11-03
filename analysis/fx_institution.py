"""Exploratory: institutional net buying as a filter for the FX first-buy signal (same design as fx_foreign.py).
Pre-declared: I20>0 = big-2 institutional net buying value over last 20 trading days > 0; I5>0 over 5 days.
Retail (개인) shown alongside as a reference only."""
import sys,os,glob; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
TSB=sys.argv[1]; KMD=sys.argv[2]
k=kospi(); px=k['Close']['1995-05-01':]; idx=px.index
b=breadth().reindex(idx); pct=b['pct200']
fx1=usdkrw().reindex(idx,method='ffill').shift(1)
ma50=px.rolling(50).mean(); hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
Z=(dd.rolling(126,min_periods=1).min()<=-0.20)|(pct.rolling(126,min_periods=1).min()<0.20)
fxcond=(fx1<=0.95*fx1.rolling(126,min_periods=63).max())&(px>ma50)
f252=px.shift(-252)/px-1; mx252=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
mn126=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
def load(col):
    s=[]
    for c in ('A005930','A000660'):
        d=pd.read_csv(f'{TSB}/{c}.csv'); d['날짜']=pd.to_datetime(d['날짜']); s.append(d.set_index('날짜')[col].astype(float))
    return s[0].add(s[1],fill_value=0).reindex(idx)
inst=load('기관합계_거래대금_순매수'); retail=load('개인_거래대금_순매수')
I20=inst.rolling(20,min_periods=20).sum(); I5=inst.rolling(5,min_periods=5).sum(); R20=retail.rolling(20,min_periods=20).sum()
# 2026 snapshots: institutional 20d shares x last close (approximate value)
snap=[]
for p in sorted(glob.glob(f'{KMD}/archive/*/foreign-flows-aggregates.csv'))+[f'{KMD}/data/foreign-flows-aggregates.csv']:
    head=open(p,encoding='utf-8').readline(); asof=head.split('as of')[1].split('·')[0].strip()
    t=pd.read_csv(p,comment='#',dtype={'ticker':str}); kp=t[t.market=='KOSPI']
    v=(kp.i_20d_sh*kp.last_close); big=kp.ticker.isin(['005930','000660'])
    snap.append(dict(asof=asof,kospi_i20_tn=v.sum()/1e12,big2_i20_tn=v[big].sum()/1e12,kospi_f20_tn=kp.f_20d_val.sum()/1e12))
SN=pd.DataFrame(snap).drop_duplicates('asof').sort_values('asof'); SN['asof']=pd.to_datetime(SN['asof'])
print('2026 snapshots (trillion KRW, 20-day net; institution value approximated as shares x close):')
print(SN.iloc[::5].round(2).to_string(index=False))
def events(sig,cool=126,start='2019-02-01'):
    s=(sig&Z).fillna(False); s=s[s.index>=start]; out=[];last=None
    for d in s[s].index:
        if last is None or idx.get_loc(d)-idx.get_loc(last)>cool: out.append(d); last=d
    return out
print('\nFX first-buy signals and institutional / retail flows at the signal (big-2, trillion KRW):')
for d in events(fxcond):
    s=SN[SN['asof']<=d].tail(1)
    extra=f" | 2026 snapshot: KOSPI inst 20d {s['kospi_i20_tn'].iloc[0]:+.1f}tn, big-2 inst {s['big2_i20_tn'].iloc[0]:+.1f}tn" if len(s) and d.year==2026 else ''
    i20=I20.get(d,np.nan); r20=R20.get(d,np.nan)
    print(f"  {d.date()} KOSPI {px[d]:.0f} inst I20 {i20/1e12:+.2f}tn I5 {I5.get(d,np.nan)/1e12:+.2f}tn retail R20 {r20/1e12:+.2f}tn -> 1y {('%+.0f%%'%(f252[d]*100)) if not np.isnan(f252[d]) else 'n/a'} max1y {mx252[d]*100:+.0f}% worst6m {mn126[d]*100:+.0f}%{extra}")
print('\nVariant FX & I20>0 events:')
for d in events(fxcond&(I20>0)): print(f"  {d.date()} KOSPI {px[d]:.0f} 1y {('%+.0f%%'%(f252[d]*100)) if not np.isnan(f252[d]) else 'n/a'} max1y {mx252[d]*100:+.0f}% worst6m {mn126[d]*100:+.0f}%")
D=pd.DataFrame({'f':f252,'mx':mx252,'mn':mn126,'fx':fxcond,'i20':I20>0,'i5':I5>0,'r20':R20>0,'z':Z,'has':I20.notna()})
D=D[(D.z==True)&(D.has==True)].dropna(subset=['f'])
agg=dict(n=('f','size'),mean1y=('f','mean'),succ30=('mx',lambda x:(x>=0.3).mean()),worst6m=('mn','mean'))
print('\nZone days 2019-2024 (n=%d) by FX condition x institution 20d buying:'%len(D)); print(D.groupby(['fx','i20']).agg(**agg).round(3).to_string())
print('\n... x institution 5d buying:'); print(D.groupby(['fx','i5']).agg(**agg).round(3).to_string())
print('\n(reference) ... x retail 20d buying:'); print(D.groupby(['fx','r20']).agg(**agg).round(3).to_string())
mcap=pd.read_parquet(S+'/work/mcap.parquet')[['005930','000660']].sum(axis=1).reindex(idx)
D2=pd.DataFrame({'f':f252,'ip':I20/mcap*100,'fx':fxcond,'z':Z}).dropna(); D2=D2[D2.fx&D2.z]
print('\nFX-condition days: n=%d, Spearman(inst 20d as %% of big-2 mcap, 1y return)=%.2f'%(len(D2),D2[['ip','f']].corr(method='spearman').iloc[0,1]))
SN.to_csv(S+'/work/institution_snapshots_2026.csv',index=False)
