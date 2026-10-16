#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZEN GOLF RANGE（ゼンゴルフレンジ）の店舗を公式サイトから取る。

店舗一覧 https://zengolf.jp/location/ に店舗ページへのリンクが並んでいる。
店舗ページは直下のスラッグ（/ageo/ など）で、各ページの <dt>/<dd> に
住所・営業時間・電話番号・駐車場・月会費が入っている。

⚠️ 一覧には /column/ /faq/ などの非店舗ページも混ざる。URLで弾いたうえで、
   最後は「住所の行があるか」で判定する（名前で弾くと新しい固定ページを取りこぼす）。
⚠️ 公式に書いていない項目は None のままにする。推測で埋めない。

2026-10-16 追加（「公式サイトに記載なし」が実際は店舗ページに書いてあった）:
  - 打席数・機種名は店舗トップのメインビジュアル（div.kv_text）に出ている（「6打席」「8打席（GDR 6打席 / X-SWING 2打席）」
    ＋機種ロゴ画像 alt「シミュレーター GDR」）。⚠️ 店によって CSS で kv_text の画像を隠している
    （春日 ACADEMY は全部・尾久は「シミュレーター X-GOLF」だけ）。隠されたロゴは画面に出ないので使わない。
    機種名は店舗の /simulator/ ページの本文（「GolfzonGDRは…」「「GOLFZON WAVE」は…」「「SKYTRAK」の最新モデル「STMAX」」）
    と突き合わせ、本文に出てこない機種は採らない。
  - アクセスの見出しは「電車で<br>お越しの方」。タグを空白にすると「電車で お越しの方」になり一致しなかった。
    見出しは空白を詰めて比べる。表に電車の行が無い店（大森）は kv_text の「…駅…徒歩…」を使う。
  - 定休日は営業時間の文中（「定休日：月曜日」）。「なし」だけでなく何でも拾う。

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
        # 「電車で<br>お越しの方」→ 空白を詰めて「電車でお越しの方」
        k, v = re.sub(r"\s+", "", text(m.group(2))), text(m.group(4))
        if k and v and k not in out:
            out[k] = v
    return out


# 店舗ページのロゴ alt → （表示名, /simulator/ ページ本文で確かめる語）
SIMULATORS = {
    "GDR": ("GOLFZON GDR", "GDR"),
    "GDR Plus": ("GOLFZON GDR Plus", "GDR Plus"),
    "GZ Wave": ("GOLFZON WAVE", "GOLFZON WAVE"),
    "X-GOLF": ("X-GOLF", "X-GOLF"),
    "ST MAX": ("SKYTRAK ST MAX", "STMAX"),
}


def hidden_kv_alts(page_html: str):
    """CSS で隠されている kv_text の画像。None=全部隠れている。"""
    hid = set()
    for m in re.finditer(r"\.kv_text img(\[alt=\"([^\"]*)\"\])?\s*\{\s*display:\s*none", page_html):
        if not m.group(1):
            return None
        hid.add(m.group(2))
    return hid


def kv_info(page_html: str, sim_text: str) -> dict:
    """メインビジュアルの文言（打席数・駅・機種）を読む。"""
    m = re.search(r'<div class="kv_text">(.*?)</div>', page_html, re.S)
    if not m:
        return {}
    spans = [text(x) for x in re.findall(r"<span[^>]*>(.*?)</span>", m.group(1), re.S)]
    out = {"spans": spans}
    for sp in spans:
        bm = re.match(r"(\d+)打席(.*)$", sp)
        if bm:
            out["bays"], out["bays_num"] = sp, int(bm.group(1))
    hid = hidden_kv_alts(page_html)
    equip = []
    # 画面に文字で出ている機材（春日 ACADEMY「スイング解析機 GOLF VISION」「⾼精度弾道計測器GTRAK」）
    for sp in spans:
        em = re.match(r"(スイング解析機|[⾼高]精度弾道計測器)\s*([A-Za-z][A-Za-z0-9 \-]+)$", sp)
        if em:
            equip.append(f"{em.group(2).strip()}（{em.group(1).replace('⾼', '高')}）")
    if not equip and hid is not None:
        for alt in re.findall(r'<img[^>]*alt="([^"]*)"', m.group(1)):
            if alt in hid:
                continue
            name = alt.replace("シミュレーター", "").strip()
            if name in SIMULATORS and SIMULATORS[name][1] in sim_text:
                equip.append(SIMULATORS[name][0])
            elif name:
                print(f"    ⚠️ 見覚えのない機種 / 本文で確かめられない: {alt}")
    # 「8打席（GDR 6打席 / X-SWING 2打席）」の内訳にだけ出る機種
    for nm in re.findall(r"([A-Za-z][A-Za-z\-]+)\s*\d+打席", out.get("bays", "") or ""):
        if nm not in ("GDR",) and nm not in " ".join(equip):
            equip.append(nm)
    if equip:
        out["equipment"] = "／".join(equip)
    st = [sp for sp in spans if "駅" in sp and re.search(r"徒歩|バス|分", sp)]
    if st:
        out["station"] = " ".join(st)
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
        # 機種の裏取り: /simulator/ ページの本文＋店舗トップの Simulator 欄（ロゴ画像の alt を含む）。
        # ACADEMY の多くは /simulator/ ページが無い（空が返る）ので店舗トップの欄で確かめる。
        sim_html = get(url + "simulator/")
        sec = re.search(r'<section id="simulator".*?</section>', h, re.S)
        sec_html = sec.group(0) if sec else ""
        sim_text = " ".join([
            text(re.sub(r"<script.*?</script>|<style.*?</style>", "", sim_html, flags=re.S)),
            text(sec_html), " ".join(re.findall(r'alt="([^"]*)"', sec_html))])
        kv = kv_info(h, sim_text)
        hours = r.get("営業時間")
        # 2026-10-16: 全店の営業時間の末尾に「2026/11/1からの新時間割は こちら」（別ページへのリンク）が付いた。
        # リンク文言なのでページには出さない。吉川は公式の「定休日：月曜日し」の打ち間違いをそのまま拾うので直す。
        if hours:
            hours = re.sub(r"\s*\d{4}/\d{1,2}/\d{1,2}からの新時間割は\s*こちら\s*$", "", hours)
            hours = hours.replace("月曜日し", "月曜日")
        parking = r.get("駐車場")
        # 春日部は公式の駐車場欄が「駐車場<br>V」（末尾の V は打ち間違い）
        if parking:
            parking = re.sub(r"\s+[A-Za-z]$", "", parking)
        # 店舗ページのスラッグをそのままURLに使う（/academy/ 付きは親を使う）
        slug = re.sub(r"/academy$", "", url.replace(BASE, "").strip("/"))
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": slug.replace("/", "-"),
            "name": name,
            "pref": pref_of(addr),
            "zip": None,
            "address": addr,
            "access": r.get("電車でお越しの方") or kv.get("station"),
            "tel": r.get("電話番号"),
            "hours": hours,
            "open_24h": bool(hours and "24時間" in hours),
            # 「定休日：なし」が営業時間の文中に入っている
            "closed": r.get("定休日") or (lambda cm: cm.group(1).strip() if cm else None)(
                re.search(r"定休日[：:]\s*(\S+)", hours or "")),
            "bays": kv.get("bays"), "bays_num": kv.get("bays_num"),
            "private_room": None,
            "parking": parking,
            "monthly_fee": r.get("月会費"),
            "equipment": kv.get("equipment"),
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
