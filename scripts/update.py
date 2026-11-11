"""매일 실행: 주가를 받아 지표를 계산하고 docs/index.html 대시보드를 새로 만든다.

사용법:  python scripts/update.py
"""
import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
EPISODE_MIN = 0.20  # 20% 이상 하락 구간만 기록


def fetch_daily(symbol):
    """분할 반영(배당 미반영) 일별 종가 [(date_str, close), ...]."""
    import yfinance as yf
    for attempt in range(3):
        try:
            df = yf.Ticker(symbol).history(period="max", interval="1d", auto_adjust=False, actions=False)
            if df is not None and len(df):
                out = []
                for idx, row in df.iterrows():
                    c = row.get("Close")
                    if c is not None and c == c and c > 0:
                        out.append((idx.strftime("%Y-%m-%d"), float(c)))
                if out:
                    return out
        except Exception as e:  # 네트워크 일시 오류 대비 재시도
            print(f"  {symbol} retry {attempt + 1}: {e}", file=sys.stderr)
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{symbol}: 데이터를 받지 못했습니다")


def r4(x):
    return float(f"{x:.4g}")


def compute(symbol, name, daily):
    """daily: [(YYYY-MM-DD, close), ...] -> (stats dict, monthly points)."""
    pk, pk_d = daily[0][1], daily[0][0]
    tr, tr_d = pk, pk_d
    in_dd = False
    eps = []
    for d, p in daily:
        if p >= pk:
            if in_dd and 1 - tr / pk >= EPISODE_MIN:
                eps.append([pk_d, tr_d, r4(-(1 - tr / pk) * 100), d])
            pk, pk_d, tr, tr_d, in_dd = p, d, p, d, False
        else:
            in_dd = True
            if p < tr:
                tr, tr_d = p, d
    last_d, last = daily[-1]
    if in_dd and 1 - tr / pk >= EPISODE_MIN:
        eps.append([pk_d, tr_d, r4(-(1 - tr / pk) * 100), None])

    last_dt = datetime.strptime(last_d, "%Y-%m-%d")
    cutoff = last_dt.replace(year=last_dt.year - 1).strftime("%Y-%m-%d")
    h52 = max(p for d, p in daily if d > cutoff)

    month_last = {}
    for d, p in daily:
        month_last[d[:7]] = p
    monthly = []
    for k, v in month_last.items():
        y, m = int(k[:4]), int(k[5:7])
        monthly.append([round(y + (m - 0.5) / 12, 4), r4(v)])

    stats = {
        "s": symbol, "n": name, "ath": r4(pk), "athD": pk_d,
        "last": r4(last), "lastD": last_d, "dd": r4(-(1 - last / pk) * 100),
        "h52": r4(h52), "eps": eps,
    }
    return stats, monthly


def render(stats, monthly, names):
    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    asof = max(s["lastD"] for s in stats if not s["s"].endswith((".KS", ".KQ")))
    meta = {"asof": asof, "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "names": names}
    html = (tpl.replace("__STATS__", json.dumps(stats, ensure_ascii=False, separators=(",", ":")))
               .replace("__MONTHLY__", json.dumps(monthly, separators=(",", ":")))
               .replace("__META__", json.dumps(meta, ensure_ascii=False)))
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out, asof


def main():
    names = json.loads((ROOT / "tickers.json").read_text(encoding="utf-8"))["tickers"]
    stats, monthly, failed = [], {}, []
    for sym, name in names.items():
        try:
            daily = fetch_daily(sym)
            s, m = compute(sym, name, daily)
            stats.append(s)
            monthly[sym] = m
            print(f"{sym:10} {len(daily):6d}일  현재 {s['last']}  전고점 대비 {s['dd']}%")
        except Exception as e:
            failed.append(sym)
            print(f"{sym}: 실패 - {e}", file=sys.stderr)
    if len(stats) < len(names) * 0.8:
        sys.exit(f"너무 많은 종목이 실패했습니다: {failed}")
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    out, asof = render(stats, monthly, names)
    print(f"완료: {out} (기준일 {asof}), 실패: {failed or '없음'}")


if __name__ == "__main__":
    main()
