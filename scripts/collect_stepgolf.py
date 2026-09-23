#!/usr/bin/env python3
"""ステップゴルフ（www.stepgolf.co.jp）の店舗を収集する。

⚠️ CLAUDE.md に「店舗ページの住所がJavaScriptで描画される／ブラウザを動かせば取れるが
   149ページぶんかかる」と書いてあったが、2026-09-23に実測したら**両方とも違った**。
   - 店舗一覧 https://www.stepgolf.co.jp/store/ に**全店の店名と住所がHTMLで入っている**
     （`storeList__listItemLinkHeader` と `storeList__listItemLinkTxt`）。
   - 店舗ページの住所も curl でそのまま取れる。JS描画ではない。
   当時の調査時はドメインを step-golf.co.jp と誤っていた可能性が高い（正は stepgolf.co.jp）。

⚠️ 業態がこのサイトの他の施設と違う。ステップゴルフは**完全予約制・コーチ付き・月会費制の
   レッスンスクール**で、自分の好きな時間に打ちに行く場所ではない。
   ただし全店に**弾道測定機（スカイトラック）とスイング解析機**があると公式が明記しており、
   「弾道を計測できる屋内施設」という軸では対象に入る。
   そこで segment を 'lesson' として、屋内シミュレーションゴルフ（indoor）や
   弾道計測つき練習場（range）と**混ぜずに区別する**。探している人の目的が違う。
"""
import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.stepgolf.co.jp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CACHE = ROOT / "data" / ".stepgolf-cache"


def fetch(url, timeout=40):
    import hashlib
    cp = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    if cp.exists():
        return cp.read_text(encoding="utf-8", errors="ignore")
    r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True, timeout=timeout + 15)
    h = r.stdout or ""
    if len(h) > 5000:
        CACHE.mkdir(parents=True, exist_ok=True)
        cp.write_text(h, encoding="utf-8")
    return h


def text_of(html):
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html)
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


PREFS = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県",
         "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県",
         "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府",
         "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県",
         "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県",
         "鹿児島県", "沖縄県"]


# 住所に都道府県が書かれていない店がある（例:「横浜市港北区新羽町…」）。
# 推測できる市名だけを表にする。表に無いものは補わない（当てずっぽうで県名を作らない）。
CITY_PREF = {"横浜市": "神奈川県", "川崎市": "神奈川県", "相模原市": "神奈川県",
             "名古屋市": "愛知県", "大阪市": "大阪府", "京都市": "京都府", "神戸市": "兵庫県",
             "札幌市": "北海道", "仙台市": "宮城県", "さいたま市": "埼玉県", "千葉市": "千葉県",
             "広島市": "広島県", "福岡市": "福岡県", "北九州市": "福岡県", "岡山市": "岡山県",
             "熊本市": "熊本県", "新潟市": "新潟県", "静岡市": "静岡県", "浜松市": "静岡県",
             "堺市": "大阪府"}

ZIP = re.compile(r"^〒?\s*(\d{3}-?\d{4})\s*")


def split_zip(addr):
    """先頭の郵便番号を住所から切り離す。〒が付くものと付かないものが混在している。"""
    m = ZIP.match(addr)
    if not m:
        return None, addr
    z = m.group(1)
    z = z if "-" in z else f"{z[:3]}-{z[3:]}"
    return z, addr[m.end():].strip()


def pref_of(addr):
    for p in PREFS:
        if addr.startswith(p):
            return p
    for city, p in CITY_PREF.items():
        if addr.startswith(city):
            return p
    return None


def parse_index(html):
    """店舗一覧から 店名 / 住所 / URL を取る。住所は一覧に載っているものを正とする。"""
    out = []
    for m in re.finditer(
        r'<a class="storeList__listItemLink" href="([^"]+)">\s*'
        r'<span class="storeList__listItemLinkHeader">(.*?)</span>\s*'
        r'<p class="storeList__listItemLinkTxt">(.*?)</p>', html, re.S):
        url, name, addr = m.group(1), text_of(m.group(2)).strip(), text_of(m.group(3)).strip()
        out.append({"url": url, "name": name, "address": addr})
    return out


# 営業時間の書式は店ごとに揺れる（【】と［］、「□ レッスンタイム」の有無）。
# 形を決め打ちせず、「営業時間」から「住所」までを原文のまま持つ。
HOURS = re.compile(r"営業時間\s*(.{4,200}?)\s*住所\s")
TEL = re.compile(r"(0\d{1,4}-\d{1,4}-\d{3,4})")
FEE = re.compile(r"([^ ]{0,14}プラン)\s*([0-9,]+円\(税込[0-9,]+円\))")


def parse_store(html):
    t = text_of(html)
    d = {}
    m = HOURS.search(t)
    if m:
        # 店によってはセルフタイム（レッスン以外に打てる時間）も書かれていて、そこが肝心。
        # 途中で切ると意味が変わるので、切るときは区切り文字の手前までにする。
        h = re.sub(r"^□\s*", "", m.group(1).strip())
        if len(h) > 160:
            cut = max(h.rfind("】", 0, 160), h.rfind("］", 0, 160), h.rfind("）", 0, 160))
            h = h[:cut + 1] if cut > 60 else h[:160]
        d["hours"] = h
    m = TEL.search(t)
    if m:
        d["tel"] = m.group(1)
    fees = FEE.findall(t)
    if fees:
        # 最安のプランを月会費として持つ（公式表記のまま。円だけの行は作らない）
        cheapest = min(fees, key=lambda x: int(re.sub(r"[^0-9]", "", x[1].split("(")[0])))
        d["monthly_fee"] = f"{cheapest[0]} {cheapest[1]}"
    # ⚠️ 「オープン準備中」はサイト共通のヘッダ/フッタ（「※掲載の店舗数はオープン準備中の
    #    数値を含みます」）に必ず出てくる。これを店舗の状態として読むと**全150店が準備中**に
    #    なる（実際にそうなった）。店舗一覧に載っている店は営業中として扱い、
    #    準備中の判定は店名/見出しに明示があるときだけにする。
    d["open"] = not re.search(r"(近日オープン|OPEN予定|オープン予定)", t)
    return d


def main():
    idx = fetch(f"{BASE}/store/")
    if len(idx) < 50000:
        print("店舗一覧を取得できませんでした", file=sys.stderr)
        return 1
    stores = parse_index(idx)
    print(f"一覧から {len(stores)}店")

    out = []
    for i, s in enumerate(stores, 1):
        h = fetch(s["url"])
        extra = parse_store(h) if len(h) > 5000 else {}
        zipcode, addr = split_zip(s["address"])
        pref = pref_of(addr)
        rec = {
            "segment": "lesson",
            "brand": "ステップゴルフ",
            "brand_slug": "stepgolf",
            "name": s["name"],
            "pref": pref,
            "zip": zipcode,
            "address": addr,
            "tel": extra.get("tel"),
            "hours": extra.get("hours"),
            "open_24h": False,          # 完全予約制のスクール。24時間営業ではない
            "monthly_fee": extra.get("monthly_fee"),
            # 公式が全店「弾道測定機（スカイトラック）・スイング解析機 完備」と明記
            "equipment": "スカイトラック（弾道測定機）",
            "open": extra.get("open", True),
            "official": s["url"],
            "source_url": s["url"],
            "fetched_at": date.today().isoformat(),
        }
        out.append(rec)
        if i % 25 == 0 or i == len(stores):
            print(f"  {i}/{len(stores)}")
        if not (CACHE / "x").exists():
            time.sleep(0.4)

    p = ROOT / "data" / "stepgolf.json"
    p.write_text(json.dumps({"generated_at": date.today().isoformat(),
                             "count": len(out), "stores": out}, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    ok = sum(1 for x in out if x["pref"])
    print(f"\n保存: {p} ({len(out)}店 / 都道府県を取れた {ok}店 / "
          f"営業時間 {sum(1 for x in out if x['hours'])} / 電話 {sum(1 for x in out if x['tel'])} / "
          f"月会費 {sum(1 for x in out if x['monthly_fee'])})")
    miss = [x["name"] for x in out if not x["pref"]]
    if miss:
        print("  都道府県を取れなかった店（住所の書式が違う）:", miss[:5])
    return 0


if __name__ == "__main__":
    sys.exit(main())
