import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
k=kospi(); px=k['Close']; b=breadth().reindex(px.index).ffill()
fx=usdkrw().reindex(px.index).ffill()
ma200=px.rolling(200).mean(); ret=np.log(px).diff()
F=pd.DataFrame(index=px.index)
F['ext200']=px/ma200-1                                  # stretch above 200DMA
F['pct200']=b['pct200']
F['div_breadth']=b['pct200']-b['pct200'].rolling(250,min_periods=100).max()   # breadth vs its 1y max (negative = divergence)
F['top2_chg120']=b['top2']-b['top2'].shift(120)          # concentration rising
F['turn_z']=(b['turnover'].rolling(20).mean()/b['turnover'].rolling(1250,min_periods=500).median())  # froth
F['vol20_ratio']=ret.rolling(20).std()/ret.rolling(250).std()   # vol rising at highs
F['fx60']=fx/fx.shift(60)-1                              # + = KRW weakening
F['nh_div']=b['nh52']-b['nh52'].rolling(120,min_periods=60).max()
F['adv_neg']=b['adv'].rolling(20).mean()
hi=px.rolling(252,min_periods=200).max(); athish=px>=0.97*hi   # condition: index near 1y high
peaks=['2000-01-04','2002-04-18','2004-04-23','2007-10-31','2011-05-02','2018-01-29','2021-07-06','2024-07-11','2026-06-22']
T=F.loc[[px.index[px.index.get_indexer([pd.Timestamp(p)],method='nearest')[0]] for p in peaks]]
# reference: all days where index within 3% of 1y high (i.e., "looks strong" days)
R=F[athish]
pr=pd.DataFrame({c:[(R[c]<v).mean()*100 for v in T[c]] for c in F.columns},index=T.index)
with pd.option_context('display.float_format','{:.3f}'.format,'display.width',250): 
    print("Values at cycle peaks:\n",T.to_string())
    print("\nMedian of near-high days:\n",R.median().to_string())
    print("\nPercentile of peak value among all near-high days:\n",pr.round(0).to_string())
T.to_csv(S+'/work/top_features.csv'); pr.to_csv(S+'/work/top_feature_pct.csv')
# Composite warning: count of conditions, evaluated on all near-high days, and forward 63/126d drawdown
cond=pd.DataFrame({'div_breadth':F['div_breadth']<-0.25,'top2_up':F['top2_chg120']>0.05,'froth':F['turn_z']>1.8,'vol_up':F['vol20_ratio']>1.3,'fx_weak':F['fx60']>0.03,'stretch':F['ext200']>0.25})
score=cond.sum(1)
fwd_min=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
f126=px.shift(-126)/px-1
dfc=pd.DataFrame({'score':score,'mdd126':fwd_min,'f126':f126})[athish].dropna()
print("\nOn near-1y-high days: forward 126d max drawdown & return by warning score")
print(dfc.groupby('score').agg(n=('f126','size'),mean_f126=('f126','mean'),mean_mdd126=('mdd126','mean'),p_dd20=('mdd126',lambda x:(x<-0.2).mean())).round(3).to_string())
score.to_frame('score').join(cond).to_parquet(S+'/work/warn_score.parquet')
print("\nScore path 2026:"); s26=score['2026-03-01':'2026-07-15']; print(s26[s26.diff()!=0].to_string())
