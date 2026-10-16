#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DOOR TO GOLF（24時間・完全個室のインドアゴルフ）の店舗を公式サイトから取る。

店舗一覧は WordPress のカスタム投稿 `shop-post-newplan`。REST で店舗URLを列挙し、
各店舗ページの <dt>/<dd> から住所・アクセス・営業時間を読む。

⚠️ ACF は空を返すので REST だけでは住所が取れない。店舗ページのHTMLを見る必要がある。
⚠️ 403になるので実ブラウザのUAを付ける。
⚠️ 公式に書いていない項目は None のままにする。推測で埋めない。

2026-10-16 追加（「公式サイトに記載なし」と出ていたが、店舗ページに書いてあった）:
  - 機種: 店名の下の「GOLF SIMULATOR」の <ul><li>（「Trackman iO（トラックマンiO）」「SDR」「WAVE」…）。
  - 駐車場: 「設備情報 その他」のアイコン <h5>駐車場<br>2台</h5>。アイコンが無い店は書かない
    （FAQ「駐車場の有無は店舗HPよりご確認いただけます」＝無い＝「なし」とは言い切れない）。
    台数の無い「駐車場」だけのアイコン（天理）は「駐車場あり（台数の記載なし）」。
  - 月会費: 「料金プラン PRICE」の各プラン。<div class="original">（通常）→<div class="sale">（キャンペーン）の
    2段の店と sale だけの店がある。公式の表記どおり（税抜・税込）並べる。
    ⚠️ 豊田大林は original 10,000円→sale 12,000円のプランがある（公式どおり）。「→はキャンペーン」と書かない。
  - 電話: 店舗ページに店ごとの番号は無い。全ページ共通の「お問い合わせ」欄の Tel ボタン（tel:05031745136・
    受付 平日9:00～20:00／土日祝9:00～18:00）だけ。ブランドの問い合わせ窓口として載せる。
  - 個室: 公式トップの title「24時間完全個室｜インドアゴルフ…」・「自分のペースで個室ゴルフ」。ブランド全体の表記として true。
  - 定休日・打席数（部屋数）はどこにも書いていない → None のまま（24時間営業から年中無休を作らない）。

  python3 scripts/collect_doortogolf.py          # 取得して data/doortogolf.json に書く
  python3 scripts/collect_doortogolf.py --limit 3  # 動作確認
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
BASE = "https://doortogolf.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "DOOR TO GOLF", "doortogolf"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")

# 住所が市名から始まる店がある（「大阪市北区天神橋…」）。推測できる政令市だけを表にする。
# 表に無いものは補わない（当てずっぽうで県名を作らない）。他の収集スクリプトと同じ方針。
CITY_PREF = {"横浜市": "神奈川県", "川崎市": "神奈川県", "相模原市": "神奈川県",
             "名古屋市": "愛知県", "大阪市": "大阪府", "京都市": "京都府", "神戸市": "兵庫県",
             "札幌市": "北海道", "仙台市": "宮城県", "さいたま市": "埼玉県", "千葉市": "千葉県",
             "広島市": "広島県", "福岡市": "福岡県", "北九州市": "福岡県", "岡山市": "岡山県",
             "熊本市": "熊本県", "新潟市": "新潟県", "静岡市": "静岡県", "浜松市": "静岡県",
             "堺市": "大阪府"}


# 店舗ページはあるが、公式のどこにも開業（済・予定）の告知が無い店。営業中とも準備中とも書けないので載せない。
# 次回、トップページのお知らせに名前が出たら外す。
#   青葉台店・上小田井店（2026-10-12 保留）は 10/13 にお知らせ「続々新店舗オープン!」（10/07付）の
#   「オープン予定日」を読めるようにして準備中で載せた。HOLD から外した。
HOLD: dict[str, str] = {}


def pref_of(addr: str):
    m = re.match(rf"({PREFS})", addr)
    if m:
        return m.group(1)
    for city, pref in CITY_PREF.items():
        if addr.startswith(city):
            return pref
    return None


def get(url: str) -> str:
    # ⚠️ 空で返ってくることがある。1回で諦めると店舗が黙って落ちる（実際に4店落ちた）
    for attempt in range(3):
        r = subprocess.run(["curl", "-s", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return r.stdout or ""


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def rows(page_html: str) -> dict:
    out = {}
    for m in re.finditer(r"<(dt|th)[^>]*>(.*?)</\1>\s*<(dd|td)[^>]*>(.*?)</\3>", page_html, re.S):
        k, v = text(m.group(2)), text(m.group(4))
        if k and v and k not in out:
            out[k] = v
    return out


def simulators(h: str):
    m = re.search(r"<p>GOLF SIMULATOR</p>\s*<ul>(.*?)</ul>", h, re.S)
    names = [text(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", m.group(1), re.S)] if m else []
    return "／".join(n for n in names if n) or None


def parking(h: str):
    for x in re.findall(r"<h5[^>]*>(.*?)</h5>", h, re.S):
        v = text(x)
        if v.startswith("駐車場"):
            rest = v[len("駐車場"):].strip()
            return f"駐車場 {rest}" if rest else "駐車場あり（台数の記載なし）"
    return None


def plans(h: str):
    """料金プランを「プラン名 月額…(税抜)→…(税抜)・税込…」で並べる。"""
    out = []
    for m in re.finditer(r"<li>\s*<h4>(.*?)</h4>\s*<div class=\"main\">(.*?)</div>\s*<div class=\"foot\">", h, re.S):
        name = re.sub(r"\s+", "", text(m.group(1)))
        body = m.group(2)
        def price(cls):
            pm = re.search(rf'<div class="{cls}">(.*?)</div>', body, re.S)
            if not pm:
                return None, None
            ps = [text(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", pm.group(1), re.S)]
            main_ = re.sub(r"\s+", "", ps[0]).replace("月額", "") if ps else None
            tax = next((p.replace(" ", "") for p in ps[1:] if "税込" in p), None)
            return main_, tax
        orig, _ = price("original")
        sale, tax = price("sale")
        if not sale:
            continue
        v = f"{name} 月額{orig}→{sale}" if orig else f"{name} 月額{sale}"
        out.append(v + (f"・{tax}" if tax else ""))
    if not out:
        return None
    note = "（「A→B」は公式の料金欄の2段表記どおり。Bが現在の表示価格）" if "→" in "".join(out) else ""
    return "／".join(out) + note


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    posts, page = [], 1
    while True:
        raw = get(f"{BASE}/wp-json/wp/v2/shop-post-newplan?per_page=100&page={page}")
        try:
            batch = json.loads(raw)
        except Exception:
            break
        if not isinstance(batch, list) or not batch:
            break
        posts += batch
        if len(batch) < 100:
            break
        page += 1
    print(f"店舗投稿 {len(posts)}件")

    today = date.today().isoformat()
    # ⚠️ 店舗ページは開業前から普通の店舗ページとして公開される（土浦駅東店・2026-10-12）。
    #    開業予定はトップページの「【店名】10月16日 OPEN予定」にしか書かれていないので、ここを読む。
    #    「予定」の付いた店は準備中にする（日付が過ぎても「予定」のままなら準備中のまま＝判断待ちの扱いに合わせる）。
    top = re.sub(r"<[^>]+>", "\n", get(BASE + "/"))
    planned = {m.group(1): m.group(0).strip() for m in re.finditer(
        r"【([^】]+)】\s*(\d{1,2})月(\d{1,2})日\s*(?:OPEN|オープン)予定", top)}
    # ⚠️ 複数店をまとめた告知は「店名 場所：… オープン予定日：11月25日」の形でお知らせ本文にだけ出る
    #    （「続々新店舗オープン!」2026-10-07 の青葉台・上小田井・弁天町・十日市場）。トップには載らない。
    try:
        news = json.loads(get(f"{BASE}/wp-json/wp/v2/posts?per_page=20&_fields=title,content,link,date"))
    except Exception:
        news = []
    for n in news if isinstance(news, list) else []:
        body = text(n.get("content", {}).get("rendered", ""))
        title = text(n.get("title", {}).get("rendered", ""))
        for m in re.finditer(r"(\S+店)\s*場所：\s*\S+\s*オープン予定日：\s*(\d{1,2})月(\d{1,2})日", body):
            planned.setdefault(m.group(1), f"お知らせ「{title}」（{n.get('date', '')[:10]}）: "
                                            f"{m.group(1)} オープン予定日：{m.group(2)}月{m.group(3)}日")
    print("開業予定:", planned)
    # 店舗ページ共通の「お問い合わせ」欄（店ごとの電話番号は無い）
    tm = re.search(r'href="tel:(\d+)"', get(BASE + "/"))
    tel = None
    if tm:
        d = tm.group(1)
        tel = f"{d[:3]}-{d[3:7]}-{d[7:]}（DOOR TO GOLF お問い合わせ窓口・受付 平日9:00～20:00／土日祝9:00～18:00）"
    stores, skipped = [], []
    for i, p in enumerate(posts, 1):
        if a.limit and i > a.limit:
            break
        name = text(p.get("title", {}).get("rendered", ""))
        url = p.get("link")
        if not name or not url:
            continue
        if name in HOLD:
            skipped.append(f"{name}（保留: {HOLD[name]}）")
            continue
        h = get(url)
        r = rows(h)
        addr = r.get("住所")
        if not addr:
            skipped.append(name)
            continue
        hours = r.get("営業時間")
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": p.get("slug"),
            "name": name,
            "pref": pref_of(addr),
            "zip": None,
            "address": addr,
            "access": r.get("アクセス"),
            "tel": r.get("電話番号") or r.get("TEL") or (tel if tm and f'tel:{tm.group(1)}' in h else None),
            "hours": hours,
            # 「24時間」とだけ書いてある店が多い。文言どおりに判定する
            "open_24h": bool(hours and "24時間" in hours),
            "closed": r.get("定休日"),
            # 打席数（部屋数）は店舗ページに出ていない。推測で埋めない
            "bays": r.get("打席数"), "bays_num": None,
            "private_room": True,
            "private_room_note": "公式トップ title「24時間完全個室｜インドアゴルフ」（https://doortogolf.com/）",
            "parking": r.get("駐車場") or parking(h),
            "monthly_fee": plans(h),
            "equipment": simulators(h),
            "open": name not in planned,
            **({"note": planned[name]} if name in planned else {}),
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        print(f"  {i:3}/{len(posts)} {name} … {stores[-1]['pref'] or '県不明'}")
        time.sleep(2)   # 公式サイトに負荷をかけない

    out = DATA / "doortogolf.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    nopref = [s["name"] for s in stores if not s["pref"]]
    print(f"\n書き出し {len(stores)}件 → {out}")
    if nopref:
        print("  ⚠️ 都道府県が取れなかった店:", nopref)
    if skipped:
        print("  ⚠️ 住所が無く除外した店:", skipped)


if __name__ == "__main__":
    main()
