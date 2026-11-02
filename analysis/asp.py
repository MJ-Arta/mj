import sys, json; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
a=json.load(open(sys.argv[1])); s=pd.Series({pd.Timestamp(x['date']):x['value'] for x in a['data']}).sort_index()
print(a['metric'],a['source'],len(s),s.index.min().date(),s.index.max().date())
print(s.resample('QE').last().round(3).to_string())
close=pd.read_parquet(S+'/work/close.parquet'); h=close['000660'].dropna()
for a_,b_ in [('2020-06-01','2021-06-30'),('2021-06-01','2023-12-31'),('2023-06-01','2025-12-31')]:
    w=s[a_:b_]; print('ASP window',a_,b_,'min',w.idxmin().date(),w.min(),'max',w.idxmax().date(),w.max())
m=s.resample('ME').last(); hm=h.resample('ME').last().reindex(m.index)
r=pd.DataFrame({'asp_yoy':m.pct_change(12),'hyn_yoy':hm.pct_change(12)}).dropna()
from scipy.stats import pearsonr
for lag in range(-9,10,3):
    x=r['hyn_yoy'].shift(lag); ok=x.notna()
    print('lag',lag,'(hynix leads ASP by %d m)'%lag, 'corr=%.2f'%pearsonr(x[ok],r['asp_yoy'][ok])[0], 'n',ok.sum())
json.dump([[d.strftime('%Y-%m-%d'),v] for d,v in s.items()],open(S+'/work/asp_dram.json','w'))
