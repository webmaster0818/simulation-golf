#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""インザゴルフ（九州のシミュレーションゴルフスクール）の店舗を公式サイトから取る。

店舗一覧 https://inthegolf.com/list/ に /list/<slug>/ のリンクが並ぶ。
店舗ページの <dt>/<dd> に 店舗名・住所・アクセス・駐車場・電話・利用時間が入っている。

⚠️ 同じ <dt> ラベルが1ページに何度も出る（料金プランごとに「利用」「内容」が繰り返される）。
   店舗情報は**最後に出てくる「店舗名」ブロック**にあるので、先勝ちで拾うと
   料金表の値を住所欄に入れてしまう。ラベルごとに「最後の値」を採る。
⚠️ 公式に書いていない項目は None のままにする。推測で埋めない。
   2026-10-16: 打席数・月額（料金表）・休業（「年末年始・夏季休暇あり」）は店舗ページ上部と料金表にある → page_facts。
   機種は FAQ が「GOLFZONを導入している店舗と、JoyGolf smart+を導入している店舗があります」で店ごとに分からない
   → 店舗ページに書いてある佐賀卸本町だけ。

  python3 scripts/collect_inthegolf.py            # 取得して data/inthegolf.json に書く
  python3 scripts/collect_inthegolf.py --limit 3  # 動作確認
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
BASE = "https://inthegolf.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "インザゴルフ", "inthegolf"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-s", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def rows_last(page_html: str) -> dict:
    """ラベルが重複するので「最後に出てきた値」を採る（店舗情報はページ末尾側にある）"""
    out = {}
    for m in re.finditer(r"<(dt|th)[^>]*>(.*?)</\1>\s*<(dd|td)[^>]*>(.*?)</\3>", page_html, re.S):
        k, v = text(m.group(2)), text(m.group(4))
        if k and v:
            out[k] = v
    return out


def page_lines(page_html: str) -> list[str]:
    h = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", page_html)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", h))
    return [x.strip() for x in t.split("\n") if x.strip()]


def page_facts(page_html: str) -> dict:
    """2026-10 のリニューアル後の店舗ページから 打席・個室・機種・月額・休業 を読む。
    ⚠️ 以前の collector は <dt>/<dd> の店舗情報欄しか見ておらず、ページ上部の「6打席・シミュレーター完備」
       や料金表を読んでいなかった（全23店で 打席・月額 が null になっていた）。"""
    L = page_lines(page_html)
    d: dict = {}
    # 打席: 「6打席・シミュレーター完備」「現在5打席・シミュレーター完備」「5打席＋個室2室・シミュレーター完備」
    for x in L:
        m = re.match(r"^(現在)?(\d+)打席(＋個室(\d+)室)?・シミュレーター完備$", x)
        if m:
            d["bays"] = x.replace("・シミュレーター完備", "")
            d["bays_num"] = int(m.group(2))
            if m.group(4):
                d["private_room"] = f"個室{m.group(4)}室"
            d["bays_quote"] = x
            break
    # LITE: 「2ルーム・2台設置」＋「周囲を気にしにくいプライベート空間で…」
    if "bays" not in d:
        for i, x in enumerate(L):
            m = re.match(r"^(\d+)ルーム・(\d+)台設置$", x)
            if m:
                d["bays"] = f"{m.group(1)}ルーム（シミュレーター{m.group(2)}台）"
                d["bays_num"] = int(m.group(1))
                d["bays_quote"] = x
                if i + 1 < len(L) and "プライベート空間" in L[i + 1]:
                    d["private_room"] = f"{m.group(1)}ルーム（プライベート空間）"
                    d["private_quote"] = f"{x} {L[i + 1]}"
                break
    # 機種: 店舗ページに書いている店だけ（佐賀卸本町「JoyGolf 5打席・GOLFZON 3打席」）。
    # FAQ は「GOLFZONを導入している店舗と、JoyGolf smart+を導入している店舗があります」＝店ごとには分からない。
    for x in L:
        m = re.search(r"JoyGolf\s*(\d+)打席・GOLFZON\s*(\d+)打席", x)
        if m:
            d["equipment"] = f"JoyGolf（{m.group(1)}打席）／GOLFZON（{m.group(2)}打席）"
            d["equipment_quote"] = m.group(0)
            break
    # 月額: 料金表の「プラン名／月額／金額／円／（税込…円）」の並び（レッスン店は◯◯会員、LITEは◯◯プラン）
    plans, seen = [], set()
    for i in range(len(L) - 4):
        if re.search(r"(会員|プラン)$", L[i]) and L[i + 1] == "月額" and re.match(r"^[\d,]+$", L[i + 2]) \
                and L[i + 3] == "円" and re.match(r"^（税込[\d,]+円）$", L[i + 4]):
            if L[i] not in seen:
                seen.add(L[i])
                plans.append(f"{L[i]} {L[i + 2]}円{L[i + 4]}")
    if plans:
        d["monthly_fee"] = "／".join(plans)
    # 休業: 料金表の利用時間に「年末年始・夏季休暇あり」と書く店がある
    if "年末年始・夏季休暇あり" in L:
        d["closed"] = "年末年始・夏季休暇あり"
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    listing = get(f"{BASE}/list/")
    paths = sorted({p for p in re.findall(r'href="(/list/[^"?#]+/)"', listing) if p != "/list/"})
    print(f"店舗ページ {len(paths)}件")

    today = date.today().isoformat()
    stores, skipped = [], []
    for i, path in enumerate(paths, 1):
        if a.limit and i > a.limit:
            break
        url = BASE + path
        h = get(url)
        r = rows_last(h)
        addr = r.get("住所")
        if not addr:
            skipped.append(path)
            continue
        zipc = None
        mz = re.match(r"〒?(\d{3})-?(\d{4})\s*", addr)
        if mz:
            zipc = mz.group(1) + mz.group(2)
            addr = addr[mz.end():].strip()
        mp = re.match(rf"({PREFS})", addr)
        hours = r.get("利用時間")
        pf = page_facts(h)
        fn = {}
        for k, q in (("bays", "bays_quote"), ("equipment", "equipment_quote"), ("private_room", "private_quote")):
            if pf.get(q):
                fn[k] = f"{url} 「{pf[q]}」"
        if pf.get("private_room") and "private_room" not in fn:
            fn["private_room"] = f"{url} 「{pf['bays_quote']}」"
        if pf.get("closed"):
            fn["closed"] = f"{url} 料金表の利用時間「年末年始・夏季休暇あり」"
        if pf.get("monthly_fee"):
            fn["monthly_fee"] = f"{url} 料金表（月額＋税込）"
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": path.strip("/").replace("list/", ""),
            "name": r.get("店舗名") or text((re.search(r"<title>(.*?)</title>", h, re.S) or ["", ""])[1]),
            "pref": mp.group(1) if mp else None,
            "zip": zipc,
            "address": addr,
            "access": r.get("アクセス"),
            "tel": r.get("電話"),
            "hours": hours,
            "open_24h": bool(hours and "24時間" in hours),
            "closed": r.get("定休日") or pf.get("closed"),
            "bays": pf.get("bays"), "bays_num": pf.get("bays_num"),
            "private_room": pf.get("private_room"),
            "parking": r.get("駐車場"),
            "monthly_fee": pf.get("monthly_fee"),
            "equipment": pf.get("equipment"),
            "open": True,
            "official": url,
            "source_url": url, "fetched_at": today,
            "field_notes": fn,
        })
        print(f"  {i:3}/{len(paths)} {stores[-1]['name'][:28]} … {stores[-1]['pref'] or '県不明'}")
        time.sleep(2)   # 公式サイトに負荷をかけない

    out = DATA / "inthegolf.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件 → {out}")
    nopref = [s["name"] for s in stores if not s["pref"]]
    if nopref:
        print("  ⚠️ 都道府県が取れなかった店:", nopref)
    if skipped:
        print("  ⚠️ 住所が無く除外:", skipped)


if __name__ == "__main__":
    main()
