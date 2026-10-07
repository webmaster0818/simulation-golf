#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLUB19（人数限定の完全会員制・定額打ち放題のシミュレーションゴルフ）を公式サイトから取る。

公式 https://golf-club19.com/ は WordPress。店舗ごとに
  店舗TOP   /<slug>/            … 「◯名限定」「24時間営業」などの紹介文・設備の説明・FAQ
  料金      /menu[-店]/         … 月額と打席ごとの機材（「打席No.1 ▪️Sky-Trak導入」）
  アクセス  /access[-店]/       … <table> に 住所・交通・営業時間
の3ページに分かれている。住所・営業時間はアクセスページ、料金・打席はメニューページから取る。

⚠️ ページURLの接尾辞が店ごとに違う（新宿だけ無印、ほかは -nerima 等）。一覧ページは無いので
   STORES に固定で持つ。店が増えたらトップのメニュー（「◯◯店はこちら」）を見て足す。
⚠️ 月額は「月額¥9,980-」とだけあり、税込・税抜の別が無い。断定せず「記載なし」と書く。
⚠️ 板橋店は <title> が「板橋区TOP | CLUB19」で店名が入っていない。店名はトップのメニュー表記で固定する。
⚠️ 電話番号は全店で非公開（問い合わせはLINE・メール・Web予約）。
⚠️ 「120名限定の完全会員制」は入会できる人数の上限であって、宿泊者専用のような利用者の限定ではない。
   会員制の定額ジムと同じ扱いで掲載する（マイゴル・GREEGOL と同じ）。

  python3 scripts/collect_club19.py        # 取得して data/club19.json に書く
"""
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://golf-club19.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "CLUB19", "club19"

# (URL用slug, 店舗TOP, 料金ページ, アクセスページ, 店名)
# slug は公式URLのローマ字を使う。新宿だけ公式が「shinzyuku」（訓令式）なので、
# 市区町村ページ（/area/tokyo/shinjuku/）と同じヘボン式に直す。
STORES = [
    ("shinjuku-yamabuki", "/shinzyuku-yamabuki/", "/menu/", "/access/", "CLUB19 新宿店"),
    ("nerima-toyotama", "/nerima-toyotama/", "/menu-nerima/", "/access-nerima/", "CLUB19 練馬店"),
    ("itabashi", "/itabashi/", "/menu-itabashi/", "/access-itabashi/", "CLUB19 板橋店"),
    ("yamagata-miyamachi", "/yamagata-miyamachi/", "/menu-yamagata/", "/access-yamagata/", "CLUB19 山形宮町店"),
]

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")

# 公式が機材として名指ししているものだけ通す。表記はサイト内の既存の語にそろえる。
EQUIPMENT = [
    (r"Sky-?Trak", "SkyTrak"),
    (r"GOLFZON\s*VISION", "GOLFZON VISION"),
    (r"Xswing", "Xswing"),
    (r"GTRAK", "GTRAK"),
    (r"Joy\s*Golf\s*Range", "Joy Golf Range"),
]

# 公式サイトの記載どうしが食い違っている箇所（zipcloud で突き合わせた結果）。今のところ無し。
FIXES: dict[str, dict] = {}


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def strip_hidden(h: str) -> str:
    h = re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", "", h, flags=re.S)
    m = re.search(r"<main[^>]*>(.*?)</main>", h, re.S)
    return m.group(1) if m else h


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def table(h: str) -> dict:
    out = {}
    for m in re.finditer(r"<tr>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*</tr>", h, re.S):
        k = text(m.group(1))
        v = text(re.sub(r"<br\s*/?>", "／", m.group(2)))
        v = re.sub(r"\s*／\s*", "／", v).strip("／ ")
        if k and v and k not in out:
            out[k] = v
    return out


def main() -> None:
    today = date.today().isoformat()
    stores, problems = [], []
    for slug, top, menu, access, name in STORES:
        top_h = strip_hidden(get(BASE + top)); time.sleep(2)
        menu_h = strip_hidden(get(BASE + menu)); time.sleep(2)
        acc_h = strip_hidden(get(BASE + access)); time.sleep(2)
        if not (top_h and menu_h and acc_h):
            problems.append(f"{slug}: ページが取れなかった")
            continue
        top_t, menu_t = text(top_h), text(menu_h)
        tb = table(acc_h)
        addr = tb.get("住所", "")
        zipc = None
        mz = re.match(r"〒?\s*(\d{3})-?(\d{4})\s*／?\s*", addr)
        if mz:
            zipc = mz.group(1) + mz.group(2)
            addr = addr[mz.end():].strip()
        addr = addr.replace("／", " ")
        mp = re.match(rf"({PREFS})", addr)
        if not mp:
            problems.append(f"{slug}: 住所に都道府県が無い（{addr}）")

        hours = tb.get("営業時間")
        is24 = bool(hours and "24時間" in hours)
        if hours:
            hours = re.sub(r"(\d{1,2}:\d{2})\s*~\s*(\d{1,2}:\d{2})", r"\1〜\2", hours)
        closed = None
        if "年中無休" in top_t or "年中無休" in menu_t:
            closed = "年中無休"

        # 料金: 「月額¥9,980-」＋ 直後の条件（「24時間通い放題・打ち放題」）
        fee = None
        mf = re.search(r"月額\s*[¥￥]\s*([\d,]+)\s*-?\s*(.{0,30}?(?:通い放題|打ち放題)(?:・打ち放題)?)", menu_t)
        if mf:
            fee = f"月額{mf.group(1)}円（{mf.group(2).strip()}。税込・税抜の別は公式サイトに記載なし）"
        else:
            problems.append(f"{slug}: 月額が取れなかった")

        # 打席: 料金ページの「打席No.N」「打席No.1～3」から台数を数える
        nums = set()
        for m in re.finditer(r"打席No\.?\s*(\d+)(?:\s*[～〜~-]\s*(\d+))?", menu_t):
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
            nums.update(range(a, b + 1))
        bays_num = max(nums) if nums else None
        bays = None
        private = None
        if bays_num:
            extra = []
            if re.search(r"左打ち対応", menu_t):
                extra.append("左打ち対応打席あり")
            bays = f"{bays_num}打席" + (f"（{'・'.join(extra)}）" if extra else "")
        mb = re.search(r"完全プライベート仕様の(\d+)打席", top_t)
        if mb:
            bays_num = int(mb.group(1))
            bays = f"完全プライベート仕様の{bays_num}打席"
            private = True
        if not bays:
            problems.append(f"{slug}: 打席数が取れなかった")

        # 機材: 公式が名指ししているものだけ（店舗TOPと料金ページ）
        eq = []
        for pat, label in EQUIPMENT:
            if re.search(pat, top_t + " " + menu_t, re.I) and label not in eq:
                eq.append(label)

        # 駐車場: FAQ に「駐車場はありますか？」があればその答え。無ければ記載なし
        parking = None
        mp_ = re.search(r"駐車場はありますか？\s*(.+?。)", top_t)
        if mp_:
            parking = mp_.group(1)
        cap = re.search(r"(\d+)名限定", top_t)

        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": slug,
            "name": name,
            "pref": mp.group(1) if mp else None,
            "zip": zipc,
            "address": addr,
            "access": tb.get("交通"),
            "tel": None,
            "hours": hours,
            "open_24h": is24 if hours else None,
            "closed": closed,
            "bays": bays, "bays_num": bays_num,
            "private_room": private,
            "parking": parking,
            "monthly_fee": fee,
            "equipment": "／".join(eq) if eq else None,
            "open": True,
            "member_cap": f"{cap.group(1)}名限定の完全会員制" if cap else None,
            "official": BASE + top,
            "source_url": BASE + top, "fetched_at": today,
        })
        s = stores[-1]
        s.update(FIXES.get(slug, {}))
        print(f"  {s['name']} … {s['pref']} / {s['hours']} / {s['bays']} / {s['monthly_fee']} / {s['equipment']}", flush=True)

    out = DATA / "club19.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件 → {out}")
    for p in problems:
        print("  ⚠️", p)


if __name__ == "__main__":
    main()
