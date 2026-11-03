"""KOSPI 신호등 — daily signal computation (rules fixed in research/prereg_logic_compare.md, report v4).

usage: python3 -I daily_signal.py <workdir> <out.json>
Downloads public data into <workdir>/raw (GitHub raw), computes today's state, writes JSON for the dashboard.
Rules (identical to the validated v4 decision structure):
  zone   : min drawdown vs 252d high over last 126d <= -20%  OR  min(% stocks above own 200DMA) over last 126d < 20%
  FX     : zone & USD/KRW(prev day) <= 0.95 * its 126d max & KOSPI close > 50DMA  -> 50% starter
           exit: before first close above 200DMA -> close < entry*0.90 ; after -> close < 0.97*200DMA
  CORE   : trend hysteresis (on close>200DMA, off close<0.97*200DMA) AND breadth hysteresis (on >=60%, off <=40%) -> 100%
  position = 100% if CORE, else 50% if FX trade open, else 0%
"""
import sys, os, io, json, glob, urllib.request, datetime as dt
import pandas as pd, numpy as np
W=sys.argv[1]; OUT=sys.argv[2]; RAW=os.path.join(W,'raw'); os.makedirs(RAW,exist_ok=True)
today=dt.date.today(); Y=today.year
def get(url,path,binary=False,optional=False):
    try:
        with urllib.request.urlopen(url,timeout=180) as r: data=r.read()
        open(path,'wb').write(data); return path
    except Exception as e:
        if optional: print('optional fetch failed',url,e); return None
        raise
# 1) KOSPI index (3 years)
ks=[]
for y in (Y-2,Y-1,Y):
    p=get(f'https://raw.githubusercontent.com/FinanceData/fdr_krx_data_cache/master/data/index/year_ks11/{y}.csv',f'{RAW}/ks11_{y}.csv',optional=(y==Y-2))
    if p: ks.append(pd.read_csv(p,encoding='utf-8-sig'))
k=pd.concat(ks); k['Date']=pd.to_datetime(k['Date']); k=k.drop_duplicates('Date').set_index('Date').sort_index()
px=k['Close'].astype(float); idx=px.index
# 2) breadth from all-stock daily data (3 years), split-adjusted via exchange-reported daily change
frames=[]
for y in (Y-2,Y-1,Y):
    p=get(f'https://raw.githubusercontent.com/FinanceData/marcap/master/data/marcap-{y}.parquet',f'{RAW}/marcap_{y}.parquet',optional=(y==Y-2))
    if p: frames.append(pd.read_parquet(p,columns=['Date','Code','Close','ChangesRatio','Marcap','Market']))
m=pd.concat(frames); m['Date']=pd.to_datetime(m['Date'])
m=m[(m.Market=='KOSPI')&m.Code.str.endswith('0')&(m.Close>0)].drop_duplicates(['Date','Code'])
close=m.pivot(index='Date',columns='Code',values='Close'); chg=m.pivot(index='Date',columns='Code',values='ChangesRatio')
mcap=m.pivot(index='Date',columns='Code',values='Marcap')
raw=close/close.shift(1)-1; r=(chg/100).where(chg.notna(),raw).where(close.notna())
r=r.mask(close.notna()&close.shift(1).isna(),0.0); adj=(1+r.fillna(0)).cumprod().where(close.notna())
ma200s=adj.rolling(200,min_periods=200).mean(); ma50s=adj.rolling(50,min_periods=50).mean()
v200=ma200s.notna()&adj.notna(); v50=ma50s.notna()&adj.notna()
pct200=((adj>ma200s)&v200).sum(axis=1)/v200.sum(axis=1).replace(0,np.nan)
pct50=((adj>ma50s)&v50).sum(axis=1)/v50.sum(axis=1).replace(0,np.nan)
hi252s=adj.rolling(252,min_periods=200).max(); lo252s=adj.rolling(252,min_periods=200).min(); v252=hi252s.notna()&adj.notna()
nh=((adj>=hi252s)&v252).sum(axis=1)/v252.sum(axis=1).replace(0,np.nan); nl=((adj<=lo252s)&v252).sum(axis=1)/v252.sum(axis=1).replace(0,np.nan)
top2=(mcap.get('005930',0).fillna(0)+mcap.get('000660',0).fillna(0))/mcap.sum(axis=1)
turn=None
breadth_date=pct200.dropna().index.max()
B=pd.DataFrame({'pct200':pct200,'pct50':pct50,'nh52':nh,'nl52':nl,'top2':top2}).reindex(idx)
# 3) USD/KRW: FRED-based mirror (history) + daily Yahoo spot from a public feed for the most recent days
p=get('https://raw.githubusercontent.com/datasets/exchange-rates/main/data/daily.csv',f'{RAW}/fx.csv')
f=pd.read_csv(p); f=f[f.Country=='South Korea']; f['Date']=pd.to_datetime(f['Date'])
fx=pd.to_numeric(f.set_index('Date').iloc[:,-1],errors='coerce').dropna(); fx_src={'history':'datasets/exchange-rates (FRED), last '+fx.index.max().date().isoformat()}
recent={}
d=fx.index.max().date()+dt.timedelta(days=1)
while d<=today:
    q=get(f'https://raw.githubusercontent.com/suchoforchat-creator/krx-feed/main/out/daily/{d:%Y%m%d}.csv',f'{RAW}/feed_{d:%Y%m%d}.csv',optional=True)
    if q:
        try:
            t=pd.read_csv(q); row=t[(t.asset=='USD/KRW')&(t.key=='spot')]
            if len(row) and pd.notna(row.value.iloc[-1]):
                note=str(row.notes.iloc[-1]); sd=d
                if 'source_date=' in note:
                    try: sd=dt.date.fromisoformat(note.split('source_date=')[1][:10])
                    except Exception: pass
                recent[pd.Timestamp(sd)]=float(row.value.iloc[-1])
        except Exception as e: print('feed parse fail',d,e)
    d+=dt.timedelta(days=1)
if recent:
    fx=pd.concat([fx,pd.Series(recent)]).sort_index(); fx=fx[~fx.index.duplicated(keep='last')]
    fx_src['recent']='suchoforchat-creator/krx-feed (Yahoo KRW=X), last '+max(recent).date().isoformat()
fxa=fx.reindex(fx.index.union(idx)).ffill().reindex(idx); fx1=fxa.shift(1)
# 3b) foreign investor 20-day net buying on KOSPI (reference only, not part of the validated rules)
ff=None
q=get('https://raw.githubusercontent.com/james-brand/korea-market-data/main/data/foreign-flows-aggregates.csv',f'{RAW}/ff.csv',optional=True)
if q:
    try:
        head=open(q,encoding='utf-8').readline()
        t=pd.read_csv(q,comment='#'); t=t[t.market=='KOSPI']
        asof=head.split('as of')[1].split('·')[0].strip() if 'as of' in head else None
        ff={'as_of':asof,'net_20d_krw_tn':round(float(t.f_20d_val.sum())/1e12,2),'net_5d_krw_tn':round(float(t.f_5d_val.sum())/1e12,2)}
    except Exception as e: print('ff parse fail',e)
# 4) indicators and rules
ma200=px.rolling(200).mean(); ma50=px.rolling(50).mean(); hi=px.rolling(252,min_periods=120).max(); dd=px/hi-1
Z=(dd.rolling(126,min_periods=1).min()<=-0.20)|(B['pct200'].rolling(126,min_periods=1).min()<0.20)
fxmax=fx1.rolling(126,min_periods=63).max(); fxratio=fx1/fxmax
fxsig=Z&(fxratio<=0.95)&(px>ma50)
START=pd.Timestamp(f'{Y-1}-01-02')
P=px.values; M=ma200.values; pc=B['pct200'].values
pos_fx=np.zeros(len(idx)); pos_mah=np.zeros(len(idx)); pos_br=np.zeros(len(idx))
cur=0; entry=np.nan; armed=False; trades=[]; e_date=None
mah=0; br=0
for i,dte in enumerate(idx):
    if dte<START or np.isnan(M[i]): continue
    # trend hysteresis
    if mah==0 and P[i]>M[i]: mah=1
    elif mah==1 and P[i]<0.97*M[i]: mah=0
    # breadth hysteresis (carry state if breadth missing for the day)
    if not np.isnan(pc[i]):
        if br==0 and pc[i]>=0.60: br=1
        elif br==1 and pc[i]<=0.40: br=0
    # FX starter
    if cur==0:
        if bool(fxsig.iloc[i]): cur=1; entry=P[i]; armed=P[i]>M[i]; e_date=dte
    else:
        if not armed and P[i]>M[i]: armed=True
        if (not armed and P[i]<0.90*entry) or (armed and P[i]<0.97*M[i]):
            trades.append({'entry':e_date.date().isoformat(),'entry_lvl':round(entry,2),'exit':dte.date().isoformat(),'exit_lvl':round(P[i],2),'ret':round(P[i]/entry-1,4)}); cur=0
    pos_fx[i]=cur; pos_mah[i]=mah; pos_br[i]=br
core=(pos_mah>0)&(pos_br>0)
position=np.where(core,1.0,np.where(pos_fx>0,0.5,0.0))
# warning score (5 of the 6 original components; turnover froth omitted for data-size reasons)
ret=np.log(px).diff()
Bf=B.ffill()
warn={'stretch':bool(px.iloc[-1]/ma200.iloc[-1]-1>0.25),
      'breadth_div':bool(Bf['pct200'].iloc[-1]-Bf['pct200'].rolling(250,min_periods=100).max().iloc[-1]<-0.25),
      'top2_up':bool(Bf['top2'].iloc[-1]-Bf['top2'].shift(120).iloc[-1]>0.05),
      'vol_up':bool(ret.rolling(20).std().iloc[-1]/ret.rolling(250).std().iloc[-1]>1.3),
      'fx_weak':bool(fxa.iloc[-1]/fxa.shift(60).iloc[-1]-1>0.03)}
# carry last available breadth for 'today' display
Bl=B.ffill()
last=idx[-1]; i=len(idx)-1
state_prev=position[i-1] if i>0 else 0
def r2(x,n=2): return None if x is None or (isinstance(x,float) and np.isnan(x)) else round(float(x),n)
out={
 'generated_at_kst':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M'),
 'as_of':last.date().isoformat(),'breadth_as_of':breadth_date.date().isoformat() if pd.notna(breadth_date) else None,
 'fx_source':fx_src,'fx_as_of':fx.index.max().date().isoformat(),
 'kospi':r2(px.iloc[-1]),'kospi_chg':r2(px.iloc[-1]/px.iloc[-2]-1,4),'ma50':r2(ma50.iloc[-1]),'ma200':r2(ma200.iloc[-1]),
 'exit_level':r2(0.97*ma200.iloc[-1]),'dd_from_high':r2(dd.iloc[-1],4),'high_252':r2(hi.iloc[-1]),
 'pct200':r2(Bl['pct200'].iloc[-1],4),'pct50':r2(Bl['pct50'].iloc[-1],4),'nh52':r2(Bl['nh52'].iloc[-1],4),'nl52':r2(Bl['nl52'].iloc[-1],4),'top2':r2(Bl['top2'].iloc[-1],4),
 'usdkrw':r2(fx1.iloc[-1]),'usdkrw_126max':r2(fxmax.iloc[-1]),'fx_ratio':r2(fxratio.iloc[-1],4),
 'zone':bool(Z.iloc[-1]),'fx_signal_today':bool(fxsig.iloc[-1]),'fx_trade_open':bool(pos_fx[i]>0),
 'fx_entry':{'date':e_date.date().isoformat(),'level':r2(entry),'stop':r2(0.90*entry),'armed':armed} if pos_fx[i]>0 else None,
 'trend_on':bool(pos_mah[i]>0),'breadth_on':bool(pos_br[i]>0),'core_on':bool(core[i]),
 'position':float(position[i]),'position_prev':float(state_prev),'state_changed':bool(position[i]!=state_prev),
 'warn':warn,'warn_score':int(sum(1 for v in warn.values() if v)),
 'triggers':{
   'fx_need_close_above_ma50':r2(ma50.iloc[-1]),'fx_gap_to_ma50_pct':r2(ma50.iloc[-1]/px.iloc[-1]-1,4),
   'fx_ratio_needed':0.95,'core_need_close_above_ma200':r2(ma200.iloc[-1]),'core_gap_to_ma200_pct':r2(ma200.iloc[-1]/px.iloc[-1]-1,4),
   'core_need_breadth':0.60},
 'recent_trades':trades[-5:],
 'foreign_flow':ff,
}
H=pd.DataFrame({'date':idx.strftime('%Y-%m-%d'),'kospi':px.values,'ma50':ma50.values,'ma200':ma200.values,'pct200':B['pct200'].values,
                'fx':fx1.values,'fx_th':(0.95*fxmax).values,'pos':position,'fxsig':fxsig.values.astype(int),'zone':Z.values.astype(int)}).iloc[-260:]
out['history']={c:[(None if (isinstance(v,float) and np.isnan(v)) else (round(v,4) if isinstance(v,float) else v)) for v in H[c].tolist()] for c in H.columns}
json.dump(out,open(OUT,'w'),ensure_ascii=False,indent=1)
print(json.dumps({k:v for k,v in out.items() if k not in ('history',)},ensure_ascii=False,indent=1))

# 5) dashboard dataset files (row-object JSON) next to OUT
D=os.path.dirname(os.path.abspath(OUT))
tg=out['triggers']; fe=out['fx_entry'] or {}; ffl=out['foreign_flow'] or {}
status={'as_of':out['as_of'],'breadth_as_of':out['breadth_as_of'],'fx_as_of':out['fx_as_of'],'generated_at_kst':out['generated_at_kst'],
 'kospi':out['kospi'],'kospi_chg':out['kospi_chg'],'ma50':out['ma50'],'ma200':out['ma200'],'exit_level':out['exit_level'],
 'dd_from_high':out['dd_from_high'],'high_252':out['high_252'],'pct200':out['pct200'],'pct50':out['pct50'],'nl52':out['nl52'],'top2':out['top2'],
 'usdkrw':out['usdkrw'],'usdkrw_126max':out['usdkrw_126max'],'fx_ratio':out['fx_ratio'],'fx_ratio_needed':0.95,
 'zone':int(out['zone']),'fx_signal_today':int(out['fx_signal_today']),'fx_trade_open':int(out['fx_trade_open']),
 'fx_cond_krw':int(out['fx_ratio'] is not None and out['fx_ratio']<=0.95),'fx_cond_ma50':int(out['kospi']>out['ma50']),
 'trend_on':int(out['trend_on']),'breadth_on':int(out['breadth_on']),'core_on':int(out['core_on']),
 'position':out['position'],'position_prev':out['position_prev'],'state_changed':int(out['state_changed']),
 'warn_score':out['warn_score'],'warn_stretch':int(bool(out['warn']['stretch'])),'warn_breadth_div':int(bool(out['warn']['breadth_div'])),
 'warn_top2_up':int(bool(out['warn']['top2_up'])),'warn_vol_up':int(bool(out['warn']['vol_up'])),'warn_fx_weak':int(bool(out['warn']['fx_weak'])),
 'gap_to_ma50':tg['fx_gap_to_ma50_pct'],'gap_to_ma200':tg['core_gap_to_ma200_pct'],
 'fx_entry_date':fe.get('date'),'fx_entry_level':fe.get('level'),'fx_stop':fe.get('stop'),
 'krw_strength':r2(1-out['fx_ratio'],4) if out['fx_ratio'] is not None else None,
 'kospi_vs_ma50':r2(out['kospi']/out['ma50']-1,4),'kospi_vs_ma200':r2(out['kospi']/out['ma200']-1,4),
 'breadth_to_on':r2(0.60-out['pct200'],4) if out['pct200'] is not None else None,
 'fx_conds_met':int(out['zone'])+int(out['fx_ratio'] is not None and out['fx_ratio']<=0.95)+int(out['kospi']>out['ma50']),
 'core_conds_met':int(out['trend_on'])+int(out['breadth_on']),
 'foreign_20d_tn':ffl.get('net_20d_krw_tn'),'foreign_5d_tn':ffl.get('net_5d_krw_tn'),'foreign_as_of':ffl.get('as_of')}
json.dump([status],open(os.path.join(D,'status.json'),'w'),ensure_ascii=False)
hist=[dict(zip(out['history'].keys(),vals)) for vals in zip(*out['history'].values())]
json.dump(hist,open(os.path.join(D,'history.json'),'w'),ensure_ascii=False)
json.dump(trades[-8:] if trades else [],open(os.path.join(D,'trades.json'),'w'),ensure_ascii=False)
print('dashboard files written to',D)
