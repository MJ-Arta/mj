"""User hypothesis (2026-11-03): the FX first-buy signal fails when the moving average slopes down.
Pre-declared variants (fixed before computing): add to the FX signal
  S50_20 : 50DMA today > 50DMA 20 trading days ago
  S50_10 : 50DMA today > 50DMA 10 trading days ago
  S200_20: 200DMA today > 200DMA 20 trading days ago
  S50&200: both S50_20 and S200_20
Same evaluation as research/prereg_logic_compare.md (zone baseline random draws, 7 cycle groups, halves)."""
import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
rng=np.random.default_rng(311)
k=kospi(); px=k['Close']['1995-05-01':]; idx=px.index
b=breadth().reindex(idx); pct=b['pct200']
fx1=usdkrw().reindex(idx,method='ffill').shift(1)
ma200=px.rolling(200).mean(); ma50=px.rolling(50).mean(); hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
Z=(dd.rolling(126,min_periods=1).min()<=-0.20)|(pct.rolling(126,min_periods=1).min()<0.20)
f252=px.shift(-252)/px-1; mx252=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
mn126=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
START=pd.Timestamp('1996-03-01')
base=(fx1<=0.95*fx1.rolling(126,min_periods=63).max())&(px>ma50)
V={'FX (기존)':base,'+50일선 상승(20일)':base&(ma50>ma50.shift(20)),'+50일선 상승(10일)':base&(ma50>ma50.shift(10)),
   '+200일선 상승(20일)':base&(ma200>ma200.shift(20)),'+50·200 둘 다 상승':base&(ma50>ma50.shift(20))&(ma200>ma200.shift(20))}
def events(sig,cool=126):
    s=(sig&Z).fillna(False); s=s[s.index>=START]; out=[];last=None
    for d in s[s].index:
        if last is None or idx.get_loc(d)-idx.get_loc(last)>cool: out.append(d); last=d
    return out
zpool=np.array([idx.get_loc(d) for d in idx[(Z.fillna(False))&(idx>=START)] if not np.isnan(f252[d])])
F=f252.values; MX=mx252.values; cache={}
def null(n):
    if n in cache: return cache[n]
    M=[];SR=[]
    for _ in range(3000):
        ch=[]
        for j in rng.permutation(zpool):
            if all(abs(j-c)>126 for c in ch): ch.append(j)
            if len(ch)==n: break
        M.append(F[ch].mean()); SR.append((MX[ch]>=0.3).mean())
    cache[n]=(np.array(M),np.array(SR)); return cache[n]
G=['1997-12-12','2000-12-22','2003-03-17','2004-08-02','2008-10-24','2020-03-19','2025-04-09']
# two-stage exit trades for event entries
P_=px.values; M_=ma200.values
def trades_for(ev):
    out=[]
    for d in ev:
        i=idx.get_loc(d); entry=P_[i]; armed=P_[i]>M_[i]; j=i+1; ex=None
        while j<len(idx):
            if not armed and P_[j]>M_[j]: armed=True
            if (not armed and P_[j]<0.90*entry) or (armed and P_[j]<0.97*M_[j]): ex=j; break
            j+=1
        out.append((d, P_[ex if ex else len(idx)-1]/entry-1, ex is None))
    return out
rows=[]; evlog={}
for nm,sig in V.items():
    ev=events(sig); evlog[nm]=ev
    v=[d for d in ev if not np.isnan(f252[d])]; n=len(v)
    m=np.mean([f252[d] for d in v]); sr=np.mean([mx252[d]>=0.3 for d in v]); M,SR=null(n)
    caught=[];lv=[]
    for g in G:
        t0=pd.Timestamp(g); i0=idx.get_loc(idx[idx.get_indexer([t0],method='nearest')[0]]); v0=px.iloc[i0]
        hit=[d for d in ev if i0<=idx.get_loc(d)<=i0+126]
        caught.append(bool(hit)); 
        if hit: lv.append(px[hit[0]]/v0-1)
    tr=trades_for(ev); closed=[t for t in tr if not t[2]]
    h1=[f252[d] for d in v if d<=pd.Timestamp('2010-12-31')]; h2=[f252[d] for d in v if d>pd.Timestamp('2010-12-31')]
    rows.append(dict(variant=nm,n=len(ev),mean252=m,succ30=sr,fake10=np.mean([mx252[d]<0.10 for d in ev]),worst126=np.mean([mn126[d] for d in ev]),
                     p_mean=(M>=m).mean(),p_succ=(SR>=sr).mean(),caught=f"{sum(caught)}/7",entry_vs_trough=np.mean(lv) if lv else np.nan,
                     trade_EV=np.mean([t[1] for t in closed]),trade_win=np.mean([t[1]>0 for t in closed]),avg_loss=np.mean([t[1] for t in closed if t[1]<=0]),
                     mean_h1=np.mean(h1) if h1 else np.nan,mean_h2=np.mean(h2) if h2 else np.nan,n_h1=len(h1),n_h2=len(h2),
                     live_2026_09=any(d>=pd.Timestamp('2026-08-01') for d in ev)))
R=pd.DataFrame(rows)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',300,'display.max_columns',30): print(R.to_string())
R.to_csv(S+'/work/fx_slope_compare.csv',index=False)
b0=set(evlog['FX (기존)'])
for nm in list(V)[1:]:
    rem=[d for d in evlog['FX (기존)'] if d not in set(evlog[nm])]; add=[d for d in evlog[nm] if d not in b0]
    print(f"\n{nm}: removed {len(rem)} -> ",[(d.date(), None if np.isnan(f252[d]) else round(f252[d],2), round(mx252[d],2)) for d in rem])
    print("   new/shifted entries:",[(d.date(), None if np.isnan(f252[d]) else round(f252[d],2), round(mx252[d],2)) for d in add])
# slope state on key dates
for d in ['1998-10-09','2003-05-13','2009-03-17','2020-06-08','2025-05-07','2026-09-07']:
    t=idx[idx.get_indexer([pd.Timestamp(d)],method='nearest')[0]]
    print(d,'MA50 20d chg %.2f%%'%((ma50[t]/ma50.shift(20)[t]-1)*100),' MA200 20d chg %.2f%%'%((ma200[t]/ma200.shift(20)[t]-1)*100))
