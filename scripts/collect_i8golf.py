#!/usr/bin/env python3
"""i8 GOLF（i8golf.jp）の店舗を収集する。7店。

ステップゴルフと違い、こちらは**24時間の無人インドア練習場**でシミュレーションゴルフを打つ形。
公式FAQに「体験時にはスタッフによるシミュレーションゴルフの使い方の案内」とあり、業態は
このサイトの indoor と同じ。segment は 'indoor' にする。

⚠️ トップの店舗一覧には都道府県と市区町村までしか無い（「長野県下諏訪町」）。
   番地まで要るので各店舗ページを見る。店舗ページが別ドメインの店もある
   （i8golf-yokohama.com / niceshot-i8golf.com）。
"""
import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent.parent
TOP = "https://i8golf.jp/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

PREFS = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県",
         "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県",
         "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府",
         "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県",
         "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県",
         "鹿児島県", "沖縄県"]
# ⚠️ 「本文に出てくる最初の都道府県」を住所として拾ってはいけない。
#    豊橋店で、併設コラムの「愛知県新城市にある新城カントリー倶楽部も収録されており」を
#    住所として拾った（実測）。**「住所」ラベルの直後**だけを見る。
ADDR_LABELED = re.compile(r"(?:住所|所在地)\s*[:：]?\s*(〒?\s*\d{3}-?\d{4}\s*)?"
                          r"((?:" + "|".join(PREFS) + r"|横浜市|川崎市|名古屋市|大阪市|神戸市|札幌市)"
                          r"[^\s、。｜|]{3,44})")
BAYS = re.compile(r"打席数\s*([^\s]{1,18})")
PARK = re.compile(r"(無料駐車場|駐車場)\s*(あり[^\s]{0,12}|なし)")
CITY_PREF = {"横浜市": "神奈川県", "川崎市": "神奈川県", "名古屋市": "愛知県", "大阪市": "大阪府",
             "神戸市": "兵庫県", "札幌市": "北海道"}
TEL = re.compile(r"(0\d{1,4}-\d{1,4}-\d{3,4})")


def fetch(url, timeout=30):
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA, url],
                           capture_output=True, text=True, timeout=timeout + 10)
        return r.stdout or ""
    except Exception:
        return ""


def text_of(html):
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html)
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def store_links(html):
    """トップの店舗一覧から「店舗の詳細へ」のリンクを拾う。"""
    urls = []
    for m in re.finditer(r'href="([^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*店舗の詳細へ', html):
        urls.append(urljoin(TOP, m.group(1)))
    if not urls:  # 構造が変わったとき用のフォールバック
        for m in re.finditer(r'href="(https?://[^"]*(?:i8golf|niceshot)[^"]*)"', html):
            u = m.group(1)
            if re.search(r"/(column|feed|law|privacy|recruit|fc|company|support|flow|business)", u):
                continue
            urls.append(u)
    out = []
    for u in urls:
        if u not in out:
            out.append(u)
    return out


# 公式URLが店名を表していない店がある（i8-golf-fitness＝下諏訪店、別ドメインの戸塚2店）。
# 7店しかないので、地名のローマ字を表で持つ。日本語店名の機械音訳はこのサイトで失敗済み。
SLUG = {
    "https://i8golf.jp/i8-golf-fitness/": "shimosuwa",
    "https://i8golf.jp/i8golf-matsumoto/": "matsumoto",
    "https://i8golf-yokohama.com/": "totsuka-harajuku",
    "https://niceshot-i8golf.com/": "totsuka-risemall",
    "https://i8golf.jp/toyohashi/": "toyohashi",
    "https://i8golf.jp/toyama/": "toyama",
    "https://i8golf.jp/takasaki/": "takasaki",
}


def main():
    top = fetch(TOP)
    if len(top) < 20000:
        print("トップを取得できませんでした", file=sys.stderr)
        return 1
    links = store_links(top)
    print(f"店舗ページ {len(links)}件")

    out = []
    for u in links:
        h = fetch(u)
        t = text_of(h)
        name = ""
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        if m:
            # 「24時間インドアゴルフ練習場 i8 GOLF 松本店」のような形。｜以降の宣伝文は落とす
            name = re.split(r"[｜|]", text_of(m.group(1)))[0].strip()
        m = ADDR_LABELED.search(t)
        full = m.group(2).strip() if m else None
        zipcode = (m.group(1) or "").replace("〒", "").strip() if m else None
        if zipcode and "-" not in zipcode:
            zipcode = f"{zipcode[:3]}-{zipcode[3:]}"
        pref = None
        if full:
            pref = next((p for p in PREFS if full.startswith(p)), None) \
                or next((v for k, v in CITY_PREF.items() if full.startswith(k)), None)
        mb, mp = BAYS.search(t), PARK.search(t)
        rec = {
            "segment": "indoor",
            "slug": SLUG.get(u),
            "brand": "i8 GOLF",
            "brand_slug": "i8golf",
            "name": name or u,
            "pref": pref,
            # ⚠️ 〒無しの `\d{3}-\d{4}` は電話番号にも一致する
            #    （045-443-7090 → 443-7090 を郵便番号として拾っていた）。〒付きだけ採る。
            "zip": zipcode or None,
            "address": full,
            "tel": (TEL.search(t).group(1) if TEL.search(t) else None),
            "hours": "24時間" if "24時間" in t else None,
            "open_24h": "24時間" in t,
            "bays": mb.group(1) if mb else None,
            "parking": (mp.group(1) + mp.group(2)) if mp else None,
            "private_room": ("個室" in t) or None,
            "equipment": None,          # 機材名は公式に明示が無い。書かない
            "open": True,
            "official": u,
            "source_url": u,
            "fetched_at": date.today().isoformat(),
        }
        out.append(rec)
        print(f"  {rec['name'][:38]:<40} {rec['pref'] or '住所不明'}  {rec['address'] or ''}")
        time.sleep(0.5)

    p = ROOT / "data" / "i8golf.json"
    p.write_text(json.dumps({"generated_at": date.today().isoformat(),
                             "count": len(out), "stores": out}, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    miss = [x["name"] for x in out if not x["slug"]]
    if miss:
        print("  🚨 URLスラッグ未設定（SLUG表に追加する）:", miss)
    print(f"\n保存: {p} ({len(out)}店 / 住所を取れた {sum(1 for x in out if x['address'])}店)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
