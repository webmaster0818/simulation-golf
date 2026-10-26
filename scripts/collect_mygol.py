#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""マイゴルフレーン（マイゴル・会員制の定額インドアゴルフ練習場）の店舗を公式サイトから取る。

店舗検索 https://www.mygol.jp/shop/ に /shop/<slug>/ のリンクが並ぶ。
店舗ページの `<div id="information">` の <dt>/<dd> に 営業時間・住所・電話番号・アクセス・駐車場、
`shop-price-list__item` に月額（定額練習し放題／回数制）がある。

⚠️ 一覧には /range/shop/<slug>.php という別形式のページ（マイゴルフレンジ＝都内11店＋福岡1店）も混ざる。
   高級路線の会員制個室スタジオで、店舗情報は `<div class="access">` の <dt>/<dd>（住所・TEL・最寄駅・駐車場）、
   料金は <h3>プラン名</h3> + <p class="tax-price">税込…円/月</p>。営業時間の欄は無く、
   本文の「24時間365日」／特徴欄の「365日営業」／TELの注記「（営業時間 6:00〜24:00）」で判定する（2026-10-07）。
   - <title> は全店「…| 24時間年中無休」が付くサイト共通のもので、6:00〜24:00 の店にも付いている。使わない。
   - 「施設利用なし」のレッスン専用プランは月会費に入れない。
   - 機種は冒頭の紹介文で『VISION PLUS』のように名指しされている。クラブのブランド（『PXG』『PING』）も
     同じ『』で書かれているので、既知の機種名だけ通す。
⚠️ 月額は税抜の大きな数字と「（基本プラン・税込10,000円）」が並んでいる。載せるのは税込のほう。
⚠️ 打席数・個室・機種・駐車場は店舗トップではなく、店舗ごとの別ページにある（/shop/ 形式・2026-10-16 追加）:
   <店舗>/equipments … 「打席数 4打席」「個別打席 個室あり／半個室あり／なし」「シミュレーター GDR Plus」
   <店舗>/facility   … 「駐車場 なし／無料駐車場あり …」
   以前は店舗トップしか読まず、全部「記載なし」になっていた。
   - 「半個室あり」は個室に数えない（サイトは bays に「個室」の字があると個室ありと表示する）。private_room は None。
   - facility ページ冒頭の「24時間365日、定額制で…」は 7時〜22時 の店（茅ヶ崎）にも出るテンプレートなので使わない。
     定休日は店舗トップの紹介文の「24時間365日通い放題」「365日使い放題」「24時間365日営業」だけで判定する
     （「365日レッスン受け放題」はプラン名・「電話：24時間365日受付可」は電話の話なので除く）。
⚠️ 公式に書いていない項目は None のままにする。推測で埋めない。

  python3 scripts/collect_mygol.py               # 取得して data/mygol.json に書く
  python3 scripts/collect_mygol.py --limit 3     # 動作確認
  python3 scripts/collect_mygol.py --range-only  # /range/shop/ の店だけ取り直して保存済みの結果に差し込む
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
BASE = "https://www.mygol.jp"
LIST_URL = f"{BASE}/shop/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
# 店名は「マイゴル八戸店」「マイゴルフレーン那覇店」の2通りある。ブランド名は両方に含まれる短いほうにする
# （長いほうにすると、ページタイトルが「マイゴルフレーン マイゴル八戸店」になる）
BRAND, BRAND_SLUG = "マイゴル", "mygol"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


# 公式サイトの記載どうしが食い違っている箇所。郵便番号検索（zipcloud）で突き合わせて見つけた。
FIXES = {
    # 郵便番号 470-0206 は「みよし市莇生町」で、住所の「三好丘緑」と合わない。合わない番号は載せない。
    "miyoshi": {"zip": None},
    # 越谷せんげん台駅東口店（2026-10-08・オープン前）: 店舗情報の欄に「住所」の行がまだ無い。
    # 本文に「越谷市千間台東に位置する」とあるだけなので町域までを住所にし、県は越谷市から補う。
    # 地図の埋め込みには 〒343-0042 越谷市千間台東1丁目10-1 が入っており、zipcloud でも 343-0042＝
    # 越谷市千間台東で一致するが、ページの本文に書かれていない番地・郵便番号は載せない。
    # → 2026-10-26 の取得で店舗情報に「住所 〒343-0042 埼玉県越谷市千間台東1丁目3-1」が出た（地図の 10-1 とは別の番地）。
    #   店舗情報の住所をそのまま使う。県はそこにあるのでこの FIX は実質不要だが、住所欄が消えたときの保険に残す。
    "koshigaya": {"pref": "埼玉県"},
}

# 住所の欄が無い店で、本文の「◯◯市◯◯に位置する」から町域までを取るための表現
LOCATED_RE = re.compile(r"([^\s「」。、]+?(?:市|区|町|村)[^\s「」。、]*?)に位置する")


CACHE: Path | None = None


def get(url: str) -> str:
    fp = None
    if CACHE is not None and "/shop/" in url and url.rstrip("/") != LIST_URL.rstrip("/"):
        CACHE.mkdir(parents=True, exist_ok=True)
        fp = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", url.split("mygol.jp", 1)[-1]).strip("_") + ".html")
        if fp.exists() and fp.stat().st_size > 2000:
            return fp.read_text(encoding="utf-8", errors="ignore")
    h = _fetch(url)
    if fp is not None and h:
        fp.write_text(h, encoding="utf-8")
    if "/equipments" in url or "/facility" in url:
        time.sleep(2)   # 店舗ごとの別ページも公式サイトに負荷をかけない間隔で
    return h


def _fetch(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def strip_hidden(h: str) -> str:
    return re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", "", h, flags=re.S)


def info(page_html: str) -> tuple[str | None, dict]:
    """店舗情報の欄だけを読む（ページ内のほかの <dl> を拾わない）"""
    i = page_html.find('id="information"')
    if i < 0:
        return None, {}
    seg = page_html[i:]
    j = seg.find("map-btn")
    seg = seg[: j if j > 0 else 6000]
    name = re.search(r'<h3 class="name">(.*?)</h3>', seg, re.S)
    out = {}
    for m in re.finditer(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", seg, re.S):
        k = text(m.group(1))
        # アクセスは <p> が複数並ぶ。区切りを残す
        v = text(re.sub(r"</p>\s*<p[^>]*>|<br\s*/?>", "／", m.group(2)))
        v = re.sub(r"\s*／\s*", "／", v).strip("／ ")
        if k and v and k not in out:
            out[k] = v
    return (text(name.group(1)) if name else None), out


def fee(page_html: str) -> str | None:
    items = []
    for blk in re.split(r'<div class="shop-price-list__item', page_html)[1:]:
        title = re.search(r'item-title[^"]*">(.*?)</p>', blk, re.S)
        tax = re.search(r'item-tax[^"]*">(.*?)</p>', blk, re.S)
        if not (title and tax):
            continue
        t = text(tax.group(1)).strip("（）() ")
        m = re.search(r"税込\s*([\d,]+)\s*円", t)
        if not m:
            continue
        note = re.sub(r"[・、]?\s*税込\s*[\d,]+\s*円", "", t).strip("・ ")
        items.append(f"{text(title.group(1))} {m.group(1)}円" + (f"（{note}）" if note else ""))
    return ("／".join(items) + "（税込）") if items else None


def is_open(page_text: str, today: str) -> bool:
    """「オープン予定」と書かれた日付がまだ来ていなければ準備中（False）。

    ⚠️ 開業後も「2026年8月オープン予定の…」という紹介文が残っている店が多い。
       文言の有無ではなく日付で判定する。日が書かれていない当月（「10月オープン予定」）と
       「下旬」などは、開業したと確認できないので準備中にする。
    ⚠️ 月も無い「2026年オープン予定」（越谷せんげん台駅東口店・2026-10-08）は、その年のうちは
       開業したと確認できないので準備中にする。
    ⚠️ 「無料見学・体験受付準備中！」は開業済みの店（八戸・川口・佐世保 ほか14店）にも残っている
       テンプレートの文。これで判定すると開業済みの店が準備中になる（2026-10-08 に全件取り直して判明）。
    """
    y0, m0, d0 = (int(x) for x in today.split("-"))
    dates = []
    for m in re.finditer(r"(\d{4})年(\d{1,2})月(?:(\d{1,2})日)?(上旬|中旬|下旬)?\s*(?:に)?(?:グランド)?(?:オープン|OPEN)予定", page_text):
        dates.append((int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None))
    for m in re.finditer(r"(?<![\d年])(\d{1,2})[月/](\d{1,2})日?\s*(?:オープン|OPEN)予定", page_text):
        dates.append((y0, int(m.group(1)), int(m.group(2))))
    for m in re.finditer(r"(\d{4})年\s*(?:に)?(?:グランド)?(?:オープン|OPEN)予定", page_text):
        if int(m.group(1)) >= y0:
            return False
    for y, mo, d in dates:
        if (y, mo) > (y0, m0):
            return False
        if (y, mo) == (y0, m0) and (d is None or d > d0):
            return False
    return True


def clean_hours(hours: str | None) -> tuple[str | None, bool | None]:
    """営業時間の欄に「当面の間 6:00〜23:00 に変更」とお知らせが入っている店がある（宮崎台店）。
    通常の表記だけ見て24時間と判定すると、今は開いていない時間帯を「24時間営業」と出してしまう。"""
    if not hours:
        return None, None
    h = re.sub(r"(\d)\s+時間", r"\1時間", hours)
    m = re.search(r"当面の間[^／]*?(\d{1,2}[:：]\d{2}\s*[〜～~-]\s*\d{1,2}[:：]\d{2})", h)
    if m:
        return f"当面の間 {m.group(1)}（通常は{h.split('／')[0]}）", False
    return h, ("24時間" in h)


def rows(page_html: str) -> dict:
    """<店舗>/equipments・/facility の表（<p class="value"> の前の見出し）を {見出し: 値} で返す。"""
    L = [x for x in (text(v) for v in re.split(r"<[^>]+>", strip_hidden(page_html))) if x]
    out = {}
    for i in range(len(L) - 1):
        if L[i] in ("打席数", "個別打席", "シミュレーター", "駐車場", "スタッフアワー") and L[i] not in out:
            out[L[i]] = L[i + 1]
    return out


# /shop/ の店の <店舗>/equipments に書かれた機種。表記はサイト内の既存の書き方にそろえる。
SHOP_EQUIPMENT = {"GDR Plus": "GOLFZON GDR PLUS", "TWOVISION": "GOLFZON TWOVISION",
                  "Joy Golf smart+": "Joy Golf smart+"}
# 西横浜店は「365日、24時間使い放題」と間に「、24時間」が入る（2026-10-25・以前は読めず closed が None になっていた）
OPEN365_RE = re.compile(r"(?:24時間)?365日(?:、24時間)?(?:通い放題|使い放題|営業|いつでも|利用できる)")


def shop_extra(url: str, top_html: str) -> tuple[dict, list[str]]:
    """/shop/ の店の equipments・facility ページと、トップの紹介文の 365日 の記載。"""
    problems, src = [], {}
    eq_url, fa_url = url.rstrip("/") + "/equipments", url.rstrip("/") + "/facility"
    e = rows(get(eq_url))
    f = rows(get(fa_url))
    r = {"bays": None, "bays_num": None, "private_room": None, "equipment": None,
         "parking": f.get("駐車場"), "closed": None}
    if r["parking"]:
        src["parking"] = fa_url
    m = re.fullmatch(r"(\d+)打席", e.get("打席数", ""))
    room = e.get("個別打席")
    if m:
        r["bays_num"] = int(m.group(1))
        r["bays"] = f"{m.group(1)}打席" + ("（個室あり）" if room == "個室あり" else "")
        src["bays"] = f"{eq_url}「打席数 {e['打席数']}／個別打席 {room}」"
    if room == "個室あり":
        r["private_room"] = True
    elif room == "なし":
        r["private_room"] = False
    sim = e.get("シミュレーター")
    if sim:
        if sim in SHOP_EQUIPMENT:
            r["equipment"] = SHOP_EQUIPMENT[sim]
            src["equipment"] = f"{eq_url}「シミュレーター {sim}」"
        else:
            problems.append(f"{url}: 見覚えのない機種名「{sim}」（載せていない）")
    body = text(top_html[:60000])
    hit = next((mm.group(0) for mm in OPEN365_RE.finditer(body)), None)
    if hit:
        r["closed"] = "年中無休（365日営業）" if hit.endswith("営業") else f"年中無休（公式「{hit}」）"
        src["closed"] = f"{url}「{hit}」"
    r["field_sources"] = src
    return r, problems


# マイゴルフレンジ（/range/shop/）の紹介文に出る機種。サイト内の既存の表記にそろえる。
# ⚠️ 『PXG』『PING』『テーラーメイド』『Paradym』はゴルフクラブのブランドなので通さない。
RANGE_EQUIPMENT = [
    (r"TWO\s*VISION\s*PLUS", "GOLFZON TWOVISION PLUS"),
    (r"VISION\s*PLUS", "GOLFZON VISION PLUS"),
    (r"GDR\s*PLUS", "GOLFZON GDR PLUS"),
    (r"GDR", "GOLFZON GDR"),
]


def range_store(url: str, h: str, today: str) -> tuple[dict | None, list[str]]:
    """マイゴルフレンジ（/range/shop/<slug>.php）1店ぶんを読む。"""
    problems = []
    title = re.search(r"<title>(.*?)</title>", h, re.S)
    name = text(title.group(1)).split("│")[0].strip() if title else None
    i = h.find('<div class="access">')
    if i < 0 or not name:
        return None, [f"{url}: 店舗情報が取れなかった"]
    seg = h[i:]
    j = seg.find("map-btn")
    seg = seg[: j if j > 0 else 4000]
    r = {}
    for m in re.finditer(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", seg, re.S):
        k, v = text(m.group(1)), text(m.group(2))
        if k and v and k not in r:
            r[k] = v
    addr = r.get("住所")
    if not addr:
        return None, [f"{url}: 住所が取れなかった"]
    zipc = None
    mz = re.match(r"〒?\s*(\d{3})-?(\d{4})\s*", addr)
    if mz:
        zipc = mz.group(1) + mz.group(2)
        addr = addr[mz.end():].strip()
    mp = re.match(rf"({PREFS})\s*", addr)

    # 本文（ヘッダーのタイトルやナビを除く）。営業時間と個室の判定はここだけ見る
    k = h.find('<section class="shop-main">')
    body = text(h[k:]) if k > 0 else text(h)
    hours, is24, closed = None, None, None
    if "24時間365日" in body or re.search(r"24時間\s*365日営業", body):
        hours, is24, closed = "24時間365日営業", True, "年中無休"
    elif re.search(r"365日営業|365日いつでも", body):
        closed = "年中無休（365日営業）"
    tel = r.get("TEL")
    if tel:
        tel = tel.replace("‐", "-").replace("－", "-")
        mt = re.match(r"([\d-]+)\s*[（(]\s*(.*?)\s*[）)]", tel)
        if mt:
            tel = f"{mt.group(1)}（{mt.group(2)}）"
            mh = re.search(r"営業時間\s*(\d{1,2}:\d{2}\s*[〜～~-]\s*\d{1,2}:\d{2})", mt.group(2))
            if mh and not hours:
                hours, is24 = re.sub(r"\s*[〜～~-]\s*", "〜", mh.group(1)), False
    parking = r.get("駐車場")
    if parking:
        parking = re.sub(r"\s*地図を(?:みる|見る)\s*$", "", parking)

    # 個室: 「2つの個室」と数が書いてあればその数。「完全個室」とだけあれば数は記載なし
    bays, bays_num, private = None, None, None
    mb = re.search(r"(\d+)つの個室", body)
    if mb:
        bays_num, private = int(mb.group(1)), True
        bays = f"完全個室{bays_num}打席"
    elif "完全個室" in body:
        private = True
        bays = "完全個室（打席数は公式サイトに記載なし）"

    # 機種: 冒頭の紹介文（shop-main）で『』に入っているものだけ。既知の機種だけ通す
    ml = re.search(r'<section class="shop-main">(.*?)</section>', h, re.S)
    lead = text(ml.group(1)) if ml else ""
    if "『" not in lead:
        # 動画付きの店（ランドル高輪ゲートウェイ）は紹介文が <section> の外にある
        k2 = body.find("インドアゴルフ練習場")
        lead = body[k2:k2 + 400] if k2 >= 0 else ""
    eq, unknown = [], []
    for q in re.findall(r"『([^』]+)』", lead):
        hit = next((lab for pat, lab in RANGE_EQUIPMENT if re.fullmatch(pat, q, re.I)), None)
        if hit and hit not in eq:
            eq.append(hit)
        elif not hit:
            unknown.append(q)
    if unknown:
        problems.append(f"{name}: 紹介文の『』に機種として扱わなかった語 {unknown}")

    # 料金: 税込の行だけ。施設利用の無いレッスン専用プランは入れない
    plans, seen = [], set()
    for m in re.finditer(r"<h3>(.*?)<span>.*?</span></h3>\s*<p class=\"price\">.*?</p>\s*"
                         r"<p class=\"tax-price\">(.*?)</p>\s*<p>(.*?)</p>", h, re.S):
        pname, tax, desc = text(m.group(1)), text(m.group(2)), text(m.group(3))
        my = re.search(r"税込\s*([\d,]+)\s*円", tax)
        if not my or "施設利用なし" in desc or pname in seen:
            continue
        seen.add(pname)
        note = []
        mt_ = re.search(r"(\d+時\s*[〜～~]\s*\d+時(?:\d+分)?のみ)", desc)
        if mt_:
            note.append(mt_.group(1).replace(" ", ""))
        if "全店舗" in desc:
            note.append("全店舗利用可")
        ml_ = re.search(r"(\S+限定)", desc)
        if ml_:
            note.append(ml_.group(1))
        plans.append(f"{pname} {my.group(1)}円" + (f"（{'・'.join(note)}）" if note else ""))
    fee = ("／".join(plans) + "（税込・1コマ90分）") if plans else None
    mi = re.search(r"登録料[：:]?\s*税抜[\d,]+円\s*\(税込([\d,]+)円\)\s*入会金[：:]?\s*税抜[\d,]+円\s*\(税込([\d,]+)円\)", body)
    if fee and mi:
        fee += f"。別途 初回登録料{mi.group(1)}円・入会金{mi.group(2)}円"
    if not fee:
        problems.append(f"{name}: 月額が取れなかった（{url}）")

    slug = url.rsplit("/", 1)[-1].replace(".php", "")
    s = {
        "brand": BRAND, "brand_slug": BRAND_SLUG,
        "slug": slug,
        "name": name,
        "pref": mp.group(1) if mp else None,
        "zip": zipc,
        "address": addr,
        "access": r.get("最寄駅"),
        "tel": tel,
        "hours": hours,
        "open_24h": is24,
        "closed": closed,
        "bays": bays, "bays_num": bays_num,
        "private_room": private,
        "parking": parking,
        "monthly_fee": fee,
        "equipment": "／".join(eq) if eq else None,
        "open": is_open(body, today),
        "official": url,
        "source_url": url, "fetched_at": today,
    }
    s.update(FIXES.get(slug, {}))
    return s, problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="このslug（カンマ区切り）だけ取り直して保存済みの結果に上書きする")
    ap.add_argument("--range-only", action="store_true",
                    help="/range/shop/ の店だけ取り直して保存済みの結果に差し込む（/shop/ の店は触らない）")
    ap.add_argument("--cache", default="",
                    help="店舗ページのキャッシュ先（同じ日に何度も取り直すとき用。古いキャッシュは使わない）")
    a = ap.parse_args()
    global CACHE
    CACHE = Path(a.cache) if a.cache else None
    only = {x for x in a.only.split(",") if x}

    listing = strip_hidden(get(LIST_URL))
    all_links = list(dict.fromkeys(
        re.findall(r'href="((?:https://www\.mygol\.jp)?/(?:range/)?shop/[^"#?]+)"', listing)))
    paths = [l for l in all_links if re.search(r"/shop/[a-z0-9_-]+/?$", l) and "/range/" not in l]
    other = [l for l in all_links if "/range/shop/" in l and l.endswith(".php")]
    print(f"店舗ページ {len(paths)}件（マイゴルフレンジ /range/shop/ {len(other)}件）")
    if a.range_only:
        paths = []

    today = date.today().isoformat()
    stores, problems = [], []
    for i, link in enumerate(paths, 1):
        if a.limit and i > a.limit:
            break
        url = link if link.startswith("http") else BASE + link
        url = url.rstrip("/") + "/"
        if only and url.rstrip("/").rsplit("/", 1)[-1] not in only:
            continue
        h = strip_hidden(get(url))
        name, r = info(h)
        addr = r.get("住所")
        if name and not addr:
            # オープン前の店は店舗情報に「住所」の行がまだ無い（越谷せんげん台駅東口店・2026-10-08）。
            # 本文の「越谷市千間台東に位置する」から町域までを取る。番地は書かれていないので無し
            ml = LOCATED_RE.search(text(h[:60000]))
            if ml:
                addr = ml.group(1)
                problems.append(f"{name}: 住所の欄が無い。本文の「{addr}に位置する」から町域までを載せた（{url}）")
        if not (name and addr):
            problems.append(f"{url}: 店舗情報が取れなかった")
            time.sleep(2)
            continue
        zipc = None
        mz = re.match(r"〒?\s*(\d{3})-?(\d{4})\s*", addr)
        if mz:
            zipc = mz.group(1) + mz.group(2)
            addr = addr[mz.end():].strip()
        # 「沖縄県 那覇市 宇栄原1009-2」のように県・市の後ろに空白が入る店がある
        mp = re.match(rf"({PREFS})\s*", addr)
        if mp:
            rest = addr[mp.end():]
            rest = re.sub(r"^(\S+?[市区町村郡])\s+", r"\1", rest)
            addr = mp.group(1) + rest
        hours, is24 = clean_hours(r.get("営業時間"))
        tel = r.get("電話番号")
        if tel:
            tel = re.sub(r"^TEL[：:]\s*", "", tel).replace("／", "（", 1) + ("）" if "／" in tel else "")
        opened = is_open(text(h[:60000]), today)
        ex, pr = shop_extra(url, h)
        problems.extend(pr)
        src = ex["field_sources"]
        if r.get("定休日"):
            src["closed"] = url
        if r.get("駐車場"):
            src.pop("parking", None)
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": url.rstrip("/").rsplit("/", 1)[-1],
            "name": name,
            "pref": mp.group(1) if mp else None,
            "zip": zipc,
            "address": addr,
            "access": r.get("アクセス"),
            "tel": tel,
            "hours": hours,
            "open_24h": is24,
            "closed": r.get("定休日") or ex["closed"],
            "bays": ex["bays"], "bays_num": ex["bays_num"],
            "private_room": ex["private_room"],
            # 駐車場は店舗トップの店舗情報を優先し、無ければ <店舗>/facility の「駐車場」
            "parking": r.get("駐車場") or ex["parking"],
            "monthly_fee": fee(h),
            "equipment": ex["equipment"],
            "open": opened,
            "official": url,
            "source_url": url, "fetched_at": today,
            **({"field_sources": src} if src else {}),
        })
        s = stores[-1]
        s.update(FIXES.get(s["slug"], {}))
        if s["pref"] and not s["address"].startswith(s["pref"]):
            s["address"] = s["pref"] + s["address"]   # 県を補った店（越谷）は住所の先頭にもそろえる
        if not s["monthly_fee"]:
            problems.append(f"{name}: 月額が取れなかった（{url}）")
        print(f"  {i:2}/{len(paths)} {s['name']} … {s['pref'] or '県不明'} / {s['hours']} / {s['monthly_fee']}"
              f"{'' if opened else ' / 準備中'}", flush=True)
        time.sleep(2)   # 公式サイトに負荷をかけない

    # --- マイゴルフレンジ（/range/shop/<slug>.php） ---
    range_stores = []
    for i, link in enumerate(other, 1):
        if a.limit and i > a.limit:
            break
        url = link if link.startswith("http") else BASE + link
        if only and url.rsplit("/", 1)[-1].replace(".php", "") not in only:
            continue   # --only のときは /range/shop/ の店も取り直さない
        s, pr = range_store(url, strip_hidden(get(url)), today)
        problems.extend(pr)
        if s:
            range_stores.append(s)
            print(f"  R{i:2}/{len(other)} {s['name']} … {s['pref'] or '県不明'} / {s['hours'] or '営業時間の記載なし'} / "
                  f"{s['equipment']} / {s['monthly_fee']}{'' if s['open'] else ' / 準備中'}", flush=True)
        time.sleep(2)

    out = DATA / "mygol.json"
    if only or a.range_only:
        prev = json.loads(out.read_text(encoding="utf-8"))["stores"]
        fresh = {x["slug"]: x for x in stores + range_stores}
        stores = [fresh.pop(x["slug"], x) for x in prev] + list(fresh.values())
        for x in stores:
            x.pop("opening_hint", None)
    else:
        stores = stores + range_stores
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件 → {out}")
    nopref = [s["name"] for s in stores if not s["pref"]]
    if nopref:
        print("  ⚠️ 都道府県が取れなかった店:", nopref)
    for p in problems:
        print("  ⚠️", p)


if __name__ == "__main__":
    main()
