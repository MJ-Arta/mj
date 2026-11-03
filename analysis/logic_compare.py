"""Pre-registered comparison of detection logics (research/prereg_logic_compare.md)."""
import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
rng=np.random.default_rng(2026)
k=kospi(); px=k['Close']['1995-05-01':]; idx=px.index
b=breadth().reindex(idx)
fx=usdkrw().reindex(idx,method='ffill')
adj=pd.read_parquet(S+'/work/close.parquet').reindex(idx)
semi=(adj[['005930','000660']].pct_change(fill_method=None).mean(axis=1,skipna=True)).fillna(0).add(1).cumprod()
ma200=px.rolling(200).mean(); ma50=px.rolling(50).mean()
hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
pct=b['pct200']
Z=(dd.rolling(126,min_periods=1).min()<=-0.20)|(pct.rolling(126,min_periods=1).min()<0.20)
hikes=[('1997-03-25','1997-03-25'),('1999-06-30','2000-05-16'),('2004-06-30','2006-06-29'),('2015-12-16','2018-12-19'),('2022-03-16','2023-07-26'),('2026-09-16','2026-12-31')]
fed=pd.Series(False,index=idx)
for a,z in hikes: fed[(idx>=a)&(idx<=z)]=True
f252=px.shift(-252)/px-1
mx252=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
mn126=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
START=pd.Timestamp('1996-03-01')
# ---------- entry candidates ----------
below=(px<ma200).astype(int); run=below.groupby((below!=below.shift()).cumsum()).cumsum()
cross_up=(px>ma200)&(px.shift(1)<=ma200.shift(1))
ema=b['adv'].ewm(span=10,adjust=False).mean()
cand={
 'B': cross_up,
 'B20': cross_up&(run.shift(1)>=20),
 'C': pct>0.60,
 'A': (ema>0.615)&(ema.rolling(10).min()<0.40),
 'GC': (ma50>ma200)&(ma50.shift(1)<=ma200.shift(1)),
 'NH': (b['nh52']>=0.05)&(dd<=-0.15),
 'FX': (fx<=0.95*fx.rolling(126,min_periods=60).max())&(px>ma50),
 'SEMI': ((semi/semi.shift(126))>(px/px.shift(126)))&((semi.shift(1)/semi.shift(127))<=(px.shift(1)/px.shift(127))),
}
cand['B+FED']=cand['B']&~fed; cand['C+FED']=cand['C']&~fed
def events(sig,cool=126):
    s=(sig&Z).fillna(False); s=s[s.index>=START]
    out=[];last=None
    for d in s[s].index:
        if last is None or idx.get_loc(d)-idx.get_loc(last)>cool: out.append(d); last=d
    return out
zpool=[d for d in idx[(Z.fillna(False))&(idx>=START)] if not np.isnan(f252[d])]
zi=np.array([idx.get_loc(d) for d in zpool])
F=f252.values; MX=mx252.values
def rand_null(n,ndraw=3000):
    M=[];SR=[]
    for _ in range(ndraw):
        ch=[]
        for j in rng.permutation(zi):
            if all(abs(j-c)>126 for c in ch): ch.append(j)
            if len(ch)==n: break
        M.append(F[ch].mean()); SR.append((MX[ch]>=0.30).mean())
    return np.array(M),np.array(SR)
# mechanical major-cycle troughs (grouped)
cyc=find_cycles(px,0.20); mech=[]
for t,d,v in cyc:
    if t!='T' or d<START-pd.Timedelta(days=200): continue
    i=idx.get_loc(d); w=px.iloc[i:i+253]
    if w.max()/v-1>=0.5: mech.append((d,v,w.idxmax(),w.max()))
groups=[];
for m in mech:
    if groups and (m[0]-groups[-1][-1][0]).days<400: groups[-1].append(m)
    else: groups.append([m])
G=[(g[0][0],g[0][1],max(x[3] for x in g)) for g in groups]   # first trough of group, its level, best peak
print("Mechanical cycle groups:",[(g[0].date(),round(g[1]),round(g[2])) for g in G])
nullcache={}
rows=[];evlog={}
for nm,sig in cand.items():
    ev=events(sig); evlog[nm]=[d.date().isoformat() for d in ev]
    v=[d for d in ev if not np.isnan(f252[d])]; n=len(v)
    if n==0: continue
    m=np.mean([f252[d] for d in v]); sr=np.mean([mx252[d]>=0.30 for d in v]); fk=np.mean([mx252[d]<0.10 for d in ev])
    if n not in nullcache: nullcache[n]=rand_null(n)
    Mn,SRn=nullcache[n]
    pm=(Mn>=m).mean(); ps=(SRn>=sr).mean()
    caught=[];
    for t0,v0,pk in G:
        i0=idx.get_loc(t0); hit=[d for d in ev if i0<=idx.get_loc(d)<=i0+126]
        caught.append((t0.date().isoformat(), hit[0].date().isoformat() if hit else None, round((px[hit[0]]/v0-1)*100) if hit else None))
    ncaught=sum(1 for c in caught if c[1])
    half1=[d for d in v if d<=pd.Timestamp('2010-12-31')]; half2=[d for d in v if d>pd.Timestamp('2010-12-31')]
    rows.append(dict(logic=nm,n=len(ev),n252=n,mean252=m,success30=sr,fake10=fk,worst126=np.mean([mn126[d] for d in ev]),
        p_mean=pm,p_succ=ps,bonf_mean=min(1,pm*9),bonf_succ=min(1,ps*9),caught=f"{ncaught}/{len(G)}",
        mean_h1=np.mean([f252[d] for d in half1]) if half1 else np.nan,mean_h2=np.mean([f252[d] for d in half2]) if half2 else np.nan,
        n_h1=len(half1),n_h2=len(half2),entry_vs_trough=np.nanmean([c[2] for c in caught if c[2] is not None]) if ncaught else np.nan))
R=pd.DataFrame(rows)
zb=f252[[d for d in zpool]]
print("\nZone baseline: n=%d mean=%.3f success30=%.3f fake10=%.3f"%(len(zpool),np.mean(F[zi]),np.mean(MX[zi]>=0.3),np.mean(MX[zi]<0.1)))
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',260,'display.max_columns',30): print(R.to_string())
R.to_csv(S+'/work/logic_entry_compare.csv',index=False); json.dump(evlog,open(S+'/work/logic_entry_events.json','w'),indent=0)
# ---------- strategies ----------
ret=px.pct_change().fillna(0)
def hyst(on,off):
    pos=np.zeros(len(idx)); cur=0
    for i in range(len(idx)):
        if cur==0 and on.iloc[i]: cur=1
        elif cur==1 and off.iloc[i]: cur=0
        pos[i]=cur
    return pd.Series(pos,index=idx)
def event_strat(entry_sig):
    ev=set(events(entry_sig,cool=0)); pos=np.zeros(len(idx)); cur=0
    off=(px<0.97*ma200).values
    for i,d in enumerate(idx):
        if cur==0 and d in ev: cur=1
        elif cur==1 and off[i]: cur=0
        pos[i]=cur
    return pd.Series(pos,index=idx)
MAh=hyst(px>ma200,px<0.97*ma200); BR=hyst(pct>=0.60,pct<=0.40)
strat={'BH':pd.Series(1.0,index=idx),'MA':(px>ma200).astype(float),'MAh':MAh,'BR':BR,
       'MAh&BR':((MAh>0)&(BR>0)).astype(float),'MAh|BR':((MAh>0)|(BR>0)).astype(float),
       'evC':event_strat(cand['C']),'evB':event_strat(cand['B']),'MAh-FED':(MAh*(~fed)).astype(float),
       'FXr':(fx<fx.rolling(200).mean()).astype(float)}
def perf(pos,a,z):
    p=pos.shift(1).fillna(0)          # trade next day
    sw=p.diff().abs().fillna(0)
    r=(p*ret-sw*0.001)[a:z]; eq=(1+r).cumprod()
    yrs=(r.index[-1]-r.index[0]).days/365.25
    cagr=eq.iloc[-1]**(1/yrs)-1; vol=r.std()*np.sqrt(252); mdd=(eq/eq.cummax()-1).min()
    return dict(CAGR=cagr,vol=vol,MDD=mdd,ret_mdd=cagr/abs(mdd) if mdd<0 else np.nan,expo=p[a:z].mean(),switches=int(sw[a:z].sum()))
periods={'full':('1996-03-01','2026-10-30'),'h1':('1996-03-01','2010-12-31'),'h2':('2011-01-01','2026-10-30')}
P=[]
for nm,pos in strat.items():
    for pk,(a,z) in periods.items():
        d=perf(pos,a,z); d.update(strategy=nm,period=pk); P.append(d)
P=pd.DataFrame(P)
piv=P.pivot(index='strategy',columns='period',values='ret_mdd')
P.to_csv(S+'/work/logic_strategy_compare.csv',index=False)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',260):
    for pk in periods: print(f"\n--- {pk} ---"); print(P[P.period==pk].drop(columns='period').set_index('strategy').to_string())
# capture in mechanical cycles and bear legs
print("\n--- Capture: strategy return / BH return inside windows ---")
bulls=[(g[0],px.index[px.index.get_indexer([g[0]])[0]+min(252,len(px)-1-px.index.get_loc(g[0]))]) for g in G]
bears=[(cyc[j][1],cyc[j+1][1]) for j in range(len(cyc)-1) if cyc[j][0]=='P' and cyc[j][1]>=START and cyc[j+1][2]/cyc[j][2]-1<=-0.25]
cap=[]
for nm,pos in strat.items():
    p=pos.shift(1).fillna(0)
    def wret(a,z): return float((1+(p*ret)[a:z]).prod()-1)
    bw=[wret(a,z) for a,z in bulls]; bh=[float((1+ret[a:z]).prod()-1) for a,z in bulls]
    br=[wret(a,z) for a,z in bears]; brh=[float((1+ret[a:z]).prod()-1) for a,z in bears]
    cap.append(dict(strategy=nm,bull_capture=np.mean([x/y for x,y in zip(bw,bh)]),bear_loss=np.mean(br),bear_loss_BH=np.mean(brh)))
C=pd.DataFrame(cap); C.to_csv(S+'/work/logic_capture.csv',index=False)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',200): print(C.to_string())
print("bull windows:",[(a.date(),z.date()) for a,z in bulls]); print("bear legs (>=25%):",[(a.date(),z.date()) for a,z in bears])
# rank stability
rk=pd.DataFrame({'h1':piv['h1'].rank(ascending=False),'h2':piv['h2'].rank(ascending=False)}); rk['avg']=rk.mean(axis=1)
rk['beats_BH_both']=(piv['h1']>piv.loc['BH','h1'])&(piv['h2']>piv.loc['BH','h2'])
print("\n--- Rank stability (ret/MDD) ---"); print(rk.sort_values('avg').to_string())
# current state of each strategy
print("\n--- Position today ---", {nm:int(pos.iloc[-1]) for nm,pos in strat.items()})
