#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLFEED24 の店舗データを各店舗ページの「店舗情報」表から取る。

店舗ページに 住所／アクセス方法／営業時間／定休日／打席数／駐車場 が揃っている。
一覧ページから店舗ページのURLを拾い、2秒間隔で1件ずつ取得する。

⚠️ 表に無い項目は None のまま。埋めない。

2026-10-16 追加:
- monthly_fee: 店舗ページの「料金プラン」欄（店ごとに4種類の作りがある。カード型「/月（税込）」、
  「月額 ¥N （税込）」、表型「プラン 料金 …」）から個人向けプランを店の表記のまま並べる。
  税込の記載がある店だけ「税込」と書く（表型の店は料金表に税の記載が無い）。法人プランは「ほかに法人プランあり」。
- equipment: 店舗ページには機種名が無い（「高性能シミュレーター」のみ）。公式FAQの
  「GOLFEED24について」の問い「他のインドアゴルフ練習場との違いは何ですか？」の答え
  「高性能シミュレーター【OKON GOLF】を導入し…」をブランド全体の記載として全店に当てる（note に出典）。
  表記はFC募集ページ・豊中店ページと同じ「OK ON GOLF」。店舗ページに型式があれば店舗ページを優先。
- tel: 店舗ページ・FAQに店舗の電話番号は無い（問い合わせはLINE）。会社概要の番号は本社なので入れない。
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


FAQ = "https://golfeed24.com/faq"
# 見出しの表記が揺れる店（神戸東灘: title「東灘店」／h1「神戸東灘店」）は店名を固定する（CLAUDE.md・2026-10-12）
KEEP_NAME = {"higashinada": "ゴルフィード24 神戸東灘店"}
BRAND_EQUIP = "OK ON GOLF"
STOP = ("追加チケット", "会員様限定追加チケット", "ビジター料金", "ビジターチケット",
        "スクール会員", "レッスンチケット", "無料レンタルサービス", "店舗情報")
PRICE = re.compile(r"^[¥￥]?[\d,]+円?〜?$")


def fee_of(ls: list):
    """料金プラン欄から個人向けプランの料金を店の表記のまま並べる。"""
    try:
        a = ls.index("ご利用用途に合わせて選べる豊富な料金プランをご用意しています。")
    except ValueError:
        return None
    b = next((i for i in range(a, len(ls)) if ls[i] in STOP), len(ls))
    sec = ls[a:b]
    plans, corp, entry, entry_tax, taxed = [], False, None, False, []
    for i, v in enumerate(sec):
        m = re.match(r"^入会金\s*([\d,]+円)$", v)
        if m and not entry:
            entry, entry_tax = m.group(1), "税込" in " ".join(sec[i + 1:i + 2])
            continue
        if not PRICE.match(v) or i == 0:
            continue
        name = sec[i - 2] if sec[i - 1] == "月額" else sec[i - 1]
        if name == "入会金":
            if not entry:
                entry, entry_tax = v, "税込" in " ".join(sec[i + 1:i + 2])
            continue
        if name.startswith(("（", "(", "＋", "+")) or "：" in name:
            continue
        # レッスンの回数券（「1回券 4,000円 /枚」）は月会費ではない
        if i + 1 < len(sec) and sec[i + 1].startswith("/枚"):
            continue
        name = re.sub(r"^[^\w（(]+", "", name).strip()
        if re.search(r"法人|CORPORATE", name):
            corp = True
            continue
        price = v if v.endswith(("円", "円〜")) else v + "円"
        price = price.replace("￥", "¥")
        if price.startswith("¥"):
            price = price[1:] if price.endswith("円") else price
        plans.append(f"{name} {price}")
        nxt = " ".join(sec[i + 1:i + 6])
        taxed.append("税込" in nxt)
    if not plans:
        return None
    monthly = any(x.startswith("/月") for x in sec) or "月額" in sec
    tag = "・".join(t for t in (("月額" if monthly else ""), ("税込" if all(taxed) else "")) if t)
    out = "／".join(plans) + (f"（{tag}）" if tag else "")
    if entry:
        out += f"／入会金 {entry}" + ("（税込）" if entry_tax else "")
    if corp:
        out += "・ほかに法人プランあり"
    return out


def equip_of(ls: list):
    for v in ls:
        m = re.search(r"「(OK ON GOLF[^」]*)」", v)
        if m:
            return m.group(1)
    return None


def name_of(heading: str) -> str:
    m = re.search(r"(ゴルフィード24\s*\S+?店)", heading)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else heading.strip()


def main() -> None:
    idx = get(LIST)
    urls = sorted({re.sub(r"/?$", "/", u) for u in
                   re.findall(r"https://golfeed24\.com/store/[a-z0-9\-]+/?", idx)})
    urls = [u for u in urls if u != "https://golfeed24.com/store/"]
    print(f"店舗ページ: {len(urls)}件")

    faq = lines_of(get(FAQ))
    q = "他のインドアゴルフ練習場との違いは何ですか？"
    faq_ans = faq[faq.index(q) + 1] if q in faq else ""
    # ⚠️ FAQの文言が変わって機種名が消えたら、全店への当てはめもやめる。
    brand_equip = BRAND_EQUIP if "OKONGOLF" in faq_ans.replace(" ", "") else None
    print("FAQ:", faq_ans)

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
        own_equip = equip_of(ls)
        equip = own_equip or brand_equip
        note = None
        if equip and not own_equip:
            note = (f"機種は公式FAQ（{FAQ}）の「{q}」への回答「{faq_ans}」から（ブランド全体の記載。"
                    "店舗ページには機種名の記載なし）")
        out.append({
            "brand": "GOLFEED24", "brand_slug": "golfeed24",
            # 見出しはSEO用の長い文言（「インドアゴルフ 赤穂｜ゴルフィード24 赤穂店【…】」）
            # なので、その中から店舗名だけを取り出す。
            "name": KEEP_NAME.get(u.rstrip("/").rsplit("/", 1)[-1])
                    or name_of(ls[start + 1] if start + 1 < len(ls) else u),
            "slug": u.rstrip("/").rsplit("/", 1)[-1],
            "zip": zipc, "address": addr, "pref": pm.group(1) if pm else None,
            **{k: rec[k] for k in ("access", "hours", "closed", "bays", "parking")},
            "bays_num": int(bm.group(1)) if bm else None,
            "open_24h": "24時間" in (rec["hours"] or ""),
            "private_room": "個室" in (rec["bays"] or ""),
            "monthly_fee": fee_of(ls), "equipment": equip,
            **({"note": note} if note else {}),
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
    for k in ("address", "pref", "hours", "closed", "bays", "parking", "access", "monthly_fee", "equipment"):
        print(f"  {k}: {sum(1 for x in out if x.get(k))}/{len(out)}")
    for x in out[:3]:
        print("   ", x["name"], "|", x["pref"], "|", x["bays"], "|", x["hours"])


main()
