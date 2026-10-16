#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMART GOLF（sma-gol.com）の店舗データを、公式の店舗ページから取る。

店舗の一覧は公式サイトの sitemap-0.xml にある /shop/<slug>/ を使う（2026-10-12 時点 215店）。
店舗ページは静的HTMLで、以下が店舗ごとに書かれている:
  「アクセス・営業時間」欄 … 住所 / 最寄り駅 / 営業時間
  「<店名>のプラン・料金」欄 … プラン名 → ¥ → 税抜額 → 税抜 → （税込¥ → 税込額
  「店舗詳細」欄 … 住所 / TEL / 最寄駅 / 「2ルーム」「シミュレーター2台設置」

⚠️ 同じサイトの /smagol/<slug>/ は別ブランド「スマゴル」（6店）。SMART GOLF には混ぜない。
   /shop/ の下でも店舗詳細欄が「スマゴル」の店（鎌ヶ谷・清瀬）は「アクセス・営業時間」欄が無く、取れずに落ちる＝除外のままでよい。
⚠️ 駐車場（2026-10-16 追加）。公式FAQページ（/faq/）は「店舗により提携駐車場をご案内しています。各店舗ページのアクセスをご確認ください。」。
   店舗ページの次の順で読む:
     1.「アクセス・営業時間」欄の「駐車場」行（専用駐車場あり(店舗前2台) 等・35店）
     2.「店舗詳細」欄の「※提携駐車場（有料）を割引でご利用いただけるプランをご用意しています。…」（20店）
     3. 店舗ページの「よくあるご質問」の「駐車場はありますか？」の答え
   ⚠️ 以前は 3 を「全店共通の文」として捨てていたが、実際は店舗ごとに書き分けられている
      （専用駐車場のある店は「店舗前に専用駐車場がございます(2台分)。」、イオンタウン新船橋は「…駐車場を2時間無料で…」）。
      ただしトップページ（sma-gol.com/）の FAQ はブランド全体の文なので使わない。
      1・2 と 3 が食い違う店（「店舗詳細」に提携駐車場プラン・FAQ は「提携駐車場のご用意はございません」）は 1・2 を採る。
⚠️ 定休日: 公式FAQ「年中無休の店舗が中心です。※店舗によって異なります」＝全店ではない。
   営業時間の欄に「365日」と書かれた店（「24時間365日」「6:00-24:00 365日」）だけ「年中無休（365日営業）」。
   「24時間」「6:00-24:00」だけの店は None（24時間から定休日を推測しない）。
⚠️ 機種: 公式FAQ「取り扱いシミュレーターの種類は？ … 機種は店舗により異なります。」で、店舗ページにも機種名が無い
   （GOLFZON WAVE の記載は別ブランド「スマゴル」の鎌ヶ谷・清瀬だけ）。equipment は None。
⚠️ 右打席のみ・レンタルクラブ等も FAQ の共通文なので施設データには入れない。
⚠️ 開業日（「YYYY年M月D日 GRAND OPEN!」）が今日より後の店は open=False（準備中）。

使い方:
  python3 scripts/collect_smartgolf.py [--cache /tmp/smartgolf-pages]
"""
import argparse
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = "https://sma-gol.com/sitemap-0.xml"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = re.compile(r"^(北海道|東京都|大阪府|京都府|.{2,3}県)")


def curl(url: str) -> str:
    return subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                          capture_output=True, text=True).stdout


def lines(html: str) -> list:
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<!--[\s\S]*?-->", "", html)
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", "\n", t).replace("&nbsp;", " ").replace("&amp;", "&")
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip() for v in t.split("\n")) if x]


def after(L: list, label: str, start: int = 0, stop: int | None = None) -> str | None:
    for i in range(start, stop if stop is not None else len(L) - 1):
        if L[i] == label and i + 1 < len(L):
            return L[i + 1]
    return None


def parse(slug: str, html: str, today: str) -> dict | None:
    L = lines(html)
    m = re.search(r"<title>\s*(?:インドアゴルフ\s*)?SMART GOLF\s*(.+?)\s*\|", html)
    if not m:
        return None
    shop = m.group(1).strip()
    name = f"SMART GOLF {shop}"
    # 「アクセス・営業時間」欄
    try:
        a = L.index("アクセス・営業時間")
    except ValueError:
        return None
    near = next((i for i in range(a, len(L)) if L[i] == "こちらの店舗もお近くにあります"), len(L))
    address = after(L, "住所", a, near)
    access = after(L, "最寄り駅", a, near)
    hours = after(L, "営業時間", a, near)
    parking = after(L, "駐車場", a, near)
    src = {}
    if parking:
        src["parking"] = "店舗ページ「アクセス・営業時間」欄の駐車場"
    closed = None
    if hours and "365日" in hours:
        closed = "年中無休（365日営業）"
        src["closed"] = f"店舗ページの営業時間「{hours}」"
    # 「店舗詳細」欄
    d = next((i for i in range(len(L)) if L[i] == "店舗詳細"), None)
    tel = after(L, "TEL", d, min(d + 20, len(L))) if d is not None else None
    # TEL は全店とも同じ番号（ページ上部に「受付時間 9:00 - 21:00」）。店舗に直接つながる番号と
    # 誤解されないよう、ページに書かれている受付時間を添える。
    rcpt = next((x[len("受付時間"):].strip() for x in L[:a] if x.startswith("受付時間 ")), None)
    if tel and rcpt:
        tel = f"{tel}（受付時間 {rcpt}）"
    rooms = sims = None
    if d is not None:
        for x in L[d:d + 20]:
            if re.fullmatch(r"\d+ルーム", x):
                rooms = x
            # 「2シミュレーター2台設置」と書かれた店が22店ある（原文のまま載せ、台数は「N台」から取る）
            if re.fullmatch(r"\d*シミュレーター\d+台設置", x):
                sims = x
    sims_n = int(re.search(r"(\d+)台", sims).group(1)) if sims else None
    if not parking and d is not None:
        pk = next((x for x in L[d:d + 20] if x.startswith("※提携駐車場")), None)
        if pk:
            parking = pk.lstrip("※")
            src["parking"] = "店舗ページ「店舗詳細」欄"
    if not parking:
        q = next((i for i in range(len(L) - 1) if L[i] == "駐車場はありますか？"), None)
        if q is not None and not L[q + 1].endswith("？"):
            parking = L[q + 1]
            src["parking"] = "店舗ページの よくあるご質問「駐車場はありますか？」"
    # 「<店名>のプラン・料金」欄
    fees = []
    p = next((i for i in range(len(L)) if L[i].endswith("のプラン・料金") and L[i] != "プラン・料金"), None)
    if p is not None:
        end = next((i for i in range(p, len(L)) if L[i] in ("Coach", "Store")), len(L))
        for i in range(p, end - 3):
            if (re.fullmatch(r"¥[\d,]+", L[i + 1]) and L[i + 2] == "税抜"
                    and (m2 := re.fullmatch(r"（税込¥([\d,]+)）?", L[i + 3]))):
                # 回数プランは「月3回」だけが名前の行になっているので頭に付ける
                label = f"回数プラン{L[i]}" if re.fullmatch(r"月\d+回", L[i]) else L[i]
                fees.append(f"{label} {m2.group(1)}円")
    # 開業日はページ上部の「2026年11月25日 GRAND OPEN!」。開業後も消えずに残る（成城学園前 2024年7月26日 等）。
    # ⚠️ 住所下の「※Google Mapに登録中ですが、表示されている場所にSMART GOLFのオープン予定です。」は
    #    2025年開業の店にも残っている定型文なので、準備中の判定に使わない。
    hero = L[:a]
    grand = next((m3 for x in hero if (m3 := re.match(
        r"(\d{4})年(\d{1,2})月(\d{1,2})日.*GRAND OPEN", x, re.I))), None)
    pre = None
    if grand:
        gd = date(int(grand.group(1)), int(grand.group(2)), int(grand.group(3)))
        if gd.isoformat() > today:
            pre = grand
    pref = PREF.match(address or "")
    if address:
        address = address.replace("‐", "-").replace("−", "-")
    return {
        "brand": "SMART GOLF", "brand_slug": "smartgolf", "slug": slug,
        "name": name, "pref": pref.group(1) if pref else None, "zip": None,
        "address": address, "access": access, "tel": tel, "hours": hours,
        "open_24h": bool(hours and hours.startswith("24時間")),
        "closed": closed,
        "bays": "／".join(x for x in (rooms, sims) if x) or None,
        "bays_num": sims_n, "private_room": None, "parking": parking,
        "monthly_fee": ("／".join(fees) + "（税込）") if fees else None,
        "equipment": None, "open": pre is None,
        "note": pre.group(0) if pre else None,
        "official": f"https://sma-gol.com/shop/{slug}/",
        "source_url": f"https://sma-gol.com/shop/{slug}/",
        "fetched_at": today,
        **({"field_sources": src} if src else {}),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/smartgolf-pages")
    ap.add_argument("--out", default=str(ROOT / "data" / "smartgolf.json"))
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    sm = curl(SITEMAP)
    slugs = sorted(set(re.findall(r"<loc>https://sma-gol\.com/shop/([^/<]+)/</loc>", sm)))
    print(f"sitemap: /shop/ {len(slugs)}件")
    stores, bad = [], []
    for slug in slugs:
        fp = cache / f"{slug}.html"
        if not fp.exists() or fp.stat().st_size < 10000:
            fp.write_text(curl(f"https://sma-gol.com/shop/{slug}/"), encoding="utf-8")
            time.sleep(2)
        s = parse(slug, fp.read_text(encoding="utf-8"), today)
        if not s or not s["address"] or not s["pref"]:
            bad.append(slug)
            continue
        stores.append(s)
    print(f"取得 {len(stores)}件 / 取れなかった {len(bad)}件: {bad}")
    for s in stores:
        if not s["open"]:
            print("  準備中:", s["name"], "|", s["note"])
        if not s["monthly_fee"]:
            print("  料金なし:", s["name"])
    Path(a.out).write_text(json.dumps({"brand": "SMART GOLF", "source_url": SITEMAP,
                                       "fetched_at": today, "count": len(stores), "stores": stores},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
    print("書き出し →", a.out)


if __name__ == "__main__":
    main()
