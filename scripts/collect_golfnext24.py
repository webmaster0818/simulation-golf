#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLF NEXT 24 の店舗データを公式の店舗一覧から取る。

一覧ページ1枚に全店舗の 住所・個室数・営業時間・駐車場 が載っているため、
店舗ページを1件ずつ叩く必要がない（相手のサーバに優しい）。

⚠️ 書いていない項目は埋めない。「駐車場 有（提携）」のような曖昧表記も
   そのまま残す。台数に丸めると事実から離れる。
"""
import json
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://golfnext24.jp/stores/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


def lines_of(html: str) -> list:
    """タグを落として空行を除いた行の並びにする。

    ⚠️ 住所は「〒300-0811」と「茨城県…」で改行されている店舗があるので、
       行に割ってから 住所〜Google MAP の間を連結して1つに戻す。
    """
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", "\n", t)
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip() for v in t.split("\n")) if x]


def zen2han(v: str) -> str:
    return v.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def field(ls: list, i: int, label: str, stop: tuple) -> str | None:
    """ls[i] 以降から label を探し、次の見出しが来るまでを値として返す。"""
    for j in range(i, min(i + 14, len(ls))):
        if ls[j] == label:
            vals = []
            for k in range(j + 1, len(ls)):
                if ls[k] in stop or ls[k] in LABELS:
                    break
                vals.append(ls[k])
            return "".join(vals) if label == "住所" else " ".join(vals)
    return None


LABELS = {"住所", "個室数", "営業時間", "駐車場", "店舗ページ", "Google MAP"}


def main() -> None:
    html = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, URL],
                          capture_output=True, text=True).stdout
    ls = lines_of(html)

    today, out = date.today().isoformat(), []
    for i, v in enumerate(ls):
        if v != "住所" or i == 0:
            continue
        name = ls[i - 1]
        addr = re.sub(r"\s+", "", field(ls, i, "住所", ("Google MAP",)) or "")
        zm = re.match(r"〒?(\d{3}-?\d{4})(.*)", addr)
        zipc, addr = (zm.group(1), zm.group(2)) if zm else (None, addr)
        pm = re.search(f"({PREF})", addr)
        rooms = field(ls, i, "個室数", ()) or ""
        hours = field(ls, i, "営業時間", ()) or ""
        rn = re.match(r"(\d+)", zen2han(rooms))
        out.append({
            "brand": "GOLF NEXT 24",
            "brand_slug": "golf-next-24",
            "name": re.sub(r"\s*（[^）]*）\s*$", "", name).strip(),
            "zip": zipc,
            "address": addr,
            "pref": pm.group(1) if pm else None,
            # このブランドは全店が完全個室。公式の項目名も「個室数」なので、
            # 打席数ではなく個室数として持つ（4打席ではなく4室）。
            "bays": f"個室{rooms}" if rooms else None,
            "bays_num": None,
            "private_room": True,
            "rooms": rooms,
            "rooms_num": int(rn.group(1)) if rn else None,
            "hours": hours,
            "open_24h": "24時間" in hours,
            "parking": field(ls, i, "駐車場", ()) or "",
            "source_url": URL,
            "fetched_at": today,
        })

    res = list({x["name"]: x for x in out}.values())
    (ROOT / "data" / "brand-golf-next-24.json").write_text(
        json.dumps({"brand": "GOLF NEXT 24", "source_url": URL, "fetched_at": today,
                    "count": len(res), "stores": res}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"GOLF NEXT 24: {len(res)}店舗")
    miss = [x["name"] for x in res if not x["pref"]]
    if miss:
        print(f"  ⚠️ 都道府県が取れない: {miss}")
    print(f"  24時間営業 {sum(1 for x in res if x['open_24h'])} / "
          f"個室数あり {sum(1 for x in res if x['rooms_num'])}")
    for x in res[:4]:
        print("   ", x["name"], "|", x["pref"], "|", x["rooms"], "|", x["parking"][:24])


main()
