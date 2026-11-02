"""Build report/index.html from template + analysis outputs.
usage: python3 -I build.py <work_dir>   (work_dir holds chartdata.json from analysis/export_data.py)"""
import json, sys, os
W=sys.argv[1]; here=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(W,'chartdata.json')))
# Korean semiconductor exports (MOTIE monthly release, as reported; None = not found in this research)
EXP=[("2023-01",6.0,-44.5),("2023-02",6.0,None),("2023-03",8.6,-34.5),("2023-04",6.4,None),("2023-05",7.4,None),("2023-06",8.9,None),
("2023-07",7.4,-33.6),("2023-08",8.6,None),("2023-09",9.9,None),("2023-10",8.97,-4.7),("2023-11",9.5,10.7),("2023-12",11.0,21.7),
("2024-01",9.41,56.2),("2024-02",9.96,66.7),("2024-03",11.67,35.7),("2024-04",None,56.1),("2024-05",11.38,54.5),("2024-06",13.42,50.9),
("2024-07",None,None),("2024-08",None,38.3),("2024-09",13.6,None),("2024-10",12.5,40.3),("2024-11",None,None),("2024-12",14.5,31.5),
("2025-01",10.1,8.1),("2025-02",9.6,-3.0),("2025-03",13.1,11.9),("2025-04",11.7,17.2),("2025-05",13.8,21.2),("2025-06",14.97,11.6),
("2025-07",14.71,31.6),("2025-08",15.1,27.1),("2025-09",16.6,None),("2025-10",15.7,None),("2025-11",17.3,None),("2025-12",20.8,43.2),
("2026-01",20.54,102.7),("2026-02",25.16,160.8),("2026-03",32.83,151.4),("2026-04",31.9,173.5),("2026-05",37.16,169.4),("2026-06",44.82,199.5),
("2026-07",41.01,178.8),("2026-08",46.65,209.0),("2026-09",60.3,262.8),("2026-10",56.44,259.4)]
EXP=[[m+"-01",v,y] for m,v,y in EXP]
LEAD=[["1998",-0.108],["2001",-0.093],["2003",-0.055],["2008",-0.125],["2016",0.157],["2020",-0.035],["2022 (실패)",-0.075],["2025",0.012]]
# heatmap (anatomy_2025.csv values, rounded)
cols=["P0 약세장<br>24.07→25.04","P1 정책·대선<br>→25.06","P2 상법·관세<br>→25.10","P3 반도체<br>→26.02","P4 전쟁<br>→26.04","P5 과열<br>→26.06","P6 붕괴<br>→26.10"]
rows=[("코스피",[-21,32,34,50,0,50,-35]),("반도체 빅2",[-36,34,90,95,8,112,-41]),("반도체 소부장",[-51,40,71,50,27,114,-42]),("방산",[66,102,-1,30,17,-20,-36]),
("조선",[49,52,42,-6,-10,6,-43]),("전력기기·전선",[-27,84,50,58,-1,35,-42]),("원전",[-8,144,9,68,7,-25,-30]),("증권",[-7,89,26,82,-2,-17,-29]),
("지주사",[-12,90,40,53,-5,54,-32]),("은행",[-16,46,15,40,-3,-1,-3]),("2차전지",[-36,2,49,22,-2,1,-9]),("바이오",[2,4,14,40,-12,-18,9]),
("자동차",[-34,18,19,98,-17,7,-39]),("인터넷·게임",[4,44,-12,-4,-13,-9,-20])]
h=['<table class="heat"><thead><tr><th>바스켓</th>'+''.join(f'<th class="n ph">{c}</th>' for c in cols)+'</tr></thead><tbody>']
for name,vals in rows:
    tds=''.join(f'<td class="h {"pos" if v>0 else "neg"}" style="--v:{min(abs(v)/100,1):.2f}">{"+" if v>0 else ""}{v}%</td>' for v in vals)
    h.append(f'<tr><td class="nowrap"><b>{name}</b></td>{tds}</tr>' if name=="코스피" else f'<tr><td class="nowrap">{name}</td>{tds}</tr>')
h.append('<tr><td class="nowrap">빅2 시총 비중(국면 끝)</td>'+''.join(f'<td class="n">{v}%</td>' for v in [24,22,31,40,42,57,52])+'</tr></tbody></table>')
t=open(os.path.join(here,'template.html')).read()
t=t.replace('__DATA__',json.dumps(D,ensure_ascii=False,separators=(',',':'))).replace('__EXPORTS__',json.dumps(EXP)).replace('__LEAD__',json.dumps(LEAD,ensure_ascii=False)).replace('__HEATMAP__','\n'.join(h))
open(os.path.join(here,'index.html'),'w').write(t); print('wrote',len(t),'bytes')
