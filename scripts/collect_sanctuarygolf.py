#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サンクチュアリゴルフ（初心者専用インドアゴルフスクール・株式会社サンクチュアリゴルフ）を公式サイトから取る。

「ゴルフスクール サンクチュアリ」と「サンクチュアリゴルフ」は同じブランド（運営は株式会社サンクチュアリゴルフ）。
公式サイトが2つに分かれている:
  https://www.sanctuarygolf.jp/<slug>          … 初期からのスクール店（六本木・池袋・銀座有楽町・新宿東口/西口・川崎・横浜・川越）
  https://range.sanctuarygolf.jp/locations/<slug>/ … 「インドアゴルフレンジ＆スクール」店（渋谷青山・葛西・戸越銀座…）
店舗一覧は www の /schools。そのメニュー（「Schools」欄）の店名とリンクを正とする。
各店ページの <table>（住所・電話番号・営業時間・休館日）と、ページ上部の紹介文（打席数・機材・駐車場）から取る。

⚠️ /schools の一覧カードには HTML コメントで隠した店（多摩永山店＝店舗ページ404）が残っている。
   コメントを除いてから読む（横浜店 /yokohama もメニュー・一覧ともコメントアウトされている。
   ページは残っているが電話番号欄が「有楽町店の番号」「決まり次第掲載」のままなので載せない）。銀座新橋店は一覧に「※閉店いたしました」と出るので除外する。
⚠️ 料金は店ごとの料金表が画像（range.sanctuarygolf.jp/fees/ の pricetable_*.jpg）で、本文に数字が無い。
   本文に「【月額】」と書いてある店はそれを入れる（亀戸）。「地域最安値5,793円～」のような
   月額かどうか書いていない金額は載せない。
   それ以外の店は料金表の画像を目で読んで転記した FEE_IMAGES / WWW_FEES を使う（2026-10-16）。
   画像がその店の料金ページから消えたら null に戻して警告する（monthly_fee_source に出典の画像名）。
⚠️ 横浜店の電話番号欄は「※こちらは有楽町店の番号となっております」→ 横浜店の番号ではないので null。
⚠️ イオン南砂店の「エリア合計30打席利用可」は近隣店舗との合計で、この店の打席数ではない。
⚠️ 姉妹業態の「無人くん」（成田・九段下・無人のインドア練習場）は別ブランド名なのでここでは取らない。

  python3 scripts/collect_sanctuarygolf.py        # 取得して data/sanctuarygolf.json に書く
"""
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
WWW = "https://www.sanctuarygolf.jp"
LIST_URL = WWW + "/schools"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "サンクチュアリゴルフ", "sanctuarygolf"

# 公式URLのローマ字が店名と食い違うものだけ直す（新宿東口店の URL は /shinjuku。一覧カードの表記は SHINJUKU HIGASHIGUCHI）
SLUG_FIX = {"shinjuku": "shinjuku-higashiguchi", "kawagoe": "atre-kawagoe"}

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")
CITY_PREF = {"千葉市": "千葉県", "さいたま市": "埼玉県", "横浜市": "神奈川県", "川崎市": "神奈川県"}
# 東京23区で始まる住所（新宿西口店「新宿区西新宿1-16-11…」）は東京都を補う
CITY_PREF.update({w: "東京都" for w in (
    "千代田区 中央区 港区 新宿区 文京区 台東区 墨田区 江東区 品川区 目黒区 大田区 世田谷区 渋谷区 "
    "中野区 杉並区 豊島区 北区 荒川区 板橋区 練馬区 足立区 葛飾区 江戸川区").split()})

# 公式が名指ししている機材だけ。表記はサイト内の既存の語にそろえる。
EQUIPMENT = [
    (r"TRACKMAN|トラックマン", "TRACKMAN"),
    (r"GDR\s*(?:\+|＋|plus|PLUS|Plus)", "GOLFZON GDR PLUS"),
    (r"QED", "QEDゴルフシミュレーター"),
    (r"ゴルフナビ", "ゴルフナビ"),
    (r"ゴルフランドシミュレーター", "ゴルフランドシミュレーター"),
    (r"ディテクト社製ゴルフシミュレーター", "ディテクト社製ゴルフシミュレーター"),
]


# --- 月額（料金表の画像を目で読んで転記したもの・2026-10-16） ---
# 料金表は画像だけで本文に数字が無い。画像を1枚ずつ目で読んで転記し、画像のファイル名で紐づける。
# 取得のたびに「その店の料金ページ（タブ）にこの画像が今も載っているか」を確かめ、
# 載っていなければ（画像が差し替わった）月額は null に戻して警告する → 画像を見て転記し直す。
# 表記は画像のまま「本体価格（税込…）」。キャンペーン価格・初月0円は載せない（通常の料金表の行だけ）。
# 店舗ページに【月額】がある店（亀戸「￥4,290〜」）は店舗ページを優先する（料金表画像は最安 7,900円（税込8,690円）で食い違う）。
RANGE_FEES = "https://range.sanctuarygolf.jp/fees/"
_E = "入会金10,000円（税込11,000円）別途"
FEE_IMAGES = {
    # range.sanctuarygolf.jp/fees/ のタブ名 → 料金表画像（月額費用の表）と転記
    "葛西": ("img1-1-1024x999.jpg",
             "フルタイム会員 男性18,900円（税込20,790円）・女性15,900円（税込17,490円）・キッズ9,800円（税込10,780円）／"
             "デイタイム会員 男性14,900円（税込16,390円）・女性11,900円（税込13,090円）／レンジ会員 9,900円（税込10,890円）（" + _E + "）"),
    "戸越銀座": ("pricetable-1024x999.jpg",
             "フルタイム会員 男性21,900円（税込24,090円）・女性17,900円（税込19,690円）・キッズ10,800円（税込11,880円）／"
             "デイタイム会員 男性17,900円（税込19,690円）・女性13,900円（税込15,290円）／レンジ会員 11,900円（税込13,090円）（" + _E + "）"),
    "錦糸町": ("pricetable_kinshicho-939x1024.jpg",
             "フルタイム会員 男性18,900円（税込20,790円）・女性15,900円（税込17,490円）・キッズ9,800円（税込10,780円）／"
             "デイタイム会員 男性14,900円（税込16,390円）・女性11,900円（税込13,090円）／"
             "練習会員 フルタイム9,900円（税込10,890円）・デイタイム7,900円（税込8,690円）（" + _E + "）"),
    "渋谷": ("pricetable_shibuya-1024x891.png",
             "フルタイム会員 男性26,900円（税込29,590円）・女性21,900円（税込24,090円）／"
             "デイタイム会員 男性22,900円（税込25,190円）・女性17,900円（税込19,690円）（" + _E + "）"),
    "千葉中央": ("chiba_pricetable-1024x1007.png",
             "フルタイム会員 女性13,900円（税込15,290円）・男性15,900円（税込17,490円）／"
             "デイタイム会員 女性9,900円（税込10,890円）・男性11,900円（税込13,090円）／"
             "デイレンジ会員 7,900円（税込8,690円）／ナイトレンジ会員 6,900円（税込7,590円）（" + _E + "）"),
    "浦和": ("pricetable_urawa-1024x804.png",
             "フルタイム会員 15,900円（税込17,490円）／デイタイム会員 11,900円（税込13,090円）／"
             "ナイトレンジ会員 9,900円（税込10,890円）（" + _E + "）"),
    "つくば": ("tsukuba_pricetable-1024x888.jpg",
             "フルタイム会員 13,900円（税込15,290円）／デイタイム会員 9,900円（税込10,890円）／"
             "レンジ会員 7,900円（税込8,690円）／フィットネス会員 3,900円（税込4,290円）（" + _E + "）"),
    "成増": ("narimasu_pricetable-1024x882.jpg",
             "フルタイム会員 17,900円（税込19,690円）／デイタイム会員 13,900円（税込15,290円）／"
             "レンジ会員 10,900円（税込11,990円）／ナイトレンジ会員 7,900円（税込8,690円）（" + _E + "）"),
    "神保町": ("jinbocho_pricetable-983x1024.jpg",
             "デイタイム会員 13,900円（税込15,290円）／フルタイム会員 17,900円（税込19,690円）／"
             "レンジ会員 10,900円（税込11,990円）／ナイトレンジ会員 7,900円（税込8,690円）／デイレンジ会員 8,400円（税込9,240円）／"
             "学生プラン［フルタイム］15,200円（税込16,720円）（" + _E + "）"),
    "秋葉原浅草橋": ("pricetable_akiba-1020x1024.png",
             "デイタイム会員 13,900円（税込15,290円）／フルタイム会員 17,900円（税込19,690円）／"
             "ナイトレンジ会員 7,900円（税込8,690円）／デイレンジ会員 8,400円（税込9,240円）（" + _E + "）"),
    "笹塚": ("sasazuka_pricetable-1020x1024.png",
             "デイタイム会員 13,900円（税込15,290円）／フルタイム会員 17,900円（税込19,690円）／"
             "ナイトレンジ会員 7,900円（税込8,690円）／デイレンジ会員 8,400円（税込9,240円）（" + _E + "）"),
    "亀戸": ("kameido_pricetable-895x1024.png",
             "フルタイム会員 男性18,900円（税込20,790円）・女性15,900円（税込17,490円）／"
             "デイタイム会員 男性14,900円（税込16,390円）・女性11,900円（税込13,090円）／"
             "デイレンジ会員 7,900円（税込8,690円）／ナイトレンジ会員 7,900円（税込8,690円）（" + _E + "）"),
    "イオン南砂": ("minamisuna_pricetable-1024x887.png",
             "フルタイム会員 15,900円（税込17,490円）／デイタイム会員 11,900円（税込13,090円）（" + _E + "）"),
    "立川": ("tachikawa_pricetable-1024x999.png",
             "フルタイム会員 17,900円（税込19,690円）／デイタイム会員 13,900円（税込15,290円）／"
             "レンジ会員 11,900円（税込13,090円）／デイレンジ会員 8,400円（税込9,240円）／ナイトレンジ会員 7,900円（税込8,690円）／"
             "ジュニア会員（中学生以下）10,800円（税込11,880円）（" + _E + "）"),
    "川越": ("kawagoe_pricetable-1024x882.png",
             "フルタイム会員 女性15,900円（税込17,490円）・男性18,900円（税込20,790円）／"
             "デイタイム会員 女性11,900円（税込13,090円）・男性14,900円（税込16,390円）（" + _E + "）"),
    "大宮": ("omiya_pricetable-1024x962.png",
             "フルタイム会員 17,900円（税込19,690円）／デイタイム会員 13,900円（税込15,290円）／"
             "レンジ会員 10,900円（税込11,990円）／デイレンジ会員 8,400円（税込9,240円）／ナイトレンジ会員 7,900円（税込8,690円）"
             "（入会金20,000円（税込22,000円）別途）"),
    "横浜桜木町": ("yokohama-sakuragucho_pricetable-939x1024.png",
             "フルタイム会員 17,900円（税込19,690円）／デイタイム会員 13,900円（税込15,290円）／"
             "ジュニア会員 12,000円（税込13,200円）／キッズ会員 9,900円（税込10,890円）／フルレンジ会員 10,900円（税込11,990円）／"
             "デイレンジ会員 8,400円（税込9,240円）／ナイトレンジ会員 7,900円（税込8,690円）（" + _E + "）"),
}
# www.sanctuarygolf.jp の店: 池袋・川崎は専用の料金ページ。六本木・銀座有楽町・新宿東口・新宿西口は専用ページが無く、
# 池袋/川崎/川越の料金ページにある「その他の店の料金はこちら」→ /fees の表（通常価格の列）を使う。
# /fees の表の注記「※表記価格のナイトレンジ会員は新宿店の利用価格になります。」→ ナイトレンジは新宿東口店（/shinjuku）にだけ入れる。
_WWW_OTHER = ("フルタイム会員 女性19,900円（税込21,890円）・男性24,900円（税込27,390円）／"
              "デイタイム会員 女性15,900円（税込17,490円）・男性20,900円（税込22,990円）")
WWW_FEES = {
    "ikebukuro": (WWW + "/fees-ikebukuro", "ikebukuro_fees.jpg",
                  "フルタイム会員 女性19,900円（税込21,890円）・男性24,900円（税込27,390円）／"
                  "デイタイム会員 女性15,900円（税込17,490円）・男性20,900円（税込22,990円）／"
                  "レンジ会員［デイ］8,900円（税込9,790円）（" + _E + "）"),
    "kawasaki": (WWW + "/fees-kawasaki", "pricetable_kawasaki.jpg",
                 "フルタイム会員 17,900円（税込19,690円）／デイタイム会員 13,900円（税込15,290円）／"
                 "レンジ会員 フルタイム10,900円（税込11,990円）・デイタイム8,400円（税込9,240円）・ナイトタイム7,900円（税込8,690円）（" + _E + "）"),
    "roppongi": (WWW + "/fees", "part04.jpg", _WWW_OTHER + "（" + _E + "）"),
    "ginza-yurakucho": (WWW + "/fees", "part04.jpg", _WWW_OTHER + "（" + _E + "）"),
    "shinjuku-nishiguchi": (WWW + "/fees", "part04.jpg", _WWW_OTHER + "（" + _E + "）"),
    "shinjuku": (WWW + "/fees", "part04.jpg",
                 _WWW_OTHER + "／ナイトレンジ会員 女性7,900円（税込8,690円）・男性9,000円（税込9,900円）（" + _E + "）"),
}
# 店名 → range の料金タブ名（店名から「店」を落とした名と違うものだけ）
FEE_TAB = {"渋谷青山店": "渋谷", "神田神保町店": "神保町", "アトレ川越店": "川越"}


def range_fee_tabs() -> dict[str, str]:
    """range の /fees/ を タブ名 → そのタブの HTML に分ける（タブの並びと中身の並びは同じ）。"""
    _, h = get(RANGE_FEES)
    h = clean(h)
    navs = [text(n) for n in re.findall(
        r'<li[^>]*class="[^"]*eael-tab-item-trigger[^"]*"[^>]*>(.*?)</li>', h, re.S)]
    parts = re.split(r'<div id="[^"]*" class="clearfix eael-tab-content-item', h)[1:]
    return dict(zip(navs, parts)) if len(navs) == len(parts) else {}


def fee_from_images(url: str, name: str, raw_slug: str, tabs: dict, www_pages: dict, problems: list) -> tuple[str | None, str | None]:
    """転記した料金表を、画像が今もその店の料金ページに載っているときだけ返す。(月額, 出典)"""
    if "range.sanctuarygolf.jp" in url:
        tab = FEE_TAB.get(name, name.removesuffix("店"))
        if tab not in FEE_IMAGES:
            problems.append(f"{name}: 料金タブ「{tab}」の転記が無い")
            return None, None
        img, fee = FEE_IMAGES[tab]
        if img not in tabs.get(tab, ""):
            problems.append(f"{name}: 料金表画像 {img} が /fees/ の「{tab}」タブに無い（差し替わった？）→ 月額 null")
            return None, None
        return fee, f"{RANGE_FEES}（「{tab}」タブの料金表画像 {img}・画像を目で読んで転記）"
    if raw_slug == "kawagoe":  # www の店だが、range の /fees/ にも「川越」タブがある（デイタイムまで載っている方を使う）
        img, fee = FEE_IMAGES["川越"]
        if img in tabs.get("川越", ""):
            return fee, f"{RANGE_FEES}（「川越」タブの料金表画像 {img}・画像を目で読んで転記。{WWW}/fees-kawagoe のフルタイムと同額）"
        problems.append(f"{name}: 料金表画像 {img} が /fees/ の「川越」タブに無い → 月額 null")
        return None, None
    if raw_slug in WWW_FEES:
        page, img, fee = WWW_FEES[raw_slug]
        if page not in www_pages:
            time.sleep(1.5)
            www_pages[page] = clean(get(page)[1])
        if img not in www_pages[page]:
            problems.append(f"{name}: 料金表画像 {img} が {page} に無い（差し替わった？）→ 月額 null")
            return None, None
        note = "画像を目で読んで転記・通常価格の列"
        if page.endswith("/fees"):
            note += "。池袋/川崎/川越の料金ページの「その他の店の料金はこちら」の先"
        return fee, f"{page}（料金表画像 {img}・{note}）"
    return None, None


def get(url: str) -> tuple[int, str]:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, "-w", "\n%{http_code}", url],
                           capture_output=True, text=True, timeout=60)
        body, _, code = r.stdout.rpartition("\n")
        if code == "404":
            return 404, ""
        if body and len(body) > 2000:
            return int(code or 0), body
        time.sleep(3)
    return 0, ""


def clean(h: str) -> str:
    return re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", "", h, flags=re.S)


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def store_list() -> list[tuple[str, str, str]]:
    """/schools のメニュー（Schools 欄）から (URL, 店名, 一覧カードの文) を返す。閉店は除く。"""
    _, h = get(LIST_URL)
    h = clean(h)
    cards = text(h)
    out, seen = [], set()
    for m in re.finditer(r'<a href="([^"]+)"[^>]*>\s*([^<]{2,20}店)\s*</a>', h):
        url, name = m.group(1), m.group(2).strip()
        if url.startswith("/"):
            url = WWW + url
        if not re.search(r"sanctuarygolf\.jp/(?:locations/)?[a-z-]+/?$", url) or url in seen:
            continue
        seen.add(url)
        # 一覧カード（「◯◯店 ROMAJI …詳細を見る」）でこの店に閉店の記載があるか
        cm = re.search(re.escape(name) + r" [A-Z][A-Z -]+ (.{0,200}?)詳細を", cards)
        card = cm.group(1) if cm else ""
        if "閉店" in card:
            print(f"  除外（一覧に閉店の記載）: {name}")
            continue
        out.append((url, name, card))
    return out


def table(h: str) -> dict:
    out = {}
    for m in re.finditer(r"<tr[^>]*>\s*<t[hd][^>]*>(.*?)</t[hd]>\s*<td[^>]*>(.*?)(?:</td>|</tr>)", h, re.S):
        k = text(m.group(1))
        v = text(re.sub(r"<br\s*/?>", " ", m.group(2)))
        if k and v and k not in out:
            out[k] = v
    return out


def main_text(h: str) -> str:
    """フッター・ナビの全店共通文を落とした本文。"""
    t = text(h)
    for cut in ("インドアゴルフレンジ＆スクール「サンクチュアリ」 インドアゴルフレンジ&",
                "初心者専用のゴルフスクール『サンクチュアリ』 初心者専用",
                "初心者専用のゴルフスクール『サンクチュアリ』"):
        t = t.split(cut)[0]
    t = re.sub(r"^.*?Toggle navigation.*?九段下店 体験レッスンお申込み 会員様WEB予約", "", t)
    return t


def access_of(t: str) -> str | None:
    """「電車ご利用の方」欄の見出し行（◆/■/路線名「駅」…徒歩N分）だけを拾う。①〜の道順は載せない。"""
    m = re.search(r"電車(?:・モノレール)?(?:ご利用|でお越し)の方(.*?)(?:バスご利用|車で(?:ご利用|お越し)|まずは体験|$)", t)
    if not m:
        return None
    sec = re.sub(r"ACCESS BY [A-Z・]+", " ", m.group(1))
    # 道順（①〜）の最後の手順は「…の4階（EVあり）」「…の2階へ」で終わる。そこまでを道順として落とす
    chunks = re.split(r"[◆■]|詳しい行き方はこちら|[①-⑳]|ルート\s*\d|パターン|【|★", sec)
    items = []
    for c in chunks:
        c = re.sub(r"^.*(?:階|EVあり）|F)\s*(?:です|へ)?\s*(?=\S*[線駅])", "", c.strip())
        mm = re.match(r"(.{0,60}?(?:徒歩\s*\d+\s*(?:分|秒)|約?\s*\d+\s*分)[）)]?)", c)
        if mm and re.search(r"駅|線|モノレール|東京メトロ|都営|JR", mm.group(1)):
            items.append(re.sub(r"\s+", " ", mm.group(1)).strip())
    return "／".join(dict.fromkeys(items)) or None


def parking_of(t: str) -> str | None:
    pats = [
        r"((?:屋根付き)?無料(?:地下)?駐車場[^。◆■]{0,40}?完備[^◆■]{0,40}?)(?=\s*◆|\s*■|$|\s)",
        r"(\d[\d,]*台の駐車場完備[^◆■]{0,20})",
        r"(大型市営駐車場あり)",
        r"(※?(?:専用)?駐車場(?:の(?:ご用意|用意)は|は)ございません。?(?:\s*近隣[^。]{0,40}。)?)",
        r"(※?(?:当店に)?駐車場はございません。?(?:\s*お車でお越しの際は[^。]{0,40}。)?)",
        r"(※?専用(?:及び提携)?駐車場(?:は)?ありません。?(?:\s*※?近隣[^。]{0,40}。)?)",
    ]
    for p in pats:
        m = re.search(p, t)
        if m:
            return m.group(1).strip()
    return None


def bays_of(intro: str) -> tuple[str | None, int | None]:
    """「全6打席（左右対応打席1打席）」「打席数8（うち左右打席1）」「11打席県内最大級」から打席数。
    「エリア合計30打席利用可」（近隣店との合計）は取らない。"""
    intro = intro.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    for p in (r"全\s*然?\s*(\d+)\s*打席", r"打席数\s*(\d+)\s*(?:打席)?", r"(?<![\d合計])(\d+)\s*打席"):
        m = re.search(p, intro)
        if m:
            n = int(m.group(1))
            rest = intro[m.end():]
            mp = re.match(r"\s*([（(][^）)]{1,20}[）)])", rest)
            if not mp:
                mp = re.match(r"\s*シミュレーション完備\s*([（(][^）)]{1,20}[）)])", rest)
            note = re.sub(r"\s+", "", mp.group(1)) if mp else ""
            return f"{n}打席{note}", n
    return None, None


def main() -> None:
    today = date.today().isoformat()
    stores, problems = [], []
    time.sleep(1.5)
    tabs = range_fee_tabs()
    if not tabs:
        problems.append(f"{RANGE_FEES} のタブを読めなかった（タブ名と中身の数が合わない）→ range 店の月額は null")
    www_pages: dict[str, str] = {}
    for url, name, card in store_list():
        time.sleep(1.5)
        code, h = get(url)
        if code == 404 or not h:
            problems.append(f"{name}: ページが取れなかった（{code}） {url}")
            continue
        h = clean(h)
        tb = table(h)
        t = main_text(h)
        intro = t.split(" 住所 ")[0]

        raw_slug = url.rstrip("/").rsplit("/", 1)[-1]
        slug = SLUG_FIX.get(raw_slug, raw_slug)

        addr = tb.get("住所", "")
        zipc = None
        mz = re.match(r"〒\s*(\d{3})-?(\d{4})\s*", addr)
        if mz:
            zipc = mz.group(1) + mz.group(2)
            addr = addr[mz.end():].strip()
        addr = addr.replace("　", " ").strip()
        mp = re.match(rf"({PREFS})", addr)
        pref = mp.group(1) if mp else None
        if not pref:
            for city, p in CITY_PREF.items():
                if addr.startswith(city):
                    pref, addr = p, p + addr
        if not pref:
            problems.append(f"{name}: 住所に都道府県が無い（{addr}）")

        tel_cell = tb.get("電話番号", "")
        tel = None
        mt = re.search(r"0\d{1,4}-\d{1,4}-\d{3,4}", tel_cell)
        if mt and "の番号となっております" not in tel_cell:
            tel = mt.group(0)

        hours = tb.get("営業時間")
        if hours:
            hours = re.sub(r"\s*：\s*", ":", hours)
        # 営業時間欄に「24時間営業」（[レンジ] 24時間営業 等）、または「ナイトレンジ（無人営業）」で夜間も埋まる店。
        # 欄に無くても店舗ページの紹介に「24時間営業」と言い切っている店（横浜桜木町）は24時間。
        # 「24時間営業(他店セルフ利用可)」（葛西・イオン南砂）は他店で24時間使えるという意味で、この店は24時間ではない。
        is24 = bool(hours and ("24時間営業" in hours or "ナイトレンジ（無人営業）" in hours))
        if hours and not is24 and re.search(r"24\s*時間営業(?![！!\s]*[（(]他店)", intro):
            is24 = True
        closed = tb.get("休館日")

        bays, bays_num = bays_of(intro)
        private = True if re.search(r"個室", intro) else None
        eq = []
        for pat, label in EQUIPMENT:
            if re.search(pat, t) and label not in eq:
                eq.append(label)
        fee = fee_src = None
        mf = re.search(r"【月額】\s*[￥¥]\s*([\d,]+)\s*(〜|～)?\s*(打席料など追加料金不要)?", t)
        if mf:
            fee = f"月額{mf.group(1)}円{'〜' if mf.group(2) else ''}（{(mf.group(3) + '。') if mf.group(3) else ''}税込・税抜の別は公式サイトに記載なし）"
            fee_src = url + "（店舗ページの【月額】）"
        else:
            fee, fee_src = fee_from_images(url, name, raw_slug, tabs, www_pages, problems)

        is_open = True
        mo = re.search(r"(\d{4})[年./](\d{1,2})[月./](\d{1,2})日?[^。◆]{0,12}(?:オープン|OPEN)予定", t)
        if mo:
            is_open = date(int(mo.group(1)), int(mo.group(2)), int(mo.group(3))).isoformat() <= today

        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": slug,
            "name": f"サンクチュアリゴルフ {name}",
            "pref": pref,
            "zip": zipc,
            "address": addr,
            "access": access_of(t),
            "tel": tel,
            "hours": hours,
            "open_24h": is24 if hours else None,
            "closed": closed,
            "bays": bays, "bays_num": bays_num,
            "private_room": private,
            "parking": parking_of(t),
            "monthly_fee": fee,
            "monthly_fee_source": fee_src,
            "equipment": "／".join(eq) if eq else None,
            "open": is_open,
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        s = stores[-1]
        print(f"  {s['name']} … {s['pref']} / 24h={s['open_24h']} / {s['bays']} / {s['equipment']} / P={s['parking']}", flush=True)

    out = DATA / "sanctuarygolf.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件（営業中 {sum(s['open'] for s in stores)}）→ {out}")
    for p in problems:
        print("  ⚠️", p)


if __name__ == "__main__":
    main()
