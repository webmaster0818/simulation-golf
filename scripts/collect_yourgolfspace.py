#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Your Golf Space（ユアゴルフスペース・水道橋の完全個室インドアゴルフ／運営 RPN合同会社）を公式サイトから取る。

公式は STUDIO（studio.design）製の SPA で、curl では本文が空（<title>YGS_LP だけ）。
ヘッドレス Chrome の --dump-dom で描画後の DOM を読む。
  https://yourgolfspace.jp/              … 現行の公式LP（特徴・料金（税込）・アクセス：住所/営業時間/最寄駅）
  https://yourgolfspace.studio.site/     … 同じ STUDIO の旧ページ（©2025 RPN合同会社）。アクセス欄に
                                           駐車場・定休日・打席、FAQ がある。.jp には無いのでここから補う
2026-10-16 時点で店舗は水道橋の1店だけ。

⚠️ 2つのページで料金の書き方が少し違う（ミッドナイトプラン: .jp「2:30〜5:30」／旧ページ「23:30~5:30」）。
   月額は現行の .jp の「レギュラープラン」だけを載せる。
⚠️ シミュレーターは「GOLFZONのシミュレーター」とだけあり機種名は無い。equipment は「GOLFZON」。
⚠️ 打席（部屋）数・郵便番号・店舗の電話番号は記載なし（電話番号は個人情報保護の窓口のものだけ）。
⚠️ 運営会社名は .jp には無く、旧ページのフッターとプライバシーポリシーに「RPN合同会社」。

  python3 scripts/collect_yourgolfspace.py      # 取得して data/yourgolfspace.json に書く
"""
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TOP = "https://yourgolfspace.jp/"
OLD = "https://yourgolfspace.studio.site/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND, BRAND_SLUG = "Your Golf Space", "yourgolfspace"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


def render(url: str) -> str:
    """描画後の DOM を行のリストにする（タグを落として空行を除く）。"""
    for _ in range(3):
        r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=15000",
                            f"--user-agent={UA}", "--dump-dom", url],
                           capture_output=True, text=True, timeout=120)
        h = re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", "", r.stdout or "", flags=re.S)
        t = html.unescape(re.sub(r"<[^>]+>", "\n", h))
        lines = [re.sub(r"\s+", " ", l).strip() for l in t.split("\n")]
        lines = [l for l in lines if l]
        if len(lines) > 50:
            return "\n".join(lines)
        time.sleep(3)
    return ""


def after(t: str, label: str, before: bool = False) -> str | None:
    """「値\\nラベル」（.jp）または「ラベル\\n値」（旧ページ）の値を取る。"""
    pat = rf"([^\n]+)\n{label}\n" if before else rf"\n{label}\n([^\n]+)"
    m = re.search(pat, t)
    return m.group(1).strip() if m else None


def main() -> None:
    today = date.today().isoformat()
    problems = []
    top = render(TOP)
    time.sleep(2)
    old = render(OLD)
    if not top:
        raise SystemExit("公式LPが描画できなかった")

    # 店舗: .jp のアクセス欄は「値\nラベル」の並び
    acc = top  # 「住所」「営業時間」「最寄駅」はアクセス欄にしか出ない（フッターにも「アクセス」の語があるので切り出さない）
    addr = after(acc, "住所", before=True)
    hours = after(acc, "営業時間", before=True)
    access = after(acc, "最寄駅", before=True)
    if not addr:
        raise SystemExit("住所が取れなかった")
    addr = re.sub(r"(\d)(SNT)", r"\1 \2", addr)  # 「2-17-9SNT水道橋ビル」→ 番地とビル名の間を空ける
    mpref = re.match(rf"({PREFS})", addr)
    if not mpref:
        problems.append(f"住所に都道府県が無い（{addr}）")
    mshop = re.search(r"Your Golf Spaceは、(\S+?駅)徒歩\d+分の完全個室インドアゴルフスタジオ", top)
    station = mshop.group(1) if mshop else None
    is24 = bool(hours and "24時間" in hours)
    closed = "年中無休" if hours and "年中無休" in hours else None

    # 料金（.jp・税込）: レギュラープラン
    fee = None
    mf = re.search(r"レギュラープラン\n一番人気\n([\d,]+)\n円/月（(税込|税抜)）\n([^\n]+)", top)
    if mf:
        cond = mf.group(3).replace("一番人気のスタンダードプラン。", "")
        fee = f"レギュラープラン 月額{mf.group(1)}円（{mf.group(2)}）。{cond}"
    else:
        problems.append("月額（レギュラープラン）が取れなかった")
    mvis = re.search(r"ビジター利用\n([\d,]+)円 / 回（(税込|税抜)）", top)
    if fee and mvis:
        fee += f"／ビジター利用 1回{mvis.group(1)}円（{mvis.group(2)}）"

    private = True if "完全個室" in top else None
    equipment = "GOLFZON" if re.search(r"GOLFZONのシミュレーター", top) else None

    # 旧ページ（同じ運営）から 駐車場・定休日・打席
    parking = bays = None
    old_ok = bool(old and "RPN合同会社" in old)
    if old_ok:
        oacc = old
        parking = after(oacc, "駐車場")
        bays = after(oacc, "打席")
        if bays == "右打席":
            bays = "右打席（打席数は記載なし）"  # 公式の表記は「打席 右打席」。「のみ」とは書いていない
        if not closed and after(oacc, "定休日") == "なし":
            closed = "定休日なし"
    else:
        problems.append("旧ページ（studio.site）が取れない・運営会社名が無い → 駐車場・打席は記載なしのまま")

    store = {
        "brand": BRAND, "brand_slug": BRAND_SLUG,
        "slug": "suidobashi",
        "name": BRAND,  # 1店だけで「◯◯店」の店名は無い。地名は slug にだけ付ける
        "pref": mpref.group(1) if mpref else None,
        "zip": None,
        "address": addr,
        "access": access,
        "tel": None,
        "hours": hours,
        "open_24h": is24 if hours else None,
        "closed": closed,
        "bays": bays, "bays_num": None,
        "private_room": private,
        "parking": parking,
        "monthly_fee": fee,
        "equipment": equipment,
        "open": True,
        "operator": "RPN合同会社" if old_ok else None,
        "official": TOP,
        "source_url": TOP, "fetched_at": today,
        "note": (f"駐車場・打席は同じ運営の旧ページ {OLD} の記載" if old_ok else None),
    }
    if station and station not in (access or ""):
        problems.append(f"紹介文の駅（{station}）と最寄駅欄（{access}）が合わない")
    print(f"  {store['name']} … {addr} / {hours} / {access} / {fee} / {parking} / {bays} / {equipment}")

    out = DATA / "yourgolfspace.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": [store]},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し 1件 → {out}")
    for p in problems:
        print("  ⚠️", p)


if __name__ == "__main__":
    main()
