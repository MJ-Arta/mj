"""Corrected (log-sum) bull capture and bear-leg loss for the pre-registered strategy set."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'logic_compare.py')).read()
pre=src.split("nullcache={}")[0]; strat_part=src.split("# ---------- strategies ----------")[1].split("def perf(")[0]
exec(pre); exec(strat_part)
cyc=find_cycles(px,0.20)
bulls=[(g[0],idx[min(idx.get_loc(g[0])+252,len(idx)-1)]) for g in G]
bears=[(cyc[j][1],cyc[j+1][1]) for j in range(len(cyc)-1) if cyc[j][0]=='P' and cyc[j][1]>=START and cyc[j+1][2]/cyc[j][2]-1<=-0.25]
for nm,pos in strat.items():
    p=pos.shift(1).fillna(0); lr=np.log1p(p*ret); lb=np.log1p(ret)
    cap=sum(lr[a:z].sum() for a,z in bulls)/sum(lb[a:z].sum() for a,z in bulls)
    print(f"{nm:8s} capture {cap:.3f}  bear {np.mean([np.expm1(lr[a:z].sum()) for a,z in bears]):.3f}")
