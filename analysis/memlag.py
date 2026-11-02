import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
close=pd.read_parquet(S+'/work/close.parquet'); mcap=pd.read_parquet(S+'/work/mcap.parquet')
k=kospi()['Close']
for code,nm in [('000660','SK하이닉스'),('005930','삼성전자')]:
    c=close[code].dropna()
    for a,b in [('2015-06-01','2016-12-31'),('2018-06-01','2019-12-31'),('2022-01-01','2023-12-31'),('2024-06-01','2025-08-31')]:
        w=c[a:b]; print(nm,a[:4],'trough',w.idxmin().date(),int(w.min()))
    for a,b in [('2017-01-01','2018-12-31'),('2020-06-01','2021-12-31'),('2024-01-01','2024-12-31'),('2026-01-01','2026-10-29')]:
        w=c[a:b]; print(nm,a[:4],'peak',w.idxmax().date(),int(w.max()))
# big2 relative strength vs rest of KOSPI (cap-weighted)
m=mcap['2024-06-01':]; big=m[['005930','000660']].sum(1); rest=m.sum(1)-big
rs=(big/big.iloc[0])/(rest/rest.iloc[0])
for d in ['2025-04-09','2025-05-30','2025-06-30','2025-07-31','2025-08-29','2025-09-30','2025-10-31','2025-11-28','2025-12-30','2026-01-30','2026-02-27','2026-03-31','2026-04-30','2026-05-29','2026-06-22','2026-07-31','2026-08-31','2026-09-30','2026-10-29']:
    print(d, 'RS big2/rest=%.2f'%rs.loc[:d].iloc[-1], ' KOSPI=%.0f'%k.loc[:d].iloc[-1])
rs.to_frame('rs').to_parquet(S+'/work/rs_big2.parquet')
