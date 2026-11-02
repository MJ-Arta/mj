# 코스피 사이클 포착 연구

2025-04-09(2,293.70)부터 2026-06-22(9,114.55)까지 오른 코스피 사이클을 분해했습니다. 그리고 1995년 이후 31년치 데이터로 "다음 사이클을 미리 포착하는 신호"를 검증한 작업입니다.

- 보고서: [`report/index.html`](report/index.html)(차트 포함). 게시본은 claude.ai 아티팩트로 공개되어 있습니다.
- 기준일: 2026-10-30 종가(5,730.74). 작성일: 2026-11-02.

## 핵심 결과 (v3, 독립 검토 반영)

| # | 결론 | 수준 |
|---|---|---|
| 1 | 2025-04-09 → 2026-06-22 코스피 +297%. 시총 증가분의 69%가 삼성전자·SK하이닉스, 종목 중간값 +10%(수정주가). | 도출 |
| 2 | 최근 6개월 안에 −20% 하락했던 날에 사면 1년 뒤 64.6% 상승, 평균 +19.1%(아무 날 59.5%, +11.7%). | 도출 |
| 3 | 200일선 회복 신호(B)는 그 기준선보다 나은 정보가 없음(무작위 대비 우연 확률 21%, 1998·2025 제외 시 +5.9%). | 기각 |
| 4 | 시장 폭 회복 신호(C)는 기준선보다 나을 가능성(1년 평균 +40.3% vs +22.3%, 손절 규칙 결합 시 +31.1% vs 무작위 +13.6%, p≈0.03, n=8). | 도출(약함) |
| 5 | 청산 규칙(종가 < 200일선×0.97)은 손실을 평균 −6~−9%로 제한. 효과는 진입이 아니라 청산에서 나옴. | 도출(탐색) |
| 6 | 유동성 조건은 기준율 77%라 변별력 없음. 2층은 '이익 엔진 가격의 새 전환' 하나로 줄이고, 진입 허가가 아니라 비중 조절로 사용. 사전등록 검증 필요. | 가설 |
| 7 | 가격 모멘텀으로 수혜주 고르기는 무효(순위상관 0.02). 바닥 6개월 뒤 52주 신고가 근처 종목은 8번 중 7번 우위(약한 증거). | 기각 / 약한 도출 |
| 8 | 하이닉스 주가는 D램 수출단가보다 1~4개월 선행(YoY 상관 0.91, 독립 표본 약 5개. 월간 변화율 0.39). | 도출 |
| 9 | 2026년 천장의 경고는 이익이 아니라 포지션과 금리에서 나왔음. 경고 점수 3 이상 국면 4/4가 −20% 하락으로 이어짐(탐색, 시점은 못 맞힘). | 검증(보도) + 탐색 |

## 구성

```
analysis/        분석 스크립트 (python3 -I 로 실행)
  common.py        데이터 로더, 20% 반전 기준 사이클 탐지
  build_panel.py   전 종목 패널과 일별 시장 폭·쏠림 지표 생성
  cycles.py        사이클 표
  signals.py       확인 신호 A~D 백테스트
  leaders.py       '먼저 오른 종목' 지속성 검정 (모멘텀, 귀무분포 포함)
  leaders2.py      52주 신고가 주도주 검정
  anatomy.py       2025–26 국면 × 업종 바스켓 수익률
  tops.py          과거 천장의 과열 지표와 경고 점수
  memlag.py        메모리 주가 바닥·정점, 빅2 상대강도
  asp.py           D램 수출단가 vs 하이닉스 리드-래그
  verify.py        보도 수치와 거래소 종가 대조
  robustness.py    신호 기준값 민감도, D램 단가 리드-래그 세부
  review_checks.py 독립 검토 대응: 공정 기준선, 무작위 추출, 기계적 사이클 정의, 청산 규칙, 연준 기준율, 메모리 대조, 경고 점수 국면
  review_checks2.py 청산 규칙 vs 무작위 진입, 경고 점수 국면 목록
  export_data.py   보고서 차트 데이터 출력
results/         결과 표 (CSV)
report/          template.html + build.py → index.html
research/        조사 메모와 출처 목록
```

## 재현 방법

데이터는 저장소에 넣지 않았습니다(약 550MB). `_data/ext/` 아래에 받습니다.

1. 지수: `github.com/FinanceData/fdr_krx_data_cache`(브랜치 master)의 `data/index/year_ks11/*.csv` → `_data/ext/fdrcache/data/index/year_ks11/`
2. 전 종목: `github.com/FinanceData/marcap`(master)의 `data/marcap-YYYY.parquet` → `_data/ext/marcapdata/`
3. 업종 분류: fdr_krx_data_cache의 `data/listing/desc/<최신일>.csv`. `leaders.py`의 경로를 그 파일로 맞추세요.
4. 환율: `github.com/datasets/exchange-rates`의 `data/daily.csv` → `_data/ext/macro/datasets_exchange-rates_main_data_daily.csv`
5. 실행 순서:

   ```bash
   python3 -I analysis/build_panel.py _data/ext/marcapdata _data/work
   python3 -I analysis/cycles.py
   python3 -I analysis/signals.py
   python3 -I analysis/leaders.py
   python3 -I analysis/tops.py
   python3 -I analysis/export_data.py
   python3 -I report/build.py _data/work
   ```

`KOSPI_ROOT` 환경변수로 `_data` 위치를 바꿀 수 있습니다. pandas, numpy, scipy, pyarrow가 필요합니다.

## 한계

- 원자료(marcap) 종가는 액면분할·무상증자 미반영입니다. `build_panel.py`는 거래소 발표 등락률(ChangesRatio)을 이어 붙여 수정주가를 만듭니다(v2). 배당과 인적분할은 반영하지 않았습니다.

- 작업 환경에서 한국은행 ECOS, KOSIS, FRED, KRX, 네이버 접속이 막혀 있었습니다. 그래서 장기 품목별 수출, PBR, 이익 전망 수정 시계열이 없고, '점화 조건'은 백테스트하지 못했습니다.
- 2023–26년 반도체 수출과 D램 가격 수치는 검색 요약에서 수집했으므로 원문 대조가 필요합니다.
- 대세상승 표본은 7번입니다. 모든 비율은 기술 통계입니다.
- 업종 분류는 현재 상장사 기준이고, 테마 바스켓은 사후에 골랐습니다.
- 투자 권유가 아닙니다.

## 데이터 출처와 라이선스

- FinanceData/fdr_krx_data_cache, FinanceData/marcap(한국거래소 원자료)
- james-brand/korea-market-data(KRX 업종지수·외국인 수급, CC BY 4.0, "K-Export Stars (kexportstars.com)")
- datasets/exchange-rates(FRED 원자료)
- SJS9401/market-dashboard `data/asp_dram.json`(증권사 차트를 수치화한 근사치)
