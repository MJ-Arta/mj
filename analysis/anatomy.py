import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
close=pd.read_parquet(S+'/work/close.parquet'); mcap=pd.read_parquet(S+'/work/mcap.parquet')
B={'반도체 빅2':['005930','000660'],'반도체 소부장(코스피)':['042700','007660','009150','011070'],
 '방산':['012450','079550','064350','047810','272210','103140'],'조선':['329180','042660','010140','009540','010620','443060'],
 '전력기기·전선':['267260','010120','298040','001440','006260','062040','000500'],'원전':['034020','052690','000720'],
 '증권':['039490','006800','071050','005940','016360'],'지주사':['034730','000880','003550','028260','267250','000150','402340'],
 '은행':['105560','055550','086790'],'2차전지':['373220','006400','005490'],'바이오':['207940','068270'],
 '자동차':['005380','000270'],'인터넷·게임':['035420','035720','259960']}
P=[('P0 약세장','2024-07-11','2025-04-09'),('P1 정책·대선','2025-04-09','2025-06-20'),('P2 상법·관세타결','2025-06-20','2025-10-27'),
   ('P3 반도체 본격화','2025-10-27','2026-02-25'),('P4 이란전쟁 급락·회복','2026-02-25','2026-04-15'),('P5 레버리지 과열','2026-04-15','2026-06-22'),('P6 붕괴','2026-06-22','2026-10-29')]
k=kospi()['Close']
def px(d): return close.loc[:pd.Timestamp(d)].iloc[-1]
rows=[]
for nm,a,b in P:
    r={'phase':nm,'from':a,'to':b,'KOSPI%':(k.loc[:b].iloc[-1]/k.loc[:a].iloc[-1]-1)*100}
    ca,cb=px(a),px(b)
    for bn,codes in B.items():
        c=[x for x in codes if x in close.columns and not np.isnan(ca.get(x,np.nan)) and not np.isnan(cb.get(x,np.nan))]
        r[bn]=((cb[c]/ca[c]-1).mean()*100) if c else np.nan
    ma=mcap.loc[:pd.Timestamp(a)].iloc[-1]; mb=mcap.loc[:pd.Timestamp(b)].iloc[-1]
    d_tot=mb.sum()-ma.sum(); d_big2=(mb[['005930','000660']].sum()-ma[['005930','000660']].sum())
    r['빅2 기여%']=d_big2/d_tot*100 if d_tot!=0 else np.nan
    r['빅2 비중(끝)']=mb[['005930','000660']].sum()/mb.sum()*100
    rows.append(r)
t=pd.DataFrame(rows).set_index('phase')
with pd.option_context('display.float_format','{:.0f}'.format,'display.width',300,'display.max_columns',30): print(t.T.to_string())
t.to_csv(S+'/work/anatomy_2025.csv')
# full-cycle
a,b='2025-04-09','2026-06-22'; ca,cb=px(a),px(b)
print("\nFull upcycle 2025-04-09 -> 2026-06-22, basket EW returns:")
for bn,codes in B.items():
    c=[x for x in codes if x in close.columns and not np.isnan(ca.get(x,np.nan)) and not np.isnan(cb.get(x,np.nan))]
    print(f"  {bn}: {((cb[c]/ca[c]-1).mean()*100):.0f}%  members={len(c)}")
ma=mcap.loc[:pd.Timestamp(a)].iloc[-1]; mb=mcap.loc[:pd.Timestamp(b)].iloc[-1]
print("Big2 share of KOSPI mcap increase over full upcycle: %.1f%%"%((mb[['005930','000660']].sum()-ma[['005930','000660']].sum())/(mb.sum()-ma.sum())*100))
print("Samsung %.0f%%, Hynix %.0f%%"%((cb['005930']/ca['005930']-1)*100,(cb['000660']/ca['000660']-1)*100))
# median stock
uni=ma.dropna().index; r=(cb[uni]/ca[uni]-1).dropna()
print("Median KOSPI stock: %.0f%%, share of stocks beating KOSPI(+297%%): %.1f%%, share negative: %.1f%%"%(r.median()*100,(r>2.97).mean()*100,(r<0).mean()*100))
