#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""チキンゴルフ（CHICKEN GOLF）の店舗を公式サイトから取る。

公式 https://chicken-golf.com/ 。シミュレーターを置いた屋内のセミパーソナルゴルフレッスン。
店舗一覧 /schools/ に /schools/<slug>/ が並ぶ（2026-10-16 時点 29店）。
店舗ページ上部の「住所・アクセス・営業時間・定休日・電話」欄（_detailRow_ / _detailLabel_）を読む。

⚠️ クラス名の末尾はビルドごとのハッシュ（_detailLabel_vb1kd_177 など）。前方一致で読む。
⚠️ 駐車場は「アクセス」欄の中に、駅の行（_routeChip_）とは別の値として書かれている店がある
   （豊橋「駐車場あり」・松戸・天美・和泉・那覇・奈良）。parking に入れ、access には駅の行だけを残す。
⚠️ シミュレーターの機種は「GOLFZON社製」としか書かれていない（五反田・心斎橋）。機種名ではないので載せない。
⚠️ 打席数は本文の「打席数5打席」「2打席の小規模店舗」がある店だけ（千葉・西川口・京橋）。
⚠️ 個室は「全ブース個室」「完全個室」と書いた店だけ true（刈谷・梅田）。「半個室」は true にしない。
   トップページの「完全個室＆高性能シミュレーター付き」はブランド全体の宣伝文なので店舗には使わない。
⚠️ 月額は店舗ページの「デイライト通い放題 ¥9,800 / 月 ＋入会金」。税込・税抜の別は書かれていない。
⚠️ 公式URLの綴りが崩れている店がある（chohu＝調布・kyouto＝京都・kobesannnomiya＝神戸三宮）。
   CLUB19 と同じくヘボン式にそろえる。hakata は店名が「福岡赤坂店」（住所は福岡市中央区大名）なので
   店名の地名に合わせる。

  python3 scripts/collect_chickengolf.py
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
BASE = "https://chicken-golf.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "チキンゴルフ", "chickengolf"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")

# 住所が市名から始まる店（「福岡市中央区…」「札幌市中央区…」「神戸市中央区…」「大阪市都島区…」）
CITY_PREF = {"横浜市": "神奈川県", "川崎市": "神奈川県", "相模原市": "神奈川県",
             "名古屋市": "愛知県", "大阪市": "大阪府", "京都市": "京都府", "神戸市": "兵庫県",
             "札幌市": "北海道", "仙台市": "宮城県", "さいたま市": "埼玉県", "千葉市": "千葉県",
             "広島市": "広島県", "福岡市": "福岡県", "北九州市": "福岡県", "岡山市": "岡山県",
             "熊本市": "熊本県", "新潟市": "新潟県", "静岡市": "静岡県", "浜松市": "静岡県",
             "堺市": "大阪府"}

# 公式URL → こちらのslug。公式の先頭の県名（tokyo- osaka- など）は落とす。
SLUG_FIX = {"chohu": "chofu", "kyouto": "kyoto", "kobesannnomiya": "kobe-sannomiya",
            "hakata": "fukuoka-akasaka", "aichi-nagoyasakae": "nagoya-sakae",
            "osaka-amami": "sevenpark-amami", "osaka-izumi": "lalaport-izumi"}
PREF_PREFIX = ("tokyo-", "osaka-", "aichi-", "chiba-", "hokkaido-", "kanagawa-", "miyagi-", "okinawa-")


def pref_of(addr: str):
    m = re.match(rf"({PREFS})", addr)
    if m:
        return m.group(1)
    for city, pref in CITY_PREF.items():
        if addr.startswith(city):
            return pref
    return None


def our_slug(official: str) -> str:
    if official in SLUG_FIX:
        return SLUG_FIX[official]
    for p in PREF_PREFIX:
        if official.startswith(p):
            return official[len(p):]
    return official


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def text(s: str) -> str:
    s = re.sub(r"<br\s*/?>", " ", s)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def detail_rows(h: str) -> dict:
    """{ラベル: 行のHTML}。行は _detailRow_ の div ごと。"""
    out = {}
    parts = re.split(r'<div class="_detailRow_[^"]*">', h)
    for p in parts[1:]:
        lab = re.search(r'_detailLabel_[^"]*">(.*?)</span>', p, re.S)
        if lab:
            out[text(lab.group(1))] = p[lab.end():]
    return out


def body_text(h: str) -> str:
    h = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", "", h)
    return text(h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    listing = get(f"{BASE}/schools/")
    officials = sorted(set(re.findall(r'schools/([a-z0-9-]+)/', listing)))
    print(f"店舗候補 {len(officials)}件")
    today = date.today().isoformat()
    stores, skipped = [], []
    for i, off in enumerate(officials, 1):
        if a.limit and i > a.limit:
            break
        url = f"{BASE}/schools/{off}/"
        h = get(url)
        rows = detail_rows(h)
        if "住所" not in rows:
            skipped.append(off)
            continue
        addr_lines = [text(x) for x in re.findall(r'_addressLine_[^"]*">(.*?)</span>', rows["住所"], re.S)]
        zipc = None
        if addr_lines and addr_lines[0].startswith("〒"):
            z = re.sub(r"\D", "", addr_lines.pop(0))
            zipc = z if len(z) == 7 else None
        addr = " ".join(addr_lines).strip()

        acc = rows.get("アクセス", "")
        acc = acc.split('<div class="_detailRow_')[0]
        chips = [text(c) for c in re.findall(r'_routeChip_[^"]*">(.*?)</span>', acc, re.S)]
        extra = [text(v) for v in re.findall(r'_detailValue_[^"]*"[^>]*>(.*?)</span>', acc, re.S)]
        # 奈良は「※以下の提携駐車場をご利用ください。」が span の外の地の文
        rest = text(re.sub(r'<span class="_routeChip_.*?</span>|<span class="_detailValue_.*?</span>', " ", acc, flags=re.S))
        notes = [x for x in [rest] + extra if x]
        # 駐車場の語を含む店だけ parking にする（名古屋栄は「エレベーターが停まりません」の注意書き＝経路の話）
        parking = " ".join(notes) if any("駐車" in x for x in notes) else None
        if notes and not parking:
            chips.append(" ".join(notes))

        def val(label):
            r = rows.get(label)
            if not r:
                return None
            m = re.search(r'_detailValue_[^"]*"[^>]*>(.*?)</span>', r, re.S)
            return text(m.group(1)) if m else None

        hours = val("営業時間")
        tel = rows.get("電話")
        tel_txt = None
        if tel:
            m = re.search(r'_detailValue_[^"]*"[^>]*>(.*?)</span>', tel, re.S)
            tel_txt = re.sub(r"\s*\n\s*", "／", html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()) if m else None

        name_m = re.search(r'<h2 id="access_store_name"[^>]*>(.*?)</h2>', h, re.S)
        name = text(name_m.group(1)) if name_m else off

        bt = body_text(h)
        bays_num = bays = None
        m = re.search(r"打席数\s*(\d+)\s*打席", bt) or re.search(r"(\d+)\s*打席の小規模店舗", bt)
        if m:
            bays_num = int(m.group(1)); bays = f"{bays_num}打席"
        private_room = True if re.search(r"全(ブース|室)個室|完全個室", bt) else None

        fee = None
        pn = re.search(r'_planName_[^"]*">(.*?)</p>', h, re.S)
        mp = re.search(r'_monthlyPrice_[^"]*">(.*?)</p>', h, re.S)
        mu = re.search(r'_monthlyUnit_[^"]*">(.*?)</p>', h, re.S)
        ad = re.search(r'_admission_[^"]*">(.*?)</p>', h, re.S)
        if pn and mp and re.search(r"\d", mp.group(1)):
            price = text(mp.group(1)).replace("¥", "")
            unit = text(mu.group(1)).replace(" ", "") if mu else ""
            tail = "（別途入会金。" if ad and "入会金" in ad.group(1) else "（"
            fee = f"{text(pn.group(1))} {price}円{unit}{tail}税込・税抜の別は公式サイトに記載なし）"

        open_ = not re.search(r"OPEN予定|オープン予定|グランドオープン予定", bt)
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": our_slug(off),
            "name": name,
            "pref": pref_of(addr),
            "zip": zipc,
            "address": addr,
            "access": "／".join(chips) or None,
            "tel": tel_txt,
            "hours": hours,
            "open_24h": bool(hours and "24時間" in hours),
            "closed": val("定休日"),
            "bays": bays, "bays_num": bays_num,
            "private_room": private_room,
            "parking": parking,
            "monthly_fee": fee,
            "equipment": None,
            "open": open_,
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        print(f"  {i:3}/{len(officials)} {name} … {stores[-1]['pref'] or '県不明'}")
        time.sleep(1.5)

    out = DATA / "chickengolf.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件（準備中 {sum(not s['open'] for s in stores)}）→ {out}")
    nopref = [s["name"] for s in stores if not s["pref"]]
    if nopref:
        print("  ⚠️ 都道府県が取れなかった店:", nopref)
    if skipped:
        print(f"  住所の欄が無く除外: {skipped}")


if __name__ == "__main__":
    main()
