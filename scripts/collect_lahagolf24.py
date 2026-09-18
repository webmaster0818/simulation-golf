#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ラハゴルフ24 の店舗データを各店舗ページから取る。

店舗ページに 店舗名／住所／営業時間／アクセス／電話番号／月会費 が並ぶ。
**月会費が店舗ごとに載っている数少ないブランド**なので、料金比較の実データになる。

⚠️ 月会費は「10,900円（税抜）」「11,990円(税込)」と税表記が店舗で揃っていない。
   数値だけ取り出さず、税表記ごとそのまま残す（税抜と税込を並べて比べさせない）。
"""
import json
import re
import subprocess
import time
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = "https://laha-golf24.com/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")
LABELS = ["店舗名", "住所", "地図", "営業時間", "アクセス", "電話番号", "メールアドレス", "月会費"]
KEY = {"地図": None, "店舗名": "name", "住所": "address", "営業時間": "hours", "アクセス": "access",
       "電話番号": "tel", "メールアドレス": "email", "月会費": "monthly_fee"}


# 公式のURLが日本語のままの店舗が1件ある（/list/横浜東口店/）。
# 日本語のURLは共有やログで壊れやすいので、こちらでローマ字を割り当てる。
SLUG_FIX = {"横浜東口店": "yokohama-higashiguchi"}


def slug_of(url: str) -> str:
    raw = urllib.parse.unquote(url.rstrip("/").rsplit("/", 1)[-1])
    return SLUG_FIX.get(raw, raw)


def parking_from_access(access: str | None) -> str | None:
    """このブランドは公式の「アクセス」欄に駐車場の案内を混ぜて書いている。

    例: 「茅ヶ崎駅南口より徒歩5分 駐車場2台 駐輪場5台有」
    駐車場の有無で絞り込めるようにしたいので、駐車場に触れている部分だけを
    取り出して parking にも入れる。⚠️ 原文は access にそのまま残す（改変しない）。
    """
    if not access or "駐車" not in access:
        return None
    parts = re.split(r"[、,／/ 　]+", access)
    hit = [x for x in parts if "駐車" in x]
    return " ".join(hit) if hit else access


def get(url: str) -> str:
    return subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                          capture_output=True, text=True).stdout


def lines_of(html: str) -> list:
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip()
                        for v in re.sub(r"<[^>]+>", "\n", t).split("\n")) if x]


def main() -> None:
    idx = get(LIST)
    urls = sorted(set(re.findall(r"https://laha-golf24\.com/list/[^\"'\s]+/", idx)))
    print(f"店舗ページ: {len(urls)}件")

    today, out, ng = date.today().isoformat(), [], []
    for n, u in enumerate(urls, 1):
        ls = lines_of(get(u))
        rec, i = {}, 0
        while i < len(ls):
            if ls[i] in LABELS:
                vals = []
                for k in range(i + 1, len(ls)):
                    if ls[k] in LABELS or ls[k] == "店舗一覧に戻る":
                        break
                    vals.append(ls[k])
                if KEY[ls[i]]:
                    rec[KEY[ls[i]]] = vals
                i += len(vals) + 1
            else:
                i += 1
        if "address" not in rec:
            ng.append(u); time.sleep(2); continue
        # 住所は「336-0021」と「埼玉県…」の2行に分かれている
        parts = rec["address"]
        zipc = next((p.replace("〒", "") for p in parts
                     if re.fullmatch(r"〒?\d{3}-?\d{4}", p)), None)
        addr = "".join(p for p in parts if not re.fullmatch(r"〒?\d{3}-?\d{4}", p))
        pm = re.search(f"({PREF})", addr)
        out.append({
            "brand": "ラハゴルフ24", "brand_slug": "lahagolf24",
            "name": (rec.get("name") or [u])[0],
            "slug": slug_of(u),
            "zip": zipc, "address": addr, "pref": pm.group(1) if pm else None,
            "hours": " ".join(rec.get("hours", [])) or None,
            "open_24h": "24時間" in " ".join(rec.get("hours", [])),
            "access": " ".join(rec.get("access", [])) or None,
            "parking": parking_from_access(" ".join(rec.get("access", []))),
            "tel": next((p for p in rec.get("tel", []) if re.match(r"^0\d", p)), None),
            "monthly_fee": (rec.get("monthly_fee") or [None])[0],
            "source_url": u, "fetched_at": today,
        })
        if n % 5 == 0 or n == len(urls):
            print(f"  [{n}/{len(urls)}]", flush=True)
        time.sleep(2)

    (ROOT / "data" / "brand-lahagolf24.json").write_text(
        json.dumps({"brand": "ラハゴルフ24", "source_url": LIST, "fetched_at": today,
                    "count": len(out), "stores": out, "failed": ng},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ラハゴルフ24: {len(out)}店舗 / 取得失敗 {len(ng)}")
    for k in ("address", "pref", "hours", "access", "tel", "monthly_fee"):
        print(f"  {k}: {sum(1 for x in out if x.get(k))}/{len(out)}")
    for x in out[:4]:
        print("   ", x["name"], "|", x["pref"], "|", x["monthly_fee"], "|", x["hours"])


main()
