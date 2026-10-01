#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZEN GOLF RANGE（ゼンゴルフレンジ）の店舗を公式サイトから取る。

店舗一覧 https://zengolf.jp/location/ に店舗ページへのリンクが並んでいる。
店舗ページは直下のスラッグ（/ageo/ など）で、各ページの <dt>/<dd> に
住所・営業時間・電話番号・駐車場・月会費が入っている。

⚠️ 一覧には /column/ /faq/ などの非店舗ページも混ざる。URLで弾いたうえで、
   最後は「住所の行があるか」で判定する（名前で弾くと新しい固定ページを取りこぼす）。
⚠️ 公式に書いていない項目（打席数・機種名）は None のままにする。推測で埋めない。

  python3 scripts/collect_zengolf.py            # 取得して data/zengolf.json に書く
  python3 scripts/collect_zengolf.py --limit 3  # 動作確認
"""
import argparse
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://zengolf.jp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "ZEN GOLF RANGE", "zengolf"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")

# 住所が市名から始まる店がある（「さいたま市北区大成町…」）。推測できる政令市だけを表にする。
# 表に無いものは補わない（当てずっぽうで県名を作らない）。他の収集スクリプトと同じ方針。
CITY_PREF = {"横浜市": "神奈川県", "川崎市": "神奈川県", "相模原市": "神奈川県",
             "名古屋市": "愛知県", "大阪市": "大阪府", "京都市": "京都府", "神戸市": "兵庫県",
             "札幌市": "北海道", "仙台市": "宮城県", "さいたま市": "埼玉県", "千葉市": "千葉県",
             "広島市": "広島県", "福岡市": "福岡県", "北九州市": "福岡県", "岡山市": "岡山県",
             "熊本市": "熊本県", "新潟市": "新潟県", "静岡市": "静岡県", "浜松市": "静岡県",
             "堺市": "大阪府"}


def pref_of(addr: str):
    m = re.match(rf"({PREFS})", addr)
    if m:
        return m.group(1)
    for city, pref in CITY_PREF.items():
        if addr.startswith(city):
            return pref
    return None


# 店舗ではないと分かっているパス
NOT_STORE = re.compile(r"/(column|faq|feature|flow|facilities|news|company|contact|price|"
                       r"lesson|campaign|voice|blog|privacy|terms|sitemap|recruit|fc)/")


def get(url: str) -> str:
    # ⚠️ 空で返ることがある。1回で諦めると店舗が黙って落ちる
    for _ in range(3):
        r = subprocess.run(["curl", "-s", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def rows(page_html: str) -> dict:
    out = {}
    for m in re.finditer(r"<(dt|th)[^>]*>(.*?)</\1>\s*<(dd|td)[^>]*>(.*?)</\3>", page_html, re.S):
        k, v = text(m.group(2)), text(m.group(4))
        if k and v and k not in out:
            out[k] = v
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    listing = get(f"{BASE}/location/")
    urls = sorted({u for u in re.findall(rf'href="({re.escape(BASE)}/[^"?#]+/)"', listing)
                   if u != f"{BASE}/" and not NOT_STORE.search(u)})
    print(f"店舗候補 {len(urls)}件")

    today = date.today().isoformat()
    stores, skipped = [], []
    for i, url in enumerate(urls, 1):
        if a.limit and i > a.limit:
            break
        h = get(url)
        r = rows(h)
        addr = r.get("住所")
        if not addr:
            skipped.append(url.replace(BASE, ""))
            continue
        title = text((re.search(r"<title>(.*?)</title>", h, re.S) or ["", ""])[1])
        name = title.split("|")[0].strip() or url.rstrip("/").rsplit("/", 1)[-1]
        hours = r.get("営業時間")
        # 店舗ページのスラッグをそのままURLに使う（/academy/ 付きは親を使う）
        slug = re.sub(r"/academy$", "", url.replace(BASE, "").strip("/"))
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": slug.replace("/", "-"),
            "name": name,
            "pref": pref_of(addr),
            "zip": None,
            "address": addr,
            "access": r.get("電車でお越しの方"),
            "tel": r.get("電話番号"),
            "hours": hours,
            "open_24h": bool(hours and "24時間" in hours),
            # 「定休日：なし」が営業時間の文中に入っている
            "closed": r.get("定休日") or ("なし" if hours and "定休日：なし" in hours else None),
            "bays": None, "bays_num": None,
            "private_room": None,
            "parking": r.get("駐車場"),
            "monthly_fee": r.get("月会費"),
            "equipment": None,
            "open": True,
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        print(f"  {i:3}/{len(urls)} {name} … {stores[-1]['pref'] or '県不明'}")
        time.sleep(2)   # 公式サイトに負荷をかけない

    out = DATA / "zengolf.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件 → {out}")
    nopref = [s["name"] for s in stores if not s["pref"]]
    if nopref:
        print("  ⚠️ 都道府県が取れなかった店:", nopref)
    if skipped:
        print(f"  住所の行が無く除外（店舗ページではない）: {len(skipped)}件 {skipped[:8]}")


if __name__ == "__main__":
    main()
