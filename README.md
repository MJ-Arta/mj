# 코스피 사이클 포착 연구

2025-04-09(2,293.70)부터 2026-06-22(9,114.55)까지 오른 코스피 사이클을 분해했습니다. 그리고 1995년 이후 31년치 데이터로 "다음 사이클을 미리 포착하는 신호"를 검증한 작업입니다.

- 보고서: [`report/index.html`](report/index.html)(차트 포함). 게시본은 claude.ai 아티팩트로 공개되어 있습니다.
- 기준일: 2026-10-30 종가(5,730.74). 작성일: 2026-11-02.

## 핵심 결과 (증거 수준 표시)

| # | 결론 | 수준 |
|---|---|---|
| 1 | 2025-04-09 → 2026-06-22 동안 코스피는 +297% 올랐습니다. 시총 증가분의 69%는 삼성전자·SK하이닉스가 차지했고, 종목 중간값은 +14%였습니다. | 도출 |
| 2 | 200일선 회복 신호(B)와 시장 폭 회복 신호(C)는 진짜 대세상승에서 바닥 대비 +12~40% 지점에 켜졌습니다. 그 뒤에도 상승폭의 50~85%가 남아 있었습니다. 1년 뒤 상승 비율은 64~67%로, 기준선 58%보다 높았습니다. | 도출 |
| 3 | 같은 신호의 약 1/3은 약세장 반등에서 나온 가짜였습니다. 가격 정보만으로는 둘을 구분할 수 없습니다. | 도출 |
| 4 | 가짜를 거르려면 '점화 조건'이 필요합니다. 이익 엔진의 제품 가격 전환과 전망치 상향, 유동성 전환, 구속력 있는 제도 변화입니다. | 가설 (장기 데이터 미확보로 백테스트 못 함) |
| 5 | 가격 모멘텀으로 수혜주를 고르는 방법은 코스피에서 무효였습니다. 60일 수익률 순위와 이후 1년 수익률 순위의 상관은 평균 0.004였고, 사이클 초입에서는 −0.04였습니다. | 기각 |
| 6 | SK하이닉스 주가 YoY는 D램 수출단가 YoY를 약 3개월 앞섰습니다(상관 0.91). 주가 바닥은 계약가 바닥보다 4~12개월 빨랐습니다. | 도출 (근사 데이터, 작은 표본) |
| 7 | 2026년 6월 천장은 이익이 아니라 포지션과 금리에서 경고가 나왔습니다. 외국인 매도 속 상승, 신용 한도 소진, 두 종목 55% 쏠림, 연준 인상 반영이 그 경고였습니다. | 검증(보도) + 도출 |

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
