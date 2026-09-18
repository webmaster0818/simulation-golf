#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""トップトレーサー導入施設を GDO の一覧から収集する。

■ なぜこの軸か
  シミュレーションゴルフは「どの計測機材が入っているか」で体験が変わる
  （計測できる項目・弾道の再現・コースデータ数）。しかし施設の公式サイトは
  機材名を前面に出していないことが多く、「トップトレーサー 店舗」のような
  機材名の検索に答えているサイトがほぼ無い。
  GDOは導入施設の一覧を公開しており、1施設ごとに
  住所・距離・打席数・トップトレーサー利用料金・公式URL まで揃う。

■ 取得元と敬意
  https://www.golfdigest.co.jp/ttr/rangelist/
  robots.txt は /keyword/ のみ Disallow（2026-09-12 実測）。2秒間隔で取得する。
  掲載時は施設ごとに出典URLと取得日を明記する。

■ 出力
  data/toptracer.json
"""
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.golfdigest.co.jp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SLEEP = 2.0


def get(url: str) -> str:
    r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                       capture_output=True, text=True)
    return r.stdout or ""


def text_of(html: str) -> str:
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def field(t: str, label: str, nxt: str) -> str | None:
    m = re.search(re.escape(label) + r"\s*(.+?)\s*" + re.escape(nxt), t)
    return m.group(1).strip() if m else None


def main() -> None:
    today = date.today().isoformat()
    idx = get(f"{BASE}/ttr/rangelist/")
    paths = sorted(set(re.findall(r"/ttr/rangelist/detail/[^\"']+\.html", idx)))
    print(f"施設ページ: {len(paths)}件")
    out, ng = [], []
    for i, p in enumerate(paths, 1):
        url = BASE + p
        h = get(url)
        if not h:
            ng.append(p); continue
        t = text_of(h)
        name = None
        m = re.search(r"練習場一覧\s+(.+?)\s+\1", t)
        if m:
            name = m.group(1)
        else:
            m = re.search(r"<title[^>]*>(.*?)\s*\|", h, re.S)
            name = re.sub(r"\s+", " ", m.group(1)).strip() if m else p
        rec = {
            "slug": p.rsplit("/", 1)[-1].replace(".html", ""),
            "name": name,
            "address": field(t, "住所", "電話番号"),
            "tel": field(t, "電話番号", "距離"),
            "distance": field(t, "距離", "トップトレーサー"),
            "ttr_fee": field(t, "トップトレーサー・レンジ 利用料金", "トップトレーサー"),
            "ttr_bays": field(t, "トップトレーサー・レンジ 打席数", "練習場ガイド"),
            "official": (re.search(r"公式サイト\s+(https?://\S+)", t) or [None, None])[1],
            "source_url": url,
            "fetched_at": today,
        }
        if rec["address"]:
            out.append(rec)
        else:
            ng.append(p)
        if i % 25 == 0 or i == len(paths):
            print(f"  [{i}/{len(paths)}] 取得 {len(out)} / 失敗 {len(ng)}", flush=True)
        time.sleep(SLEEP)

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "toptracer.json").write_text(json.dumps({
        "generated_at": today,
        "source": "GDO トップトレーサー・レンジ 練習場一覧",
        "source_url": f"{BASE}/ttr/rangelist/",
        "note": "掲載時は施設ごとに source_url と fetched_at を必ず併記する。",
        "count": len(out), "facilities": out, "failed": ng,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n保存: {len(out)}件 / 失敗 {len(ng)}件")


main()
