# 전고점 대비 낙폭 모니터

미국 시가총액 상위 30종목 + 한화솔루션의 장기 주가, 변동성, 전고점 대비 낙폭을 매일 자동으로 갱신하는 대시보드입니다.

- 대시보드: GitHub Pages 주소 (Settings → Pages에서 확인)
- 갱신: 매주 화~토 한국시간 오전 7:17 (`.github/workflows/daily.yml`)
- 수동 갱신: Actions 탭 → "매일 대시보드 갱신" → Run workflow
- 종목 바꾸기: `tickers.json` 수정
- 데이터: Yahoo Finance (yfinance), 분할 반영·배당 미반영 종가

참고용이며 투자 권유가 아닙니다.
