# 코스피 신호등 (매일 갱신)

보고서 v4의 판별 구조를 매 거래일 같은 방식으로 계산해 대시보드에 보여줍니다.

- **대시보드:** https://claude.ai/artifact/Rtp2LiRW9TxiKbse1Bfuxt (비공개, 소유자만 열람)
- **계산:** `daily_signal.py <작업폴더> <작업폴더>/signal.json`
  - 같은 폴더에 `status.json`(오늘 상태 1행), `history.json`(최근 260거래일), `trades.json`(FX 거래 기록)을 씁니다.
- **페이지 원본:** `dashboard_index.html`. 대시보드 저장소의 `files/index.html` 문서와 같은 내용입니다.
- **갱신:** 예약 작업이 화~토 07:17 KST에 실행됩니다.
  1. 위 스크립트를 실행합니다.
  2. 세 JSON 파일을 대시보드 자산으로 올리고 `datasets/status|history|trades` 문서의 `source.url`을 바꿉니다.
  3. 상태가 바뀌면 휴대폰으로 알립니다.

## 데이터 출처

- **코스피 지수:** FinanceData/fdr_krx_data_cache `data/index/year_ks11/<연도>.csv`
- **전 종목 일별 데이터:** FinanceData/marcap `data/marcap-<연도>.parquet`
  - 시장 폭 계산에 씁니다. 수정주가는 거래소 등락률로 만듭니다.
- **원/달러:** 과거 값은 datasets/exchange-rates(FRED, 약 1주 지연), 최근 값은 suchoforchat-creator/krx-feed의 일별 파일(야후 KRW=X)입니다.
- **외국인 수급(참고용):** james-brand/korea-market-data(CC BY 4.0)

## 규칙 (보고서 v4와 동일)

- **관찰 구간:** 최근 126거래일 안에 1년 고점 대비 −20% 이하였거나, 200일선 위 종목 비율이 20% 미만이었던 경우입니다.
- **FX 50%:**
  - 진입: 관찰 구간이고, 전일 원/달러 ≤ 126일 최고치 × 0.95이고, 종가가 50일선 위일 때입니다.
  - 청산: 200일선을 회복하기 전에는 진입가 × 0.90, 회복한 뒤에는 200일선 × 0.97 아래로 내려갈 때입니다.
- **본진입 100%:** 아래 두 조건이 모두 켜져 있을 때입니다.
  - 추세: 200일선 위에서 켜지고, 200일선 × 0.97 아래에서 꺼집니다.
  - 시장 폭: 60% 이상에서 켜지고, 40% 이하에서 꺼집니다.
- **과열 경고:** 원래 6개 지표 중 거래대금 과열을 뺀 5개입니다(데이터 크기 때문). 3개 이상이면 레버리지를 쓰지 않습니다(탐색 단계).
