#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLFERS24 の店舗データを公式の店舗一覧から取る。

一覧ページに「店名 → 〒 → 住所」が並ぶだけの単純な作り。
営業時間・個室の有無は一覧に無いので取らない（ブランド共通の説明文から
推測して各店に書くと、実際と違う店が出る）。
"""
import json
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://www.golfers24.jp/store"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


def main() -> None:
    html = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, URL],
                          capture_output=True, text=True).stdout
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    ls = [x for x in (re.sub(r"[ \t　]+", " ", v).strip()
                      for v in re.sub(r"<[^>]+>", "\n", t).split("\n")) if x]

    today, out = date.today().isoformat(), []
    for i, v in enumerate(ls):
        if not re.fullmatch(r"〒\d{3}-?\d{4}", v) or i == 0:
            continue
        name = ls[i - 1]
        # ⚠️ 一覧の下に運営会社の住所が同じ形で載っている。店舗ではないので除く。
        if not name.endswith("店"):
            continue
        addr = (ls[i + 1] if i + 1 < len(ls) else "").replace("&nbsp;", "").strip()
        if not re.search(f"^({PREF})", addr):
            continue
        m = re.search(f"({PREF})", addr)
        out.append({
            "brand": "GOLFERS24", "brand_slug": "golfers24",
            "name": name, "zip": v.lstrip("〒"), "address": addr,
            "pref": m.group(1), "source_url": URL, "fetched_at": today,
        })

    res = list({(x["name"], x["address"]): x for x in out}.values())
    (ROOT / "data" / "brand-golfers24.json").write_text(
        json.dumps({"brand": "GOLFERS24", "source_url": URL, "fetched_at": today,
                    "count": len(res), "stores": res}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    from collections import Counter
    print(f"GOLFERS24: {len(res)}店舗  {Counter(x['pref'] for x in res).most_common()}")
    for x in res[:4]:
        print("   ", x["name"], "|", x["address"])


main()
