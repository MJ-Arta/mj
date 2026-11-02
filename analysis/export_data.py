import sys, json; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
k=kospi(); px=k['Close']; b=breadth().reindex(px.index).ffill()
close=pd.read_parquet(S+'/work/close.parquet')
out={}
# 1) long KOSPI weekly (Fri) 1995-2026
w=px.resample('W-FRI').last().dropna()
out['kospi_w']=[[d.strftime('%Y-%m-%d'),round(v,1)] for d,v in w.items()]
# signals B and C
for nm in ['B_trend_reclaim','C_breadth_recovery']:
    s=pd.read_csv(S+f'/work/sig_{nm}.csv'); out[nm]=s[['date','lvl','f252','share_of_leg_left']].replace({np.nan:None}).to_dict('records')
out['bulls']=[['1998-06-16','2000-01-04'],['2001-09-17','2002-04-18'],['2003-03-17','2007-10-31'],['2008-10-24','2011-05-02'],['2016-02-12','2018-01-29'],['2020-03-19','2021-07-06'],['2025-04-09','2026-06-22']]
# 2) 2024-07 -> 2026-10 daily
d2=px['2024-07-01':]; bb=b.loc[d2.index]
out['kospi_d']=[[d.strftime('%Y-%m-%d'),round(v,2)] for d,v in d2.items()]
out['top2_d']=[[d.strftime('%Y-%m-%d'),round(v*100,1)] for d,v in bb['top2'].items()]
out['pct200_d']=[[d.strftime('%Y-%m-%d'),round(v*100,1)] for d,v in bb['pct200'].items()]
# 3) Hynix & Samsung weekly 2022-
for code,key in [('000660','hynix_w'),('005930','samsung_w')]:
    c=close[code]['2022-01-01':].resample('W-FRI').last().dropna(); out[key]=[[d.strftime('%Y-%m-%d'),int(v)] for d,v in c.items()]
ws=pd.read_parquet(S+'/work/warn_score.parquet')['score']['2025-06-01':]
out['warn_d']=[[d.strftime('%Y-%m-%d'),int(v)] for d,v in ws.items()]
json.dump(out,open(S+'/work/chartdata.json','w'),ensure_ascii=False,separators=(',',':'))
print('bytes',len(json.dumps(out)))
# current status
last=b.index[-1]; print('last breadth date',last.date())
ma200=px.rolling(200).mean()
print('KOSPI',px.iloc[-1],'ext200=%.3f'%(px.iloc[-1]/ma200.iloc[-1]-1),'ma200=%.0f'%ma200.iloc[-1])
print({c:round(float(b[c].iloc[-1]),3) for c in ['pct200','pct50','top2','nh52','nl52']}, 'adv20', round(float(b['adv'].rolling(20).mean().iloc[-1]),3))
print('dd from peak close=%.3f'%(px.iloc[-1]/px.max()-1))
print('warn score last', pd.read_parquet(S+'/work/warn_score.parquet').iloc[-1].to_dict())
fx=usdkrw(); print('USDKRW last',fx.index[-1].date(),fx.iloc[-1],' 2026 max',fx['2026'].max(),fx['2026'].idxmax().date(), ' at 2025-04-09', fx.loc[:'2025-04-09'].iloc[-1])
# signal checks right now
hi252=px.rolling(252,min_periods=120).max(); dd=px/hi252-1
print('dd vs 252d high=%.3f'%dd.iloc[-1],' min pct200 last126=%.3f'%b['pct200'].iloc[-126:].min())
