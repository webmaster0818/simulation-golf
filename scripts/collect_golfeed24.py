#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLFEED24 の店舗データを各店舗ページの「店舗情報」表から取る。

店舗ページに 住所／アクセス方法／営業時間／定休日／打席数／駐車場 が揃っている。
一覧ページから店舗ページのURLを拾い、2秒間隔で1件ずつ取得する。

⚠️ 表に無い項目は None のまま。埋めない。
"""
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = "https://golfeed24.com/store"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")
LABELS = ["住所", "アクセス方法", "営業時間", "定休日", "打席数", "駐車場"]
KEY = {"住所": "address", "アクセス方法": "access", "営業時間": "hours",
       "定休日": "closed", "打席数": "bays", "駐車場": "parking"}


def get(url: str) -> str:
    return subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                          capture_output=True, text=True).stdout


def lines_of(html: str) -> list:
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", "\n", t)
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip() for v in t.split("\n")) if x]


def name_of(heading: str) -> str:
    m = re.search(r"(ゴルフィード24\s*\S+?店)", heading)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else heading.strip()


def main() -> None:
    idx = get(LIST)
    urls = sorted({re.sub(r"/?$", "/", u) for u in
                   re.findall(r"https://golfeed24\.com/store/[a-z0-9\-]+/?", idx)})
    urls = [u for u in urls if u != "https://golfeed24.com/store/"]
    print(f"店舗ページ: {len(urls)}件")

    today, out, ng = date.today().isoformat(), [], []
    for n, u in enumerate(urls, 1):
        ls = lines_of(get(u))
        # 「店舗情報」以降にラベル→値の並びがある
        try:
            start = ls.index("店舗情報")
        except ValueError:
            ng.append(u); time.sleep(2); continue
        rec = {KEY[k]: None for k in LABELS}
        for i in range(start, len(ls)):
            if ls[i] in LABELS and i + 1 < len(ls) and ls[i + 1] not in LABELS:
                rec[KEY[ls[i]]] = ls[i + 1]
        addr = rec["address"] or ""
        zm = re.match(r"〒?\s*(\d{3}-?\d{4})\s*(.*)", addr)
        zipc, addr = (zm.group(1), zm.group(2).strip()) if zm else (None, addr)
        pm = re.search(f"({PREF})", addr)
        bm = re.search(r"(\d+)\s*打席", rec["bays"] or "")
        out.append({
            "brand": "GOLFEED24", "brand_slug": "golfeed24",
            # 見出しはSEO用の長い文言（「インドアゴルフ 赤穂｜ゴルフィード24 赤穂店【…】」）
            # なので、その中から店舗名だけを取り出す。
            "name": name_of(ls[start + 1] if start + 1 < len(ls) else u),
            "slug": u.rstrip("/").rsplit("/", 1)[-1],
            "zip": zipc, "address": addr, "pref": pm.group(1) if pm else None,
            **{k: rec[k] for k in ("access", "hours", "closed", "bays", "parking")},
            "bays_num": int(bm.group(1)) if bm else None,
            "open_24h": "24時間" in (rec["hours"] or ""),
            "private_room": "個室" in (rec["bays"] or ""),
            "source_url": u, "fetched_at": today,
        })
        if n % 5 == 0 or n == len(urls):
            print(f"  [{n}/{len(urls)}]", flush=True)
        time.sleep(2)

    (ROOT / "data" / "brand-golfeed24.json").write_text(
        json.dumps({"brand": "GOLFEED24", "source_url": LIST, "fetched_at": today,
                    "count": len(out), "stores": out, "failed": ng},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"GOLFEED24: {len(out)}店舗 / 取得失敗 {len(ng)}")
    for k in ("address", "pref", "hours", "closed", "bays", "parking", "access"):
        print(f"  {k}: {sum(1 for x in out if x.get(k))}/{len(out)}")
    for x in out[:3]:
        print("   ", x["name"], "|", x["pref"], "|", x["bays"], "|", x["hours"])


main()
