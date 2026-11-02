# Build KOSPI common-stock panel + daily breadth/concentration metrics (1995-2026)
import pandas as pd, numpy as np, glob, sys, os
SRC=sys.argv[1]; OUT=sys.argv[2]
cols=['Date','Code','Name','Close','ChangesRatio','Amount','Marcap','Market']
dfs=[pd.read_parquet(f,columns=cols) for f in sorted(glob.glob(SRC+'/marcap-*.parquet'))]
df=pd.concat(dfs,ignore_index=True); del dfs
df['Date']=pd.to_datetime(df['Date'])
print('all rows',len(df), df.Date.min(), df.Date.max(), df.Market.unique()[:10])
k=df[(df.Market=='KOSPI') & df.Code.str.endswith('0') & (df.Close>0)].copy()
k=k.drop_duplicates(['Date','Code'])
print('kospi common rows',len(k))
# latest name per code
names=k.sort_values('Date').groupby('Code')['Name'].last()
names.to_csv(OUT+'/names.csv')
close=k.pivot(index='Date',columns='Code',values='Close').astype('float32')
mcap=k.pivot(index='Date',columns='Code',values='Marcap').astype('float64')
chg=k.pivot(index='Date',columns='Code',values='ChangesRatio').astype('float32')
amt=k.pivot(index='Date',columns='Code',values='Amount').astype('float64')
close.to_parquet(OUT+'/close.parquet'); mcap.to_parquet(OUT+'/mcap.parquet')
# breadth
up=(chg>0).sum(1); dn=(chg<0).sum(1)
ma50=close.rolling(50,min_periods=50).mean(); ma200=close.rolling(200,min_periods=200).mean()
valid200=ma200.notna()&close.notna()
pct200=((close>ma200)&valid200).sum(1)/valid200.sum(1)
valid50=ma50.notna()&close.notna()
pct50=((close>ma50)&valid50).sum(1)/valid50.sum(1)
hi252=close.rolling(252,min_periods=252).max(); lo252=close.rolling(252,min_periods=252).min()
v252=hi252.notna()&close.notna()
nh=((close>=hi252)&v252).sum(1)/v252.sum(1); nl=((close<=lo252)&v252).sum(1)/v252.sum(1)
tot=mcap.sum(1)
top2=(mcap.get('005930',0).fillna(0)+mcap.get('000660',0).fillna(0))/tot
srt=np.sort(np.nan_to_num(mcap.values),axis=1)[:,::-1]
top10=srt[:,:10].sum(1)/tot.values
turn=amt.sum(1)/tot
b=pd.DataFrame({'adv':up/(up+dn),'n_up':up,'n_dn':dn,'pct50':pct50,'pct200':pct200,'nh52':nh,'nl52':nl,
                'top2':top2,'top10':top10,'turnover':turn,'mcap_total':tot,'n':close.notna().sum(1)})
b.to_parquet(OUT+'/breadth.parquet')
print(b.describe().T[['mean','min','max']])
print(b.tail(3))
