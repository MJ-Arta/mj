import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
k=kospi(); px=k['Close']; b=breadth().reindex(px.index)
ma200=px.rolling(200).mean(); hi252=px.rolling(252,min_periods=120).max()
dd=px/hi252-1
deep=dd.rolling(126,min_periods=1).min()<=-0.20
ema_adv=b['adv'].ewm(span=10,adjust=False).mean()
# signal definitions (all use info available at close of day t)
sig={}
lowin10=ema_adv.rolling(10).min()<0.40
sig['A_breadth_thrust']=(ema_adv>0.615)&lowin10
sig['B_trend_reclaim']=deep&(px>ma200)&(px.shift(1)<=ma200.shift(1))
pct200=b['pct200']
sig['C_breadth_recovery']=(pct200>0.60)&(pct200.rolling(126,min_periods=1).min()<0.20)
sig['D_leaders_newhigh']=(b['nh52']>=0.05)&(dd<=-0.15)
fwd={h:px.shift(-h)/px-1 for h in (63,126,252)}
mxf=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
def events(s,cool=126):
    out=[];last=None
    for d in s[s.fillna(False)].index:
        if last is None or (px.index.get_loc(d)-px.index.get_loc(last))>cool: out.append(d); last=d
    return out
cyc=find_cycles(px,0.20)
bulls=[(cyc[j][1],cyc[j+1][1],cyc[j][2],cyc[j+1][2]) for j in range(len(cyc)-1) if cyc[j][0]=='T']
def which_bull(d):
    for t0,t1,v0,v1 in bulls:
        if t0<=d<=t1: return t0,t1,v0,v1
    return None
base={h:(fwd[h].mean(),(fwd[h]>0).mean()) for h in fwd}
print("BASELINE all days: ", {h:(round(m*100,1),round(p*100)) for h,(m,p) in base.items()})
summary=[]
for name,s in sig.items():
    ev=events(s); rows=[]
    for d in ev:
        wb=which_bull(d); cap=None; lag=None
        if wb:
            t0,t1,v0,v1=wb; cap=(v1/px[d]-1)/(v1/v0-1) if v1>v0 else None; lag=(px.index.get_loc(d)-px.index.get_loc(t0))
            g=(px[d]/v0-1)
        rows.append(dict(date=d.date(),lvl=round(px[d],1),f63=fwd[63][d],f126=fwd[126][d],f252=fwd[252][d],maxgain252=mxf[d],
              in_bull=(f"{wb[0].date()}->{wb[1].date()} (+{(wb[3]/wb[2]-1)*100:.0f}%)" if wb else '-'),
              days_after_trough=lag, pct_from_trough=(round(g*100,1) if wb else None), share_of_leg_left=(round(cap*100) if cap is not None else None)))
    r=pd.DataFrame(rows)
    print(f"\n=== {name}: {len(r)} events")
    with pd.option_context('display.float_format','{:.3f}'.format,'display.width',250):
        print(r.to_string())
    v=r.dropna(subset=['f252'])
    summary.append(dict(signal=name,n=len(r),n_with_252=len(v),mean_f126=r.f126.mean(),hit_f126=(r.f126>0).mean(),mean_f252=v.f252.mean(),hit_f252=(v.f252>0).mean(),median_f252=v.f252.median()))
    r.to_csv(S+f'/work/sig_{name}.csv',index=False)
sm=pd.DataFrame(summary)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',250): print("\n",sm.to_string())
sm.to_csv(S+'/work/signal_summary.csv',index=False)
