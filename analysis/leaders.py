# Do early relative-strength leaders keep leading through the cycle? (ex-ante lookback only)
import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
from scipy.stats import spearmanr
close=pd.read_parquet(S+'/work/close.parquet'); mcap=pd.read_parquet(S+'/work/mcap.parquet')
names=pd.read_csv(S+'/work/names.csv',dtype=str).set_index('Code')['Name']
desc=pd.read_csv(S+'/ext/fdrcache/data/listing/desc/2026-11-02.csv',dtype=str,encoding='utf-8-sig').set_index('Code')
ind=desc['Industry']
dates=close.index
def test(D_idx, LB=60, FW=250, topN=300):
    D=dates[D_idx]; s=dates[D_idx-LB]; e=dates[min(D_idx+FW,len(dates)-1)]
    mc=mcap.loc[D].dropna(); uni=mc.sort_values(ascending=False).index[:topN]
    c0=close.loc[s,uni]; c1=close.loc[D,uni]; c2=close.loc[e,uni]
    # forward: if delisted before e, use last available price (approximation; survivorship-safe-ish)
    last=close.loc[D:e,uni].ffill().iloc[-1]
    lb=(c1/c0-1); fw=(last/c1-1)
    ok=lb.notna()&fw.notna()&np.isfinite(lb)&np.isfinite(fw); lb,fw=lb[ok],fw[ok]
    if len(lb)<50: return None,None,None
    w=mc[lb.index]
    mkt=(fw*w).sum()/w.sum()
    q=pd.qcut(lb.rank(method='first'),5,labels=False)
    qret=fw.groupby(q).mean()
    rho=spearmanr(lb,fw).correlation
    return dict(D=D.date(),end=e.date(),n=len(lb),rho=rho,Q5_top=qret.iloc[-1],Q1_bot=qret.iloc[0],EW_all=fw.mean(),CW_mkt=mkt,spread=qret.iloc[-1]-qret.iloc[0]), lb, fw
troughs={'1998':'1998-06-16','2001':'2001-09-17','2003':'2003-03-17','2008':'2008-10-24','2016':'2016-02-12','2020':'2020-03-19','2022(fail)':'2022-09-30','2025':'2025-04-09'}
rows=[]
for nm,t in troughs.items():
    ti=dates.get_indexer([pd.Timestamp(t)],method='nearest')[0]
    for off in (40,60):
        r,lb,fw=test(ti+off); r['cycle']=nm; r['D_offset']=off; rows.append(r)
res=pd.DataFrame(rows)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',250): print(res.to_string())
res.to_csv(S+'/work/leaders_cycles.csv',index=False)
# null: every 21 days 1996-2025
null=[]
for i in range(300,len(dates)-260,21):
    r,_,_=test(i)
    if r: null.append(r)
nl=pd.DataFrame(null)
print("\nNULL (all dates, every 21d): n=%d  mean rho=%.3f  median rho=%.3f  mean Q5-Q1 spread=%.3f  frac rho>0=%.2f"%(len(nl),nl.rho.mean(),nl.rho.median(),nl.spread.mean(),(nl.rho>0).mean()))
cs=res[res.D_offset==60]
print("CYCLE STARTS (D=T+60): mean rho=%.3f  mean spread=%.3f  frac rho>0=%.2f"%(cs.rho.mean(),cs.spread.mean(),(cs.rho>0).mean()))
nl.to_csv(S+'/work/leaders_null.csv',index=False)
# percentile of each cycle rho in null
for _,r in cs.iterrows():
    print(r['cycle'], 'rho pct-rank vs null: %.0f%%'%((nl.rho<r.rho).mean()*100), ' spread pct-rank: %.0f%%'%((nl.spread<r.spread).mean()*100))
