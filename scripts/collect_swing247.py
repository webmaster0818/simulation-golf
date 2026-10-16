#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SWING24/7 の店舗データを公式の店舗一覧から取る。

一覧ページ1枚に全店舗が載っている。1店舗は <li> 1つで、
  <h3>店名 → (スケジュール span) → 住所 p.txt_l → 経路 p.icon.root → 駐車場 p.icon.parking → 電話 → リンク
の順。住所・経路は <br> で2行に割れている店舗がある。

⚠️ 「近日オープン予定」の店舗は open=False で持ち、掲載時に既存店と混ぜない。
   オープン前を営業中として数えるのは、利用者にとって実害のある誤りになる。
"""
import argparse
import html
import json
import re
import subprocess
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://swing24.co.jp/locations"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")
TEL = re.compile(r"^0\d{1,4}-\d{1,4}-\d{3,4}$")
# 住所行かどうかの判定。都道府県で始まらない表記があるため、市区町村＋数字でも拾う。
ADDR = re.compile(r"[市区町村]")
# 都道府県が省略された住所の補完（政令市など、市名で一意に定まるものだけ）
CITY_PREF = {"名古屋市": "愛知県", "札幌市": "北海道", "仙台市": "宮城県", "横浜市": "神奈川県",
             "川崎市": "神奈川県", "京都市": "京都府", "大阪市": "大阪府", "神戸市": "兵庫県",
             "広島市": "広島県", "福岡市": "福岡県", "北九州市": "福岡県", "さいたま市": "埼玉県",
             "千葉市": "千葉県", "新潟市": "新潟県", "静岡市": "静岡県", "浜松市": "静岡県",
             "堺市": "大阪府", "岡山市": "岡山県", "熊本市": "熊本県", "相模原市": "神奈川県"}


def text(fragment: str) -> list:
    """タグを外して <br> ごとの行に分ける。"""
    t = re.sub(r"<br\s*/?>", "\n", fragment)
    t = re.sub(r"<[^>]+>", "", t).replace("&nbsp;", " ")
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip() for v in t.split("\n")) if x]


def field(block: str, cls: str) -> list:
    m = re.search(rf'<(?:p|span|a)[^>]*class="{cls}"[^>]*>([\s\S]*?)</(?:p|span|a)>', block)
    return text(m.group(1)) if m else []


def curl(url: str) -> str:
    return subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                          capture_output=True, text=True).stdout


# 店舗サイトの開業告知。「10/3（土）グランドオープン！」のように日付＋オープンが言い切りで書かれたものだけ。
# ⚠️ 「…OPENいたします！」（能見台店・開業前の告知）・「プレオープン」・「OPEN予定」は開業の確認にしない。
OPENED = re.compile(r"(?<!\d)(\d{1,2})[/月](\d{1,2})日?\s*(?:[（(].[)）])?\s*グランド(?:オープン|OPEN)(?!予定)")


def opened_on_store_site(site: str, today: date) -> str | None:
    """一覧の「近日オープン予定」欄は開業後もしばらく残る（町田店・10/3開業→10/11も予定のまま）。
    店舗ごとの公式サイトに開業済みの日付が言い切りで書かれていれば、その文を返す。"""
    if not site:
        return None
    body = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", curl(site))
    for line in text(re.sub(r"<(?!br)[^>]+>", "\n", body)):
        m = OPENED.search(line)
        if m and (today.month, today.day) >= (int(m.group(1)), int(m.group(2))):
            return line
    return None


def opened_on_feed(page: str, name: str, note: str | None) -> str | None:
    """一覧ページに埋め込まれた公式インスタの投稿（Smash Balloon の sbi_item）で開業を確かめる。
    町田店（10/3投稿）・能見台店（10/10投稿）とも「⛳️swing24/7◯◯店⛳️ オープン⛳️」の言い切り。
    ⚠️ 予定日の書かれていない店（江古田「今夏」）は使わない。投稿日が一覧の予定日より前なら使わない
       （開業前の予告と区別できないため）。予定・プレの付いた文も使わない。"""
    plan = re.search(r"(\d{1,2})月(\d{1,2})日", note or "")
    if not plan:
        return None
    short = name.replace("SWING24/7", "").strip()
    jst = timezone(timedelta(hours=9))
    for item in re.split(r'<div class="sbi_item ', page)[1:]:
        d = re.search(r'data-date="(\d+)"', item)
        s = re.search(r'class="sbi-screenreader">([^<]*)', item)
        if not d or not s:
            continue
        cap = re.sub(r"\s+", " ", s.group(1))
        if not re.match(rf"⛳️\s*swing24/7\s*{re.escape(short)}⛳️\s*オープン⛳️", cap, re.I):
            continue
        if re.search(r"予定|プレ", cap):
            continue
        posted = datetime.fromtimestamp(int(d.group(1)), jst).date()
        if (posted.month, posted.day) >= (int(plan.group(1)), int(plan.group(2))) and posted.year >= 2026:
            return f"{posted.isoformat()} 投稿「{cap.strip()}」"
    return None


# ---------------------------------------------------------------------------
# 店舗ごとの公式サイト（一覧の「WEBサイト」）から 定休日・打席数・月会費 を読む（2026-10-16 追加）。
# 一覧（swing24.co.jp/locations）には住所・経路・駐車場・電話しか無い。月会費は公式の入会案内
# （swing24.co.jp/flow）に「店舗により費用や支払方法が異なります」とあり、店舗サイトにしか書かれていない。
# 店舗サイトはフランチャイズごとに作りが違う（swing24-◯◯.com 型・swing24-7.jp/studio/*.php 型・
# Wix の swing247.jp 型・swing247-golf.jp 型 など）。
# ⚠️ 機種名（GOLFZON 等）は本部サイト・全店舗サイトとも書かれていない（「最新シミュレーター完備」
#    「最新シミュレータを全打席に設置！」だけ）。本部FCページも「メーカー工場とタイアップで開発」のみ。
#    → equipment は None のまま。
# ⚠️ 希望ヶ丘・宇都宮・今里 は料金が画像（price.webp / campaign_price_*.png / price_*.svg）だけで、
#    本文に金額が無い → monthly_fee は None（画像の数字は読まない）。
# ⚠️ 本文の「会員様同士であっても1打席を…」「左打席は1打席ご用意」は打席数ではない。打席数として
#    書かれた形（打席数 3打席／打席数は4打席です／全打席(4打席)／4打席全てに）だけ拾う。
FEE_MAIN = re.compile(r"^(会費[(（]月額[)）]|月額会費|月会費|月額費用|個人向け会費[(（]月額プラン[)）]|レディース割引[(（]月額[)）])$")
FEE_PLAN = re.compile(r"^[^¥￥※（(、。]{1,16}(プラン|会員)$")
FEE_STOP = re.compile(r"入会金|手数料|ロッカー|カード代|体験|レッスン")
FEE_SKIP = re.compile(r"法人|同伴|ゲスト|ロッカー|レッスン|[0-9０-９]+\s*[ヶヵケか]月|半年|年契約|集中")
AMOUNT = re.compile(
    r"^(?=[¥￥]|[\d,]+\s*円)[¥￥]?\s*([\d,]{3,})\s*(?:円)?\s*(?:/月)?\s*"
    r"(?:[（(]\s*(税込|税抜|税別)(?:み)?\s*(?:[¥￥]?\s*([\d,]+)\s*(?:円)?)?\s*(?:/月)?(?:[・、][^)）]*)?\s*[)）])?")
OPEN365 = re.compile(r"年中無休|24時間\s*365日|365日\s*24時間|365日\s*/\s*24時間")
BAYS = [re.compile(p) for p in (
    r"打席数は\s*(\d+)\s*打席", r"全打席\s*[（(]\s*(\d+)\s*打席\s*[)）]", r"シミュレーションゴルフ\s*[（(]\s*(\d+)\s*打席\s*[)）]",
    r"(\d+)\s*打席全てに", r"全\s*(\d+)\s*打席")]
CACHE = Path("/tmp/swing247-sites")


def site_lines(h: str) -> list:
    h = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<!--[\s\S]*?-->", "", h)
    h = re.sub(r"<br\s*/?>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", h))
    t = t.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    return [x for x in (re.sub(r"[ \t　⁡]+", " ", v).strip() for v in t.split("\n")) if x]


def cached(url: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", url)[:150] + ".html")
    if fp.exists() and fp.stat().st_size > 2000:
        return fp.read_text(encoding="utf-8", errors="ignore")
    h = curl(url)
    fp.write_text(h, encoding="utf-8")
    time.sleep(1.5)   # 店舗サイトに負荷をかけない
    return h


def amount_text(vals: list, all_tax: str | None) -> str | None:
    """ラベルの次の1〜4行をつないで「¥13,200 (税込)」「12,000円（税込13,200円）」「11,000 円(税込み)」を読む。"""
    s = " ".join(vals).replace(" 円", "円").replace("円 (", "円(").replace("円 （", "円（")
    s = re.sub(r"([\d,])\s+(円)", r"\1\2", s)
    s = re.sub(r"(\d)\s+([（(]税)", r"\1\2", s)
    m = AMOUNT.match(s)
    if not m:
        return None
    base, tax, incl = m.group(1), m.group(2), m.group(3)
    if tax and incl:
        return f"{base}円（{tax}{incl}円）"
    if tax:
        return f"{base}円（{tax}）"
    return f"{base}円（{all_tax}）" if all_tax else f"{base}円"


def site_fee(L: list) -> str | None:
    all_tax = None
    for x in L:
        if re.search(r"価格は(?:すべて|全て)税込", x):
            all_tax = "税込"
        elif re.search(r"価格は(?:すべて|全て)税(?:別|抜)", x):
            all_tax = "税別"
    # swing24-7.jp/studio/*.php 型: 「入会金 / 月額費用 / レンタルロッカー」の見出しが並び、そのあと同じ順で金額
    for i, x in enumerate(L):
        if x == "月額費用":
            k = i
            while k > 0 and not re.search(r"\d", L[k - 1]) and len(L[k - 1]) <= 12:
                k -= 1
            heads = []
            j = k
            while j < len(L) and not re.search(r"\d", L[j]):
                heads.append(L[j]); j += 1
            # 値は見出しと同じ数だけ並ぶ（「準備中」「なし」のように金額でない値もある）
            vals = L[j:j + len(heads)]
            v = vals[heads.index("月額費用")] if len(vals) == len(heads) else None
            if v and re.fullmatch(r"[\d,]+円", v):
                return f"月額費用 {v}（{all_tax}）" if all_tax else f"月額費用 {v}"
            return None
    out, seen = [], set()
    for i, x in enumerate(L):
        main = FEE_MAIN.match(x)
        plan = FEE_PLAN.match(x) and not FEE_SKIP.search(x)
        if not (main or plan):
            continue
        nxt = []
        for y in L[i + 1:i + 6]:
            if FEE_MAIN.match(y) or FEE_PLAN.match(y) or FEE_STOP.search(y):
                break
            nxt.append(y)
        # 説明行（「平日10:00〜16:00利用」「24時間365日ご利用可能で」）を飛ばして最初の金額を読む
        v = None
        for k in range(len(nxt)):
            v = amount_text(nxt[k:k + 3], all_tax)
            if v:
                break
            if re.search(r"[¥￥]|\d{1,3},\d{3}", nxt[k]):
                break
        if v and (x, v) not in seen:
            seen.add((x, v))
            out.append(f"{x} {v}")
    return "／".join(out) if out else None


def site_info(site: str | None) -> dict:
    """店舗サイトのトップ（＋同じサイト内の equipment/fee/access ページ）から読む。"""
    r = {"closed": None, "bays": None, "bays_num": None, "monthly_fee": None, "src": {}}
    if not site:
        return r
    top = cached(site)
    pages = [(site, top)]
    host = re.match(r"https?://[^/]+", site).group(0)
    for sub in sorted(set(re.findall(rf'href="({re.escape(host)}/(?:equipment|fee|price|access)/?)"', top))):
        pages.append((sub, cached(sub)))
    for url, h in pages:
        L = site_lines(h)
        if not r["closed"]:
            # 店舗概要の「営業日時」欄を優先、無ければ本文の「24時間365日営業」等
            row = next((L[i + 1] for i in range(len(L) - 1) if L[i] == "営業日時" and OPEN365.search(L[i + 1])), None)
            hit = row or next((m.group(0) for x in L if (m := re.search(
                r"年中無休[^。]{0,10}|(?:24時間\s*365日|365日\s*24時間)(?:営業|ご利用可能|利用可能)", x))), None)
            if hit:
                r["closed"] = "年中無休（365日営業）"
                r["src"]["closed"] = f"{url}「{hit.strip()}」"
        if not r["bays"]:
            row = next((L[i + 1] for i in range(len(L) - 1) if L[i] == "打席数" and re.fullmatch(r"\d+打席", L[i + 1])), None)
            n = int(row[:-2]) if row else None
            if n is None:
                for x in L:
                    m = next((m for p in BAYS if (m := p.search(x))), None)
                    if m:
                        n, row = int(m.group(1)), m.group(0)
                        break
            if n:
                r["bays"], r["bays_num"] = f"{n}打席", n
                r["src"]["bays"] = f"{url}「{row}」"
        if not r["monthly_fee"] and url == site:
            f = site_fee(L)
            if f:
                r["monthly_fee"] = f
                r["src"]["monthly_fee"] = url
    return r


def parse(block: str) -> dict:
    """1店舗の <li>。公式の HTML は 住所(txt_l)・経路(icon root)・駐車場(icon parking)・
    電話(icon tel)・スケジュール(span) が欄ごとに分かれているので、欄で拾う。

    ⚠️ 以前は行の中身（駅・徒歩・〒…）で欄を推測していて、経路欄の2行目
       「その他交通機関情報に関しましてはWEBサイトにて」が住所の末尾に付いていた
       （ミロクジーナ藤沢店・2026-10-11 修正）。駐車場欄の「無し」も同じ原因（鮫洲店・10-10）。
    """
    addr = field(block, "txt_l")
    zipc = next((v.lstrip("〒") for v in addr if re.fullmatch(r"〒\d{3}-?\d{4}", v)), None)
    address = "".join(v for v in addr if not v.startswith("〒"))
    sched = re.search(r"<!--スケジュール-->\s*<span>([\s\S]*?)</span>", block)
    note = " ".join(text(sched.group(1))) if sched else None
    tel = " ".join(field(block, "icon tel")) or None
    site = re.search(r'<a href="([^"]+)" class="site"', block)
    m = re.search(f"({PREF})", address)
    return {
        "zip": zipc, "address": address,
        "pref": m.group(1) if m else next((p for c, p in CITY_PREF.items() if c in address), None),
        # 愛知・福岡の店は経路欄の1行目が見出しの「アクセス」だけ。
        # 「その他交通機関情報に関しましてはWEBサイトにて」（藤沢）は公式サイト内の案内で、
        # このサイトに載せると「どのWEBサイト？」になるので落とす。
        "access": " / ".join(v for v in field(block, "icon root")
                             if v != "アクセス" and not re.search(r"WEBサイトにて", v)) or None,
        "parking": " ".join(field(block, "icon parking")) or None,
        "tel": tel if tel and TEL.fullmatch(tel) else None,
        # ⚠️ 「近日オープン予定」の欄（スケジュール）がある店は open=False。
        "open": not note, "note": note,
        "site": site.group(1) if site else None,
    }


def main() -> None:
    global CACHE
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(CACHE),
                    help="店舗サイトのキャッシュ。古いと料金の変更を拾えないので、取り直すときは新しいディレクトリを渡す")
    CACHE = Path(ap.parse_args().cache)
    page = curl(URL)
    today, out = date.today(), []
    for name, block in re.findall(r"<h3>(SWING24/7[^<]*店)</h3>([\s\S]*?)</li>", page):
        r = parse(block)
        rec = {
            "brand": "SWING24/7", "brand_slug": "swing247", "name": name.strip(),
            **{k: r[k] for k in ("zip", "address", "pref", "parking", "tel", "open", "note")},
            "access": r["access"],
            # 公式が全店「24時間365日・無人」と明記しているブランド
            "hours": "24時間365日（無人運営）", "open_24h": True,
            "source_url": URL, "fetched_at": today.isoformat(),
        }
        # 店舗サイトから 定休日・打席数・月会費。機種名はどこにも書かれていないので None。
        si = site_info(r["site"])
        rec.update(closed=si["closed"], bays=si["bays"], bays_num=si["bays_num"],
                   monthly_fee=si["monthly_fee"], equipment=None, official=r["site"])
        if si["src"]:
            rec["field_sources"] = si["src"]
        if not r["open"]:
            said = opened_on_store_site(r["site"], today)
            if said:
                rec.update(open=True, open_source_url=r["site"],
                           note=f"一覧は「{r['note']}」のまま。店舗公式サイトに「{said}」")
            else:
                feed = opened_on_feed(page, rec["name"], r["note"])
                if feed:
                    rec.update(open=True, open_source_url=URL,
                               note=f"一覧の予定欄は「{r['note']}」のまま。同じ一覧ページの公式インスタ欄に {feed}")
        out.append(rec)

    res = list({x["name"]: x for x in out}.values())
    (ROOT / "data" / "brand-swing247.json").write_text(
        json.dumps({"brand": "SWING24/7", "source_url": URL, "fetched_at": today.isoformat(),
                    "count": len(res), "stores": res}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    opened = [x for x in res if x["open"]]
    print(f"SWING24/7: {len(res)}店舗（営業中 {len(opened)} / オープン予定 {len(res)-len(opened)}）")
    for x in res:
        if x.get("open_source_url") or not x["open"]:
            print("   ", x["name"], "| open" if x["open"] else "| 準備中", "|", x["note"])
    miss = [x["name"] for x in res if not x["pref"]]
    if miss:
        print(f"  ⚠️ 都道府県が取れない: {miss}")


main()
