#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FiT24インドアゴルフ の店舗データを公式の店舗検索が読み込むデータから取る。

店舗検索がJavaScriptで動いており、HTMLには店舗が1件も出ない。
実体は https://www.fit24.jp/shop/data/shop.js に全店舗が入っている。

  biz = "fit24" … フィットネスジム（対象外）
        "indg"  … インドアゴルフ（対象）
        "gstd"  … ゴルフスタジオ（対象）
  combi = "1"   … 同じ建物にフィットネスジムが併設されている

⚠️ このファイルは JSON ではなく JavaScript。全角スペースが紛れているので
   そのまま json.loads できない。整えてから読む。
"""
import json
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://www.fit24.jp/shop/data/shop.js"
SITE = "https://www.fit24.jp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")
GOLF = {"indg": ("FiT24インドアゴルフ", "fit24-indoor-golf"),
        "gstd": ("FiT24ゴルフスタジオ", "fit24-golf-studio")}


def main() -> None:
    js = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, URL],
                        capture_output=True, text=True).stdout
    m = re.search(r"var stores\s*=\s*(\{[\s\S]*?\});", js)
    if not m:
        raise SystemExit("店舗データの位置が変わっている。取得を中止する。")
    body = m.group(1).replace("　", " ")          # 全角スペース
    body = re.sub(r",\s*([}\]])", r"\1", body)        # 末尾カンマ
    stores = json.loads(body)

    today, out = date.today().isoformat(), []
    for region, items in stores.items():
        for s in items:
            if s.get("biz") not in GOLF:
                continue
            addr = (s.get("address") or "").strip()
            pm = re.search(f"({PREF})", addr)
            out.append({
                "brand": GOLF[s["biz"]][0], "brand_slug": GOLF[s["biz"]][1],
                "slug": s.get("store_code") or f"fit24-{s['id']}",
                "name": s.get("store_name"), "address": addr,
                "pref": pm.group(1) if pm else None,
                "tel": s.get("tel") or None,
                # 公式が全店「24時間・年中無休」と明記しているブランド
                "hours": "24時間", "open_24h": True, "closed": "年中無休",
                # 同じ建物にフィットネスジムがあるか（FiT24だけの比較軸）
                "gym_attached": s.get("combi") == "1",
                "official": SITE + s["store_url"] if s.get("store_url") else None,
                "source_url": URL, "fetched_at": today,
            })

    res = list({x["slug"]: x for x in out}.values())
    (ROOT / "data" / "brand-fit24-indoor-golf.json").write_text(
        json.dumps({"brand": "FiT24インドアゴルフ", "source_url": URL, "fetched_at": today,
                    "count": len(res), "stores": res}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    from collections import Counter
    print(f"FiT24インドアゴルフ: {len(res)}店舗")
    print("  都道府県:", Counter(x["pref"] for x in res).most_common())
    print("  ジム併設:", sum(1 for x in res if x["gym_attached"]))
    miss = [x["name"] for x in res if not x["pref"] or not x["address"]]
    if miss:
        print(f"  ⚠️ 住所が取れない: {miss}")
    for x in res[:3]:
        print("   ", x["slug"], "|", x["name"], "|", x["address"])


main()
