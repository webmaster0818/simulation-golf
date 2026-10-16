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

2026-10-16 追加: shop.js だけ読んでいたため、各店舗ページ（/shop/<store_code>.html）にある
アクセス・月会費・機種・打席の種類が「公式サイトに記載なし」になっていた。店舗ページも読む。
  - 「ACCESS アクセス案内」の <h3>■見出し</h3><div>本文</div>（■アクセス・■営業時間・■電話）。
    ■電話 の無い店は ■営業時間 の「御用の方はお客様相談室(フリーコール)0800－500-3678まで。受付時間:…」が窓口。
  - 「施設案内 充実のラインナップ」の各プラン（「通常打席×DITECT ＜ゴルフ会員＞ ¥12,000（税込¥13,200）/月 …」
    「個室打席×TRACKMAN」）から 月会費・機種・打席の種類・個室。
    ⚠️ 「■月会費 12,000円（税込 円）」の税込額は JavaScript が後から入れる空欄。ここからは読まない。
  - 駐車場: 公式FAQ（https://www.fit24.jp/qa/ のインドアゴルフ「施設・サービスについて」= id="service_g"）に
    「駐車場はありますか？ 全店舗無料駐車場を完備しております。」→ インドアゴルフ全店に適用（出典は parking_source_url）。
    ⚠️ meta description の「駐車場も完備の進化型インドアゴルフです」は全ページ同文の飾りなので根拠にしない。
    ゴルフスタジオ（横浜北山田）は FAQ の対象（インドアゴルフ）ではないので入れない。
  - 打席数（台数）はどこにも書いていない → bays_num は None。
"""
import html as html_
import json
import re
import subprocess
import time
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


QA_URL = "https://www.fit24.jp/qa/"


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                           capture_output=True, text=True)
        if r.stdout and len(r.stdout) > 5000:
            return r.stdout
        time.sleep(3)
    return ""


def clean(v: str) -> str:
    return html_.unescape(re.sub(r"[ \t　\n]+", " ", re.sub(r"<br\s*/?>", " ", re.sub(r"<(?!br)[^>]+>", "", v)))).strip()


def access_rows(h: str) -> dict:
    out = {}
    for k, v in re.findall(r'<h3 class="txtTable_title c_wh">■([^<]+)</h3>\s*<div[^>]*>(.*?)</div>', h, re.S):
        v = clean(v)
        if v:
            out.setdefault(k.strip(), v)
    return out


def lineup(h: str) -> list:
    """「充実のラインナップ」のプラン: [(プラン名, 1行目の「通常打席×DITECT」, 料金の行)]"""
    out = []
    for name, body in re.findall(r'<h5 class="lineupList_item_ttl">(.*?)</h5>.*?<div class="lineupList_item_txt">(.*?)</div>', h, re.S):
        ps = [clean(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)]
        ps = [x for x in ps if x]
        if ps and re.search(r"打席×", ps[0]):
            out.append((clean(name), ps[0], ps[1:]))
    return out


def parking_all_stores() -> bool:
    """公式FAQ（インドアゴルフの施設・サービス）に「全店舗無料駐車場を完備」と書いてあるか。"""
    h = get(QA_URL)
    i, j = h.find('id="service_g"'), h.find('id="other_g"')
    return i >= 0 and "全店舗無料駐車場を完備しております" in h[i:j if j > i else None]


def main() -> None:
    js = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, URL],
                        capture_output=True, text=True).stdout
    m = re.search(r"var stores\s*=\s*(\{[\s\S]*?\});", js)
    if not m:
        raise SystemExit("店舗データの位置が変わっている。取得を中止する。")
    body = m.group(1).replace("　", " ")          # 全角スペース
    body = re.sub(r",\s*([}\]])", r"\1", body)        # 末尾カンマ
    stores = json.loads(body)

    parking_ok = parking_all_stores()
    print("  公式FAQ「全店舗無料駐車場を完備」:", parking_ok)
    today, out = date.today().isoformat(), []
    for region, items in stores.items():
        for s in items:
            if s.get("biz") not in GOLF:
                continue
            addr = (s.get("address") or "").strip()
            pm = re.search(f"({PREF})", addr)
            official = SITE + s["store_url"] if s.get("store_url") else None
            page = get(official) if official else ""
            if official:
                time.sleep(1.5)   # 公式サイトに負荷をかけない
            rows = access_rows(page)
            plans = lineup(page)
            # 機種・打席の種類（「通常打席×DITECT」「個室打席×TRACKMAN」）
            kinds, machines = [], []
            for _, head, _ in plans:
                km = re.match(r"(\S+打席)×(\S+)", head)
                if km:
                    kinds.append(f"{km.group(1)}（{km.group(2)}）")
                    if km.group(2) not in machines:
                        machines.append(km.group(2))
            fee = "／".join(f"{n}（{head}） " + " ".join(x for x in rest if re.search(r"[¥円]", x))
                            for n, head, rest in plans if any(re.search(r"[¥円]", x) for x in rest)) or None
            if not fee and rows.get("月会費") and re.search(r"\d", rows["月会費"]):
                # ゴルフスタジオ: ラインナップに料金が無く「プラン料金（月額）」だけ。税込額は空欄（JSで後入れ）
                pr = re.search(r"プラン料金（月額）(.*?)Information",
                               re.sub(r"\s+", " ", clean(re.sub(r"<script.*?</script>", "", page, flags=re.S))))
                fee = None
                if pr:
                    items_ = re.findall(r"(\S+) ¥\s?([\d,]+) （税込¥\s?）", pr.group(1))
                    extra = re.findall(r"【[^】]+】[^【 ]+", pr.group(1))
                    if items_:
                        fee = ("／".join(f"{n} {v}円" for n, v in items_) + "（公式の税込額の欄は空欄）"
                               + ("。" + " ".join(e.strip() for e in extra) if extra else ""))
            hours_txt = rows.get("営業時間")
            if not hours_txt and rows.get("セルフ営業時間"):
                hours_txt = f"セルフ営業時間 {rows['セルフ営業時間']}／スタジオ営業時間 {rows.get('スタジオ営業時間', '')}".strip("／ ")
            tel = s.get("tel") or rows.get("電話")
            if not tel and hours_txt:
                fm = re.search(r"お客様相談室\(フリーコール\)\s*([\d０-９\-－]+)\s*まで。\s*(受付時間:[^)）]*[)）])", hours_txt)
                if fm:
                    tel = f"{fm.group(1).replace('－', '-')}（お客様相談室・フリーコール。{fm.group(2)}。終日スタッフ不在の店舗）"
            golf_indoor = s["biz"] == "indg"
            out.append({
                "brand": GOLF[s["biz"]][0], "brand_slug": GOLF[s["biz"]][1],
                "slug": s.get("store_code") or f"fit24-{s['id']}",
                "name": s.get("store_name"), "address": addr,
                "pref": pm.group(1) if pm else None,
                "tel": tel or None,
                "access": rows.get("アクセス"),
                # 公式が全店「24時間・年中無休」と明記しているブランド（FAQ「24時間年中無休でご利用いただけます」）。
                # 店舗ページの表記が違う店（ゴルフスタジオ: セルフ 20:00～10:00／スタジオ 10:00～20:00）はそちらを優先。
                "hours": "24時間" if (not hours_txt or hours_txt.startswith("24時間")) else hours_txt,
                "open_24h": True, "closed": "年中無休",
                "bays": "／".join(kinds) or None, "bays_num": None,
                "private_room": True if any(k.startswith("個室打席") for k in kinds) else None,
                "parking": "無料駐車場あり（公式FAQ「全店舗無料駐車場を完備しております。」）" if (golf_indoor and parking_ok) else None,
                **({"parking_source_url": QA_URL} if (golf_indoor and parking_ok) else {}),
                "monthly_fee": fee,
                "equipment": "／".join(machines) or None,
                # 同じ建物にフィットネスジムがあるか（FiT24だけの比較軸）
                "gym_attached": s.get("combi") == "1",
                "official": official,
                "source_url": official if page else URL, "fetched_at": today,
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
