"""Adversarial checks on the FX-recovery entry signal (post-hoc robustness; spec fixed in prereg)."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
rng=np.random.default_rng(99)
k=kospi(); px=k['Close']['1995-05-01':]; idx=px.index
b=breadth().reindex(idx); pct=b['pct200']
fx_raw=usdkrw()
ma200=px.rolling(200).mean(); ma50=px.rolling(50).mean(); hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
Z=(dd.rolling(126,min_periods=1).min()<=-0.20)|(pct.rolling(126,min_periods=1).min()<0.20)
f252=px.shift(-252)/px-1; mx252=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
mn126=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
START=pd.Timestamp('1996-03-01')
def events(sig,zone=True,cool=126):
    s=(sig&Z).fillna(False) if zone else sig.fillna(False); s=s[s.index>=START]; out=[];last=None
    for d in s[s].index:
        if last is None or idx.get_loc(d)-idx.get_loc(last)>cool: out.append(d); last=d
    return out
zpool=np.array([idx.get_loc(d) for d in idx[(Z.fillna(False))&(idx>=START)] if not np.isnan(f252[d])])
F=f252.values; MX=mx252.values
cache={}
def null(n):
    if n in cache: return cache[n]
    M=[];SR=[]
    for _ in range(2000):
        ch=[]
        for j in rng.permutation(zpool):
            if all(abs(j-c)>126 for c in ch): ch.append(j)
            if len(ch)==n: break
        M.append(F[ch].mean()); SR.append((MX[ch]>=0.3).mean())
    cache[n]=(np.array(M),np.array(SR)); return cache[n]
def summarize(ev,label):
    v=[d for d in ev if not np.isnan(f252[d])]
    if len(v)<3: print(label,'n<3'); return None
    m=np.mean([f252[d] for d in v]); sr=np.mean([mx252[d]>=0.3 for d in v]); M,SR=null(len(v))
    r=dict(label=label,n=len(ev),n252=len(v),mean252=round(m,3),succ30=round(sr,3),fake10=round(np.mean([mx252[d]<0.1 for d in ev]),3),
           worst126=round(np.mean([mn126[d] for d in ev]),3),p_mean=round((M>=m).mean(),3),p_succ=round((SR>=sr).mean(),3))
    return r
rows=[]
for lag in (0,1,2):
    fx=fx_raw.shift(lag).reindex(idx,method='ffill') if lag==0 else fx_raw.reindex(idx,method='ffill').shift(lag)
    for thr in (0.03,0.05,0.07,0.10):
        for win in (63,126,252):
            for useMA in (True,False):
                sig=(fx<=(1-thr)*fx.rolling(win,min_periods=win//2).max())
                if useMA: sig=sig&(px>ma50)
                r=summarize(events(sig),f"lag{lag} thr{thr} win{win} ma50={useMA}")
                if r: rows.append(r)
R=pd.DataFrame(rows)
print("FX parameter grid (zone-restricted):")
print(R.to_string())
R.to_csv(S+'/work/fx_grid.csv',index=False)
print("\nShare of grid with p_mean<0.05: %.2f ; p_succ<0.10: %.2f ; median mean252 %.3f"%((R.p_mean<0.05).mean(),(R.p_succ<0.10).mean(),R.mean252.median()))
# main spec with 1-day lag
fx1=fx_raw.reindex(idx,method='ffill').shift(1)
sigFX=(fx1<=0.95*fx1.rolling(126,min_periods=63).max())&(px>ma50)
ev=events(sigFX)
print("\nMain spec (lag1) events:")
for d in ev: print(' ',d.date(),round(px[d]),' fx %.0f (126d max %.0f)'%(fx1[d],fx1.rolling(126,min_periods=63).max()[d]),' f252',None if np.isnan(f252[d]) else round(f252[d],3),' max252',round(mx252[d],3),' worst126',round(mn126[d],3))
# price-only analog: KOSPI rebounded >=10% from 126d low and above MA50
lo=px.rolling(126,min_periods=63).min()
sigP=(px>=1.10*lo)&(px>ma50)
print("\nIdentifiability: price-only analogs vs FX")
for lab,s in [('FX (lag1)',sigFX),('PRICE rebound10%+MA50',sigP),('PRICE rebound15%+MA50',(px>=1.15*lo)&(px>ma50)),
              ('PRICE&FX',sigP&(fx1<=0.95*fx1.rolling(126,min_periods=63).max())),('PRICE&notFX',sigP&~(fx1<=0.95*fx1.rolling(126,min_periods=63).max())),
              ('FX without MA50',(fx1<=0.95*fx1.rolling(126,min_periods=63).max())),('FX no zone',sigFX)]:
    r=summarize(events(s,zone=(lab!='FX no zone')),lab); 
    if r: print('  ',r)
# day-level conditional test inside zone: forward 252 by FX state, controlling for price rebound state
D=pd.DataFrame({'f':f252,'mx':mx252,'fx':(fx1<=0.95*fx1.rolling(126,min_periods=63).max()),'pr':(px>=1.10*lo)&(px>ma50),'z':Z})
D=D[(D.z==True)&(D.index>=START)].dropna()
print("\nDay-level (zone days) mean fwd252 / success30 by [price rebound, FX recovered]:")
print(D.groupby(['pr','fx']).agg(n=('f','size'),mean=('f','mean'),succ=('mx',lambda x:(x>=0.3).mean())).round(3).to_string())
# leave-one-cycle-group-out
groups=[('1997-12-12','1999-12-31'),('2000-12-22','2002-06-30'),('2003-03-17','2005-12-31'),('2008-10-24','2010-06-30'),('2020-03-19','2021-06-30'),('2025-04-09','2026-10-30')]
print("\nLeave-one-group-out (main spec):")
for a,z in groups:
    e2=[d for d in ev if not (pd.Timestamp(a)<=d<=pd.Timestamp(z))]
    r=summarize(e2,f"drop {a[:7]}"); print('  ',r)
