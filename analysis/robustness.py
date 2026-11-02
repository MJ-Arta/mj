# Robustness: threshold sensitivity of signals B and C; finer ASP lag; 52w-high leaders at T+120 vs null
import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
k=kospi(); px=k['Close']; b=breadth().reindex(px.index)
fwd252=px.shift(-252)/px-1; mx=px[::-1].rolling(252,min_periods=1).max()[::-1].shift(-1)/px-1
def events(s,cool=126):
    out=[];last=None
    for d in s[s.fillna(False)].index:
        if last is None or (px.index.get_loc(d)-px.index.get_loc(last))>cool: out.append(d); last=d
    return out
def stats(ev):
    v=[d for d in ev if not np.isnan(fwd252[d])]
    big=[d for d in ev if d>=pd.Timestamp('1998-06-01') and any(pd.Timestamp(a)<=d<=pd.Timestamp(z) for a,z in BULLS)]
    return len(ev), np.mean([fwd252[d]>0 for d in v]), np.mean([fwd252[d] for d in v]), np.mean([mx[d]<0.10 for d in ev]), len(big)
BULLS=[('1998-06-16','2000-01-04'),('2001-09-17','2002-04-18'),('2003-03-17','2007-10-31'),('2008-10-24','2011-05-02'),('2016-02-12','2018-01-29'),('2020-03-19','2021-07-06'),('2025-04-09','2026-06-22')]
rows=[]
for dd_thr in (-0.15,-0.20,-0.25):
    for ma in (150,200,250):
        m=px.rolling(ma).mean(); hi=px.rolling(252,min_periods=120).max(); deep=(px/hi-1).rolling(126,min_periods=1).min()<=dd_thr
        ev=events(deep&(px>m)&(px.shift(1)<=m.shift(1))); n,hit,mean,fake,inb=stats(ev)
        e25=[d.date() for d in ev if d.year==2025]
        rows.append(('B',f'dd{int(dd_thr*100)} ma{ma}',n,hit,mean,fake,inb,e25))
for lo in (0.15,0.20,0.25):
    for hi_ in (0.55,0.60,0.65):
        p=b['pct200']; ev=events((p>hi_)&(p.rolling(126,min_periods=1).min()<lo)); n,hit,mean,fake,inb=stats(ev)
        rows.append(('C',f'lo{lo} hi{hi_}',n,hit,mean,fake,inb,[d.date() for d in ev if d.year==2025]))
r=pd.DataFrame(rows,columns=['sig','params','n','hit252','mean252','fake_share','in_major_bull','2025_dates'])
with pd.option_context('display.float_format','{:.2f}'.format,'display.width',200): print(r.to_string())
r.to_csv(S+'/work/robustness_signals.csv',index=False)
# finer ASP lag
a=json.load(open(S+'/ext/md/data/asp_dram.json')); s=pd.Series({pd.Timestamp(x['date']):x['value'] for x in a['data']}).sort_index().resample('ME').last()
h=pd.read_parquet(S+'/work/close.parquet')['000660'].resample('ME').last().reindex(s.index)
R=pd.DataFrame({'asp':s.pct_change(12),'h':h.pct_change(12)}).dropna()
print('ASP lag (months Hynix leads):',{L:round(R['h'].shift(L).corr(R['asp']),2) for L in range(0,8)})
