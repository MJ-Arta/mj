"""Post-hoc (exploratory): FX-entry strategies and corrected capture metric."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
k=kospi(); px=k['Close']['1995-05-01':]; idx=px.index
b=breadth().reindex(idx); pct=b['pct200']
fx1=usdkrw().reindex(idx,method='ffill').shift(1)
ma200=px.rolling(200).mean(); ma50=px.rolling(50).mean(); hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
Z=(dd.rolling(126,min_periods=1).min()<=-0.20)|(pct.rolling(126,min_periods=1).min()<0.20)
START=pd.Timestamp('1996-03-01'); ret=px.pct_change().fillna(0)
fxsig=(fx1<=0.95*fx1.rolling(126,min_periods=63).max())&(px>ma50)&Z
csig=(pct>0.60)&Z
def hyst(on,off):
    pos=np.zeros(len(idx)); cur=0
    for i in range(len(idx)):
        if cur==0 and on.iloc[i]: cur=1
        elif cur==1 and off.iloc[i]: cur=0
        pos[i]=cur
    return pd.Series(pos,index=idx)
off=px<0.97*ma200
MAh=hyst(px>ma200,off); BR=hyst(pct>=0.60,pct<=0.40)
# event strategy with two-stage exit (post-hoc): before first close above MA200 -> stop at entry*0.90;
# after that -> exit at close < 0.97*MA200. Re-entry only on a new signal day.
P_=px.values; M_=ma200.values
def ev2(sig):
    sg=sig.fillna(False).values; pos=np.zeros(len(idx)); cur=0; entry=0; armed=False
    for i in range(len(idx)):
        if cur==0:
            if sg[i] and idx[i]>=START: cur=1; entry=P_[i]; armed=P_[i]>M_[i]
        else:
            if not armed and P_[i]>M_[i]: armed=True
            if (not armed and P_[i]<0.90*entry) or (armed and P_[i]<0.97*M_[i]): cur=0
        pos[i]=cur
    return pd.Series(pos,index=idx)
bsig=Z&(px>ma200)&(px.shift(1)<=ma200.shift(1))
S={'BH':pd.Series(1.0,index=idx),'MAh':MAh,'MAh&BR':((MAh>0)&(BR>0)).astype(float),'BR':BR,
   'evFX':ev2(fxsig),'evC':ev2(csig),'evB':ev2(bsig),'evFX|evC':ev2(fxsig|csig),
   'MAh&BR | evFX':(((MAh>0)&(BR>0))|(ev2(fxsig)>0)).astype(float)}
def perf(pos,a,z):
    p=pos.shift(1).fillna(0); sw=p.diff().abs().fillna(0); r=(p*ret-sw*0.001)[a:z]; eq=(1+r).cumprod()
    yrs=(r.index[-1]-r.index[0]).days/365.25; cagr=eq.iloc[-1]**(1/yrs)-1; mdd=(eq/eq.cummax()-1).min()
    return cagr, mdd, cagr/abs(mdd), p[a:z].mean(), int(sw[a:z].sum())
cyc=find_cycles(px,0.20)
G=['1997-12-12','2000-12-22','2003-03-17','2004-08-02','2008-10-24','2020-03-19','2025-04-09']
bulls=[(pd.Timestamp(g),idx[min(idx.get_loc(pd.Timestamp(g))+252,len(idx)-1)]) for g in G]
bears=[(cyc[j][1],cyc[j+1][1]) for j in range(len(cyc)-1) if cyc[j][0]=='P' and cyc[j][1]>=START and cyc[j+1][2]/cyc[j][2]-1<=-0.25]
rows=[]
for nm,pos in S.items():
    p=pos.shift(1).fillna(0); lr=np.log1p(p*ret); lb=np.log1p(ret)
    cap=sum(lr[a:z].sum() for a,z in bulls)/sum(lb[a:z].sum() for a,z in bulls)
    bear=np.mean([np.expm1(lr[a:z].sum()) for a,z in bears])
    r={'strategy':nm}
    for pk,(a,z) in {'full':('1996-03-01','2026-10-30'),'h1':('1996-03-01','2010-12-31'),'h2':('2011-01-01','2026-10-30')}.items():
        c,m,rm,e,sw=perf(pos,a,z); r.update({f'{pk}_CAGR':c,f'{pk}_MDD':m,f'{pk}_ret/MDD':rm})
        if pk=='full': r.update(expo=e,switches=sw)
    r.update(bull_capture_log=cap,avg_bear_leg=bear,pos_today=int(pos.iloc[-1])); rows.append(r)
R=pd.DataFrame(rows).set_index('strategy')
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',300,'display.max_columns',30): print(R.to_string())
R.to_csv(os.environ['KOSPI_ROOT']+'/work/logic_strategy_v2.csv')
# FX trades with stop
print("\nFX entry trades (two-stage exit):")
pos=S['evFX']; p=pos.values; i=0; trades=[]
while i<len(p):
    if p[i]==1 and (i==0 or p[i-1]==0):
        j=i
        while j<len(p) and p[j]==1: j+=1
        ex=min(j,len(p)-1); trades.append((idx[i].date(),idx[ex].date(),round(px.iloc[ex]/px.iloc[i]-1,3),round(px.iloc[i:ex+1].max()/px.iloc[i]-1,3),j>=len(p)))
        i=j
    else: i+=1
for t in trades: print('  ',t)
T0=pd.DataFrame(trades,columns=['entry','exit','ret','peak','open']); T0.to_csv(os.environ['KOSPI_ROOT']+'/work/fx_trades.csv',index=False)
T=pd.DataFrame(trades,columns=['entry','exit','ret','peak','open']); c=T[~T.open]
print("closed %d, wins %d avg %.3f, losses %d avg %.3f, EV %.3f"%(len(c),(c.ret>0).sum(),c[c.ret>0].ret.mean(),(c.ret<=0).sum(),c[c.ret<=0].ret.mean(),c.ret.mean()))
