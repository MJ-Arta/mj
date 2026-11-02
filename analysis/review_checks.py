"""Checks prompted by the independent review (2026-11-02):
fair baselines, random-date test, mechanical cycle list, stop-loss rule, whipsaw variant,
Fed-condition base rate, memory lead-lag surrogate test, warning-score episodes."""
import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
rng=np.random.default_rng(7)
k=kospi(); px=k['Close']; b=breadth().reindex(px.index)
ma200=px.rolling(200).mean(); hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
deep=dd.rolling(126,min_periods=1).min()<=-0.20
f252=px.shift(-252)/px-1
mx252=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
mn126=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
def events(s,cool=126):
    out=[];last=None
    for d in s[s.fillna(False)].index:
        if last is None or (px.index.get_loc(d)-px.index.get_loc(last))>cool: out.append(d); last=d
    return out
sigB=deep&(px>ma200)&(px.shift(1)<=ma200.shift(1))
pre_C=b['pct200'].rolling(126,min_periods=1).min()<0.20
sigC=(b['pct200']>0.60)&pre_C
EV={'B':events(sigB),'C':events(sigC)}
def rand_test(ev,pool,ndraw=3000,gap=126):
    v=[d for d in ev if not np.isnan(f252[d])]; n=len(v)
    m_sig=np.mean([f252[d] for d in v]); h_sig=np.mean([f252[d]>0 for d in v])
    pool=[d for d in pool if not np.isnan(f252[d])]; pidx=np.array([px.index.get_loc(d) for d in pool])
    ms=[];hs=[]
    for _ in range(ndraw):
        perm=rng.permutation(len(pidx)); chosen=[]
        for j in perm:
            if all(abs(pidx[j]-c)>gap for c in chosen): chosen.append(pidx[j])
            if len(chosen)==n: break
        r=f252.iloc[chosen].values; ms.append(r.mean()); hs.append((r>0).mean())
    ms,hs=np.array(ms),np.array(hs)
    return n,m_sig,h_sig,(ms>=m_sig).mean(),(hs>=h_sig).mean()
out={}
print("== Fair baselines (forward 252d) ==")
allv=f252.dropna(); print("all days: n=%d hit=%.3f mean=%.3f median=%.3f"%(len(allv),(allv>0).mean(),allv.mean(),allv.median()))
for nm,pool in [('B',deep),('C',pre_C)]:
    p=f252[pool.fillna(False)].dropna()
    print(f"{nm} precondition days: n={len(p)} hit={(p>0).mean():.3f} mean={p.mean():.3f} median={p.median():.3f}")
    n,m,h,pm,ph=rand_test(EV[nm],list(p.index))
    print(f"   signal {nm}: n={n} hit={h:.3f} mean={m:.3f} | random spaced draws from precondition days: P(mean>=signal)={pm:.2f}  P(hit>=signal)={ph:.2f}")
    out[nm]=dict(pool_n=len(p),pool_hit=(p>0).mean(),pool_mean=p.mean(),pool_median=p.median(),sig_n=n,sig_hit=h,sig_mean=m,p_mean=pm,p_hit=ph)
v=[d for d in EV['B'] if not np.isnan(f252[d])]
print("B mean excl 1998 & 2025: %.3f"%np.mean([f252[d] for d in v if d.year not in (1998,2025)]))
print("\n== All signals, no hindsight labels: fwd252, max gain 252, worst drawdown within 126d ==")
rows=[]
for nm,ev in EV.items():
    for d in ev: rows.append(dict(sig=nm,date=d.date(),lvl=round(px[d],1),f252=f252[d],maxgain252=mx252[d],worst126=mn126[d]))
A=pd.DataFrame(rows); 
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',200): print(A.to_string())
A.to_csv(S+'/work/signals_all_outcomes.csv',index=False)
print("\n== Mechanical major up-cycles: 20%-zigzag trough with max close >= 1.5x within 252 trading days ==")
cyc=find_cycles(px,0.20); mech=[]
for t,d,vl in cyc:
    if t!='T': continue
    i=px.index.get_loc(d); w=px.iloc[i:i+253]; g=w.max()/vl-1
    if g>=0.5: mech.append((d.date(),round(vl,1),w.idxmax().date(),round(w.max(),1),round(g*100)))
for m in mech: print('  ',m)
print("\n== Stop-loss rule: buy at signal close, sell at first close < 0.97*MA200 (exploratory, 3% band not optimised) ==")
tr=[]
for nm,ev in EV.items():
    for d in ev:
        i=px.index.get_loc(d); exit_i=None
        for j in range(i+1,len(px)):
            if px.iloc[j]<0.97*ma200.iloc[j]: exit_i=j; break
        ex=exit_i if exit_i is not None else len(px)-1
        peak=px.iloc[i:ex+1].max()
        tr.append(dict(sig=nm,entry=d.date(),exit=px.index[ex].date(),open=exit_i is None,days=ex-i,ret=px.iloc[ex]/px.iloc[i]-1,peak_ret=peak/px.iloc[i]-1))
T=pd.DataFrame(tr)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',200): print(T.to_string())
for nm in ('B','C'):
    t=T[(T.sig==nm)&(~T.open)]; w=t[t.ret>0]; l=t[t.ret<=0]
    print(f"{nm}: closed trades {len(t)}, wins {len(w)} avg {w.ret.mean():.3f}, losses {len(l)} avg {l.ret.mean():.3f}, EV/trade {t.ret.mean():.3f}, median {t.ret.median():.3f}")
T.to_csv(S+'/work/stoploss_trades.csv',index=False)
print("\n== Whipsaw variant (post-hoc, NOT validation): B requires >=20 sessions below MA200 before crossing ==")
below=(px<ma200).astype(int); run=below.groupby((below!=below.shift()).cumsum()).cumsum()
sigB20=deep&(px>ma200)&(px.shift(1)<=ma200.shift(1))&(run.shift(1)>=20)
e=events(sigB20); print([ (d.date(), round(f252[d],3) if not np.isnan(f252[d]) else None) for d in e])
print("\n== Fed 'cut or hold' base rate (hiking phases from first to last hike, standard FOMC history) ==")
hikes=[('1997-03-25','1997-03-25'),('1999-06-30','2000-05-16'),('2004-06-30','2006-06-29'),('2015-12-16','2018-12-19'),('2022-03-16','2023-07-26'),('2026-09-16','2026-10-30')]
idx=px.index; hk=pd.Series(False,index=idx)
for a,z in hikes: hk[(idx>=a)&(idx<=z)]=True
print("share of trading days in hiking phase: %.3f -> 'cut or hold' base rate %.3f; P(7 of 7 by chance)=%.3f"%(hk.mean(),1-hk.mean(),(1-hk.mean())**7))
print("\n== Memory lead-lag: YoY vs monthly changes, circular-shift surrogate for max corr over lags 0-6 ==")
a=json.load(open(S+'/ext/md/data/asp_dram.json')); s=pd.Series({pd.Timestamp(x['date']):x['value'] for x in a['data']}).sort_index().resample('ME').last()
h=pd.read_parquet(S+'/work/close.parquet')['000660'].resample('ME').last().reindex(s.index)
for nm,(xs,ys) in {'YoY':(h.pct_change(12),s.pct_change(12)),'MoM':(h.pct_change(),s.pct_change())}.items():
    R=pd.DataFrame({'h':xs,'a':ys}).dropna()
    cs={L:round(R['h'].shift(L).corr(R['a']),2) for L in range(0,7)}
    obs=max(cs.values()); sur=[]
    for _ in range(2000):
        sh=rng.integers(12,len(R)-12); hh=np.roll(R['h'].values,sh)
        sur.append(max(pd.Series(hh).shift(L).corr(pd.Series(R['a'].values)) for L in range(0,7)))
    print(f"{nm}: n={len(R)} corr by lag {cs}  max={obs:.2f}  surrogate 95th pct of max={np.percentile(sur,95):.2f}  p={np.mean(np.array(sur)>=obs):.3f}")
print("\n== Warning score: independent episodes ==")
ws=pd.read_parquet(S+'/work/warn_score.parquet')['score'].reindex(px.index)
near=px>=0.97*px.rolling(252,min_periods=200).max()
fmin=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
D=pd.DataFrame({'s':ws,'dd':fmin})[near].dropna()
D['ep']=(D.index.to_series().diff().dt.days>90).cumsum()
for sc in range(0,5):
    x=D[D.s==sc]; eps=x.groupby('ep')['dd'].min()
    print(f"score {sc}: days {len(x)}, episodes {x.ep.nunique()}, episodes followed by -20% within 126d: {(eps<-0.2).sum()}")
json.dump({k:{kk:float(vv) for kk,vv in v.items()} for k,v in out.items()},open(S+'/work/review_baselines.json','w'),indent=1)
