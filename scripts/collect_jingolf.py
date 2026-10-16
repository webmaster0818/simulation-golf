#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JIN-golf 品川ゴルフアカデミー（株式会社ジン-ゴルフ・マンツーマンのインドアゴルフスクール）を公式サイトから取る。

公式 https://jin-golf.com/ は WordPress。店舗は品川（青物横丁）の1か所だけ（トップ・/shop-info/ とも1店）。
  /shop-info/ … 所在地・TEL・営業時間・駅からの徒歩分・近隣コインパーキング・「打席は右打ちのみ」
  /faq/       … 「世界一正確なレザー弾道測定器のトラックマン…をご用意しております」→ 機材 TRACKMAN
  /plan/      … 月額のプラン表は本文に無い（体験料金 10,000円(11,000円税込) だけ）→ monthly_fee は null

⚠️ 代表が開業した「銀座カントリークラブ」（ginza-golf-cc.com・SDR の完全個室インドア）は別ブランドなのでここでは取らない。
⚠️ 打席数・定休日は公式に記載なし。店舗専用の駐車場の記載も無い（近隣コインパーキング3か所の案内のみ）。

  python3 scripts/collect_jingolf.py        # 取得して data/jingolf.json に書く
"""
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://jin-golf.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "JIN-golf", "jingolf"


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def main_text(h: str) -> str:
    h = re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", "", h, flags=re.S)
    m = re.search(r"<main[^>]*>(.*?)</main>", h, re.S)
    h = m.group(1) if m else h
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))).strip()


def main() -> None:
    today = date.today().isoformat()
    problems = []
    shop_url, faq_url = BASE + "/shop-info/", BASE + "/faq/"
    shop = main_text(get(shop_url)); time.sleep(2)
    faq = main_text(get(faq_url))
    if not shop or not faq:
        raise SystemExit("ページが取れなかった")

    # 所在地: 「所在地 〒140-0004 東京都品川区南品川3丁目5-3 青横ビル5階503号室 【TEL】…」
    m = re.search(r"所在地\s*〒\s*(\d{3})-?(\d{4})\s*(.+?)\s*【TEL】\s*([\d-]+)", shop)
    if not m:
        raise SystemExit("所在地が取れなかった")
    zipc, addr, tel = m.group(1) + m.group(2), m.group(3).strip(), m.group(4)
    pref = re.match(r"(東京都|.+?[道府県])", addr).group(1)

    mh = re.search(r"【営業時間】\s*([\d:：]+\s*[～〜~-]\s*[\d:：]+)", shop)
    hours = mh.group(1).replace("~", "〜").replace("～", "〜") if mh else None
    if not hours:
        problems.append("営業時間が取れなかった")

    # 電車でのアクセス: 「青物横丁駅（京浜急行電鉄）徒歩約1分 品川シーサイド駅（りんかい線）徒歩約9分 …」
    ma = re.search(r"電車でのアクセス\s*(.+?)\s*近隣コインパーキング", shop)
    access = None
    if ma:
        items = re.findall(r"(\S+駅（[^）]+）\s*徒歩約?\d+分)", ma.group(1))
        access = "／".join(re.sub(r"\s+", "", x) for x in items) or None
    if not access:
        problems.append("アクセスが取れなかった")

    # 駐車場: 店舗専用の記載は無く、近隣コインパーキングの案内だけ
    names = re.findall(r"(\S+)\s*営業時間[：:]", shop.split("近隣コインパーキング", 1)[-1])
    parking = ("近隣コインパーキングの案内あり（" + "・".join(names) + "）") if names else None

    eq = []
    if re.search(r"トラックマン|TRACKMAN|Trackman", faq):
        eq.append("TRACKMAN")
    if not eq:
        problems.append("機材（トラックマン）の記載が見つからない")

    # 打席数は記載なし。「※ 打席は右打ちのみとなります。」は打席数ではないので note に残す
    note = "打席は右打ちのみ（公式 /shop-info/）" if "打席は右打ちのみ" in shop else None

    store = {
        "brand": BRAND, "brand_slug": BRAND_SLUG,
        "slug": "shinagawa",
        "name": "JIN-golf 品川ゴルフアカデミー",
        "pref": pref,
        "zip": zipc,
        "address": addr,
        "access": access,
        "tel": tel,
        "hours": hours,
        "open_24h": False if hours else None,
        "closed": None,
        "bays": None, "bays_num": None,
        "private_room": None,
        "parking": parking,
        "monthly_fee": None,
        "equipment": "／".join(eq) if eq else None,
        "open": True,
        "note": note,
        "official": BASE + "/",
        "source_url": shop_url, "fetched_at": today,
    }
    print(json.dumps(store, ensure_ascii=False, indent=1))
    out = DATA / "jingolf.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": [store]},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し 1件 → {out}")
    for p in problems:
        print("  ⚠️", p)


if __name__ == "__main__":
    main()
