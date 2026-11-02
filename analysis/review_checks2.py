"""Stop-loss rule vs random entries from the same precondition pool; list warning-score episodes."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
rng=np.random.default_rng(11)
k=kospi(); px=k['Close']; b=breadth().reindex(px.index)
ma=px.rolling(200).mean(); hi=px.rolling(252,min_periods=120).max()
deep=(px/hi-1).rolling(126,min_periods=1).min()<=-0.20
P=px.values; M=ma.values; n=len(P)
# precompute exit index for every day (first later close < 0.97*MA200)
below=np.where(P<0.97*M)[0]
def trade(i):
    j=below[np.searchsorted(below,i+1)] if np.searchsorted(below,i+1)<len(below) else n-1
    return P[j]/P[i]-1, j==n-1
T=pd.read_csv(S+'/work/stoploss_trades.csv')
for nm,pool in [('B',deep&(px>=ma)),('C',(b['pct200'].rolling(126,min_periods=1).min()<0.20)&(px>=0.97*ma))]:
    t=T[T.sig==nm]; ev_sig=t.ret.mean(); m=len(t)
    idx=np.where(pool.fillna(False).values & (np.arange(n)<n-260))[0]
    sims=[]
    for _ in range(3000):
        chosen=[]
        for j in rng.permutation(idx):
            if all(abs(j-c)>126 for c in chosen): chosen.append(j)
            if len(chosen)==m: break
        sims.append(np.mean([trade(c)[0] for c in chosen]))
    sims=np.array(sims)
    print(f"{nm}: signal EV/trade {ev_sig:.3f} (n={m}); random entries same pool & exit: mean {sims.mean():.3f}, 90th pct {np.percentile(sims,90):.3f}, P(random>=signal)={np.mean(sims>=ev_sig):.2f}")
ws=pd.read_parquet(S+'/work/warn_score.parquet')['score'].reindex(px.index)
near=px>=0.97*px.rolling(252,min_periods=200).max()
fmin=px[::-1].rolling(126,min_periods=1).min()[::-1].shift(-1)/px-1
D=pd.DataFrame({'s':ws,'dd':fmin})[near].dropna(); D['ep']=(D.index.to_series().diff().dt.days>90).cumsum()
E=D.groupby('ep').agg(start=('s',lambda x:x.index.min().date()),end=('s',lambda x:x.index.max().date()),maxscore=('s','max'),worst=('dd','min'))
print(E.to_string())
E.to_csv(S+'/work/warn_episodes.csv')
