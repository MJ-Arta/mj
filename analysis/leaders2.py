import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
from scipy.stats import spearmanr
close=pd.read_parquet(S+'/work/close.parquet'); mcap=pd.read_parquet(S+'/work/mcap.parquet')
dates=close.index
hi252=close.rolling(252,min_periods=200).max()
def nh_test(D_idx,FW=250,topN=300,near=0.95,LB=120):
    D=dates[D_idx]; e=dates[min(D_idx+FW,len(dates)-1)]
    mc=mcap.loc[D].dropna(); uni=mc.sort_values(ascending=False).index[:topN]
    c1=close.loc[D,uni]; last=close.loc[D:e,uni].ffill().iloc[-1]; fw=last/c1-1
    h=hi252.loc[D,uni]; lead=(c1>=near*h)
    lbr=c1/close.loc[dates[D_idx-LB],uni]-1
    ok=fw.notna()&h.notna()&np.isfinite(fw)&lbr.notna()
    fw,lead,lbr,w=fw[ok],lead[ok],lbr[ok],mc[ok[ok].index]
    rho=spearmanr(lbr,fw).correlation
    return dict(D=D.date(),n_lead=int(lead.sum()),n=len(fw),lead_fw=fw[lead].mean(),rest_fw=fw[~lead].mean(),diff=fw[lead].mean()-fw[~lead].mean(),rho120=rho)
troughs={'1998':'1998-06-16','2001':'2001-09-17','2003':'2003-03-17','2008':'2008-10-24','2016':'2016-02-12','2020':'2020-03-19','2022(fail)':'2022-09-30','2025':'2025-04-09'}
rows=[]
for nm,t in troughs.items():
    ti=dates.get_indexer([pd.Timestamp(t)],method='nearest')[0]
    for off in (60,120):
        r=nh_test(ti+off); r['cycle']=nm; r['off']=off; rows.append(r)
res=pd.DataFrame(rows)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',250): print(res.to_string())
null=[nh_test(i) for i in range(300,len(dates)-260,21)]
nl=pd.DataFrame(null).dropna()
print("NULL: mean diff(near-52wH minus rest)=%.3f frac>0=%.2f ; mean rho120=%.3f"%(nl['diff'].mean(),(nl['diff']>0).mean(),nl.rho120.mean()))
res.to_csv(S+'/work/leaders_52wh.csv',index=False)
