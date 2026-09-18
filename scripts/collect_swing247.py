#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SWING24/7 の店舗データを公式の店舗一覧から取る。

一覧ページ1枚に全店舗が載っている。1店舗のかたまりは
  店名 → (開店予告) → 〒 → 住所 → アクセス → 駐車場 → 電話 → Google Map
の順で、住所が2行に割れている店舗がある。

⚠️ 「近日オープン予定」の店舗は open=False で持ち、掲載時に既存店と混ぜない。
   オープン前を営業中として数えるのは、利用者にとって実害のある誤りになる。
"""
import json
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://swing24.co.jp/locations"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")
TEL = re.compile(r"^0\d{1,4}-\d{1,4}-\d{3,4}$")
# 住所行かどうかの判定。都道府県で始まらない表記があるため、市区町村＋数字でも拾う。
ADDR = re.compile(r"[市区町村]")
# 都道府県が省略された住所の補完（政令市など、市名で一意に定まるものだけ）
CITY_PREF = {"名古屋市": "愛知県", "札幌市": "北海道", "仙台市": "宮城県", "横浜市": "神奈川県",
             "川崎市": "神奈川県", "京都市": "京都府", "大阪市": "大阪府", "神戸市": "兵庫県",
             "広島市": "広島県", "福岡市": "福岡県", "北九州市": "福岡県", "さいたま市": "埼玉県",
             "千葉市": "千葉県", "新潟市": "新潟県", "静岡市": "静岡県", "浜松市": "静岡県",
             "堺市": "大阪府", "岡山市": "岡山県", "熊本市": "熊本県", "相模原市": "神奈川県"}


def lines_of(html: str) -> list:
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", "\n", t)
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip() for v in t.split("\n")) if x]


def parse(block: list) -> dict:
    """1店舗ぶんの行から項目を拾う。行の意味は内容で判定する（位置に依存しない）。"""
    # 県セクションの見出し行。住所ではないので落とす。
    block = [v for v in block
             if not re.fullmatch(f"({PREF})", v) and not re.fullmatch(r"[A-Za-z]{3,12}", v)]
    rec = {"zip": None, "address": "", "access": [], "parking": None, "tel": None,
           "open": True, "note": None}
    addr_parts = []
    for v in block:
        if re.fullmatch(r"〒\d{3}-?\d{4}", v):
            rec["zip"] = v.lstrip("〒")
        elif TEL.fullmatch(v):
            rec["tel"] = v
        elif "駐車" in v or "パーキング" in v:
            rec["parking"] = v
        elif re.search(r"OPEN|オープン", v):
            # ⚠️ 住所判定より先に見る。「9月下旬町田店OPEN予定!!」は
            #    「町＋数字」で住所にも見えてしまうため。
            rec["open"] = False
            rec["note"] = v
        elif re.search(r"(駅|徒歩|線)", v) and not re.search(f"^({PREF})", v):
            rec["access"].append(v)
        elif (re.search(f"^({PREF})", v) or (ADDR.search(v) and re.search(r"\d", v))
              or addr_parts):
            addr_parts.append(v)
    rec["address"] = "".join(addr_parts)
    m = re.search(f"({PREF})", rec["address"])
    if m:
        rec["pref"] = m.group(1)
    else:
        rec["pref"] = next((p for c, p in CITY_PREF.items() if c in rec["address"]), None)
    return rec


def main() -> None:
    html = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, URL],
                          capture_output=True, text=True).stdout
    ls = lines_of(html)
    heads = [i for i, v in enumerate(ls) if re.fullmatch(r"SWING24/7 ?\S.*店", v)]
    today, out = date.today().isoformat(), []
    for n, i in enumerate(heads):
        end = heads[n + 1] if n + 1 < len(heads) else min(i + 14, len(ls))
        block = [v for v in ls[i + 1:end] if v not in ("Google Map", "WEBサイト")]
        r = parse(block)
        out.append({
            "brand": "SWING24/7", "brand_slug": "swing247", "name": ls[i].strip(),
            **{k: r[k] for k in ("zip", "address", "pref", "parking", "tel", "open", "note")},
            "access": " / ".join(r["access"]) or None,
            # 公式が全店「24時間365日・無人」と明記しているブランド
            "hours": "24時間365日（無人運営）", "open_24h": True,
            "source_url": URL, "fetched_at": today,
        })

    res = list({x["name"]: x for x in out}.values())
    (ROOT / "data" / "brand-swing247.json").write_text(
        json.dumps({"brand": "SWING24/7", "source_url": URL, "fetched_at": today,
                    "count": len(res), "stores": res}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    opened = [x for x in res if x["open"]]
    print(f"SWING24/7: {len(res)}店舗（営業中 {len(opened)} / オープン予定 {len(res)-len(opened)}）")
    miss = [x["name"] for x in res if not x["pref"]]
    if miss:
        print(f"  ⚠️ 都道府県が取れない: {miss}")
    for x in res[:4]:
        print("   ", x["name"], "|", x["pref"], "|", (x["address"] or "")[:32], "|", x["tel"])


main()
