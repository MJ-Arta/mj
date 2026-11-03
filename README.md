# 코스피 사이클 포착 연구

2025-04-09(2,293.70)부터 2026-06-22(9,114.55)까지 오른 코스피 사이클을 분해했습니다. 그리고 1995년 이후 31년치 데이터로 "다음 사이클을 미리 포착하는 신호"를 검증한 작업입니다.

- 보고서: [`report/index.html`](report/index.html)(차트 포함). 게시본은 claude.ai 아티팩트로 공개되어 있습니다.
- 기준일: 2026-10-30 종가(5,730.74). 작성일: 2026-11-02.

## 핵심 결과 (v4, 판별 로직 사전등록 비교)

후보 10개와 판정 규칙은 `research/prereg_logic_compare.md`에 결과를 보기 전에 커밋했습니다(3d18771).

| # | 결론 | 수준 |
|---|---|---|
| 1 | 2025-04-09 → 2026-06-22 코스피 +297%. 시총 증가분의 69%가 삼성전자·SK하이닉스, 종목 중간값 +10%. | 도출 |
| 2 | **진입 판별 최선: 원화 강세 전환(FX).** 관찰 구간에서 원/달러가 6개월 최고치보다 5% 이상 낮고 지수가 50일선 위. 1년 평균 +34.6% vs 기준선 +19.3%(p=0.002, 보정 후 0.018). 대세상승 7/7 포착, 바닥 대비 +23%에서 켜짐. 기준값 72개 중 75%에서 유의. 성공률 우위는 약함(p=0.14). 2026-09-07 신호는 실패 중. | 도출(인정 기준 일부 미달) |
| 3 | **보유·현금 최선: 추세∧시장 폭**(200일선 3% 이력 + 200일선 위 종목 비율 60/40). 연복리 7.7% vs 6.4%, 최대 낙폭 −33% vs −72%, 약세 구간 −5% vs −39%. 앞·뒤 기간 모두 계속 보유보다 우위. 대세상승 첫 1년 포착률 42%. | 도출(사전등록 기준 통과) |
| 4 | 결합(추세∧시장 폭 100% + FX만 켜지면 50%)은 수익/낙폭 0.243으로 최고, 포착률 50%. | 탐색(사후) |
| 5 | B(200일선 회복), A, SEMI, 연준 필터, 원화 추세 상시 보유는 기준선 이하. C·GC는 보정 후 유의하지 않음. | 기각 |
| 6 | 가격 모멘텀으로 수혜주 고르기는 무효(순위상관 0.02). | 기각 |
| 7 | 하이닉스 주가는 D램 수출단가보다 1~4개월 선행. | 도출 |
| 8 | 2026-11-03 현재 모든 규칙이 현금. 다음 트리거는 지수가 50일선(약 6,515) 위로 마감하는 것(FX 50%). | 판독 |

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
  logic_compare.py 사전등록한 판별 로직 10개 비교(진입 판별 + 보유·현금 전략)
  fx_checks.py     FX 신호 검증(기준값 72개, 환율 시차, 주가 반등과의 구별, 한 그룹씩 빼기)
  fx_strategy.py   FX 진입 전략과 2단계 청산(사후 탐색)
  final_combo.py   추세∧시장 폭 + FX 50% 결합(사후 탐색), 현재 트리거 수준
  capture_prereg.py 사전등록 전략의 대세상승 포착률(로그 기준)
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
