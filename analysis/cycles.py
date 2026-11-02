import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
k=kospi(); px=k['Close']
print('KOSPI', px.index.min().date(), px.index.max().date(), len(px))
fx=usdkrw(); print('USDKRW', fx.index.min().date(), fx.index.max().date(), fx.iloc[-1])
piv=find_cycles(px,0.20)
print("\nZig-zag pivots (>=20% reversals):")
rows=[]
for j in range(len(piv)-1):
    t,d,v=piv[j]; t2,d2,v2=piv[j+1]
    rows.append(dict(type=('BULL' if t=='T' else 'BEAR'),start=d.date(),start_lv=round(v,1),end=d2.date(),end_lv=round(v2,1),chg_pct=round((v2/v-1)*100,1),days=(d2-d).days))
r=pd.DataFrame(rows); print(r.to_string())
r.to_csv(S+'/work/cycles_20pct.csv',index=False)
