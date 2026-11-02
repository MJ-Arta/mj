import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
k=kospi()
chk={'2024-08-05':2441.55,'2025-04-09':2293.70,'2025-06-20':3021.84,'2025-10-27':4042.83,'2025-12-30':4214.17,'2026-01-27':5084.85,'2026-02-25':6083.86,'2026-03-03':5791.91,'2026-03-04':5093.54,'2026-04-15':6091.39,'2026-05-06':7384.56,'2026-05-26':8047.51,'2026-06-02':8801.49,'2026-06-08':7484.41,'2026-06-18':9063.84,'2026-06-19':9052.42,'2026-06-22':9114.55,'2026-06-23':None,'2026-06-29':8394.65,'2026-07-13':6806.0,'2026-07-28':6023.63,'2026-07-29':5663.24,'2026-07-31':6595.45,'2026-10-02':7003.74,'2026-10-13':6035.35,'2026-10-15':5554.22,'2026-10-26':5469.47,'2026-10-30':5730.74}
for d,v in chk.items():
    r=k.loc[d]; print(d, 'KRX close=%.2f chg=%+.2f%% high=%.2f low=%.2f'%(r.Close,r.Change*100,r.High,r.Low), ' agent=',v, 'OK' if v and abs(r.Close-v)<1 else '')
print('2026 intraday high max:', k.loc['2026','High'].max(), k.loc['2026','High'].idxmax().date())
print('post-peak intraday low:', k.loc['2026-06-22':,'Low'].min(), k.loc['2026-06-22':,'Low'].idxmin().date())
print('52w low (since 2025-11-01):', k.loc['2025-11-01':,'Low'].min(), k.loc['2025-11-01':,'Low'].idxmin().date())
print('2025-04 intraday low', k.loc['2025-04','Low'].min(), k.loc['2025-04','Low'].idxmin().date())
# circuit-breaker-sized days in 2026
d=k.loc['2025':]; big=d[abs(d.Change)>=0.08]; print(big[['Close','Change']])
