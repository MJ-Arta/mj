"""Post-hoc illustration: core regime (MAh&BR, pre-registered winner) + FX starter position (50%)."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'fx_strategy.py')).read().split("rows=[]")[0])
core=((MAh>0)&(BR>0)).astype(float); fxp=ev2(fxsig)
combo=pd.Series(np.where(core>0,1.0,np.where(fxp>0,0.5,0.0)),index=idx)
for nm,pos in {'MAh&BR':core,'core+FX50%':combo,'BH':pd.Series(1.0,index=idx)}.items():
    out=[]
    for pk,(a,z) in {'full':('1996-03-01','2026-10-30'),'h1':('1996-03-01','2010-12-31'),'h2':('2011-01-01','2026-10-30')}.items():
        c,m,rm,e,sw=perf(pos,a,z); out.append(f"{pk}: CAGR {c:.3f} MDD {m:.3f} ret/MDD {rm:.3f} expo {e:.2f}")
    p=pos.shift(1).fillna(0); lr=np.log1p(p*ret); lb=np.log1p(ret)
    cap=sum(lr[a:z].sum() for a,z in bulls)/sum(lb[a:z].sum() for a,z in bulls)
    bear=np.mean([np.expm1(lr[a:z].sum()) for a,z in bears])
    print(nm,' | '.join(out),f"| bull capture {cap:.2f} | avg bear leg {bear:.3f}")
# current trigger levels
fxmax=fx1.rolling(126,min_periods=63).max()
print("\nToday: KOSPI %.1f  MA50 %.1f  MA200 %.1f  0.97*MA200 %.1f"%(px.iloc[-1],ma50.iloc[-1],ma200.iloc[-1],0.97*ma200.iloc[-1]))
print("USD/KRW (lag1) %.1f  126d max %.1f  ratio %.3f (signal needs <=0.95)"%(fx1.iloc[-1],fxmax.iloc[-1],fx1.iloc[-1]/fxmax.iloc[-1]))
print("Zone active:",bool(Z.iloc[-1]),"  breadth pct200 %.3f"%pct.iloc[-1])
print("core pos",core.iloc[-1],"fx pos",fxp.iloc[-1],"MAh",MAh.iloc[-1],"BR",BR.iloc[-1])
