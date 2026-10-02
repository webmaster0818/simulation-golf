#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""マイゴルフレーン（マイゴル・会員制の定額インドアゴルフ練習場）の店舗を公式サイトから取る。

店舗検索 https://www.mygol.jp/shop/ に /shop/<slug>/ のリンクが並ぶ。
店舗ページの `<div id="information">` の <dt>/<dd> に 営業時間・住所・電話番号・アクセス・駐車場、
`shop-price-list__item` に月額（定額練習し放題／回数制）がある。

⚠️ 一覧には /range/shop/<slug>.php という別形式のページ（都内の一部店舗）も混ざる。
   作りが違って同じ読み方ができないので取らない。件数だけ表示する。
⚠️ 月額は税抜の大きな数字と「（基本プラン・税込10,000円）」が並んでいる。載せるのは税込のほう。
⚠️ 打席数・個室・機種は店舗情報の欄に無い（特徴の文章にだけ出てくる）ので None のままにする。
⚠️ 公式に書いていない項目は None のままにする。推測で埋めない。

  python3 scripts/collect_mygol.py            # 取得して data/mygol.json に書く
  python3 scripts/collect_mygol.py --limit 3  # 動作確認
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
}


def get(url: str) -> str:
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
    """
    y0, m0, d0 = (int(x) for x in today.split("-"))
    dates = []
    for m in re.finditer(r"(\d{4})年(\d{1,2})月(?:(\d{1,2})日)?(上旬|中旬|下旬)?\s*(?:に)?(?:グランド)?(?:オープン|OPEN)予定", page_text):
        dates.append((int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None))
    for m in re.finditer(r"(?<![\d年])(\d{1,2})[月/](\d{1,2})日?\s*(?:オープン|OPEN)予定", page_text):
        dates.append((y0, int(m.group(1)), int(m.group(2))))
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="このslug（カンマ区切り）だけ取り直して保存済みの結果に上書きする")
    a = ap.parse_args()
    only = {x for x in a.only.split(",") if x}

    listing = strip_hidden(get(LIST_URL))
    all_links = list(dict.fromkeys(
        re.findall(r'href="((?:https://www\.mygol\.jp)?/(?:range/)?shop/[^"#?]+)"', listing)))
    paths = [l for l in all_links if re.search(r"/shop/[a-z0-9_-]+/?$", l) and "/range/" not in l]
    other = [l for l in all_links if "/range/shop/" in l]
    print(f"店舗ページ {len(paths)}件（別形式で取らないページ {len(other)}件）")

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
            "closed": r.get("定休日"),
            "bays": None, "bays_num": None,
            "private_room": None,
            "parking": r.get("駐車場"),
            "monthly_fee": fee(h),
            "equipment": None,
            "open": opened,
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        s = stores[-1]
        s.update(FIXES.get(s["slug"], {}))
        if not s["monthly_fee"]:
            problems.append(f"{name}: 月額が取れなかった（{url}）")
        print(f"  {i:2}/{len(paths)} {s['name']} … {s['pref'] or '県不明'} / {s['hours']} / {s['monthly_fee']}"
              f"{'' if opened else ' / 準備中'}", flush=True)
        time.sleep(2)   # 公式サイトに負荷をかけない

    out = DATA / "mygol.json"
    if only:
        prev = json.loads(out.read_text(encoding="utf-8"))["stores"]
        fresh = {x["slug"]: x for x in stores}
        stores = [fresh.get(x["slug"], x) for x in prev]
        for x in stores:
            x.pop("opening_hint", None)
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
