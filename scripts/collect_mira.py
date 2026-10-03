#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MIRA GOLF（ミラフィットネス併設の24時間シミュレーションゴルフ・静岡/愛知/神奈川/山梨）を公式サイトから取る。

店舗一覧は https://golf.mirafitness.jp/ の末尾（section08）に静的HTMLで並ぶ。
  <p class="tit">静岡県｜藤枝志太店</p> / 住所 / 電話 / 「24時間営業」、リンク先が店舗ページ。
店舗ページ（shop.mirafitness.jp/detail/<slug>/ に正規化される）に
  〒・住所・電話番号・営業時間・施設・設備（「シミュレーションゴルフ」）・料金（ゴルフ会員ほか）・打席料・入会金がある。

⚠️ ジム併設のゴルフエリア。「ゴルフ会員」でゴルフエリアだけの利用ができ、ゲスト同伴も可なので
   indoor に入れる（誰でも使える）。ジム会員だけの店は入れない（店舗ページの設備に
   「シミュレーションゴルフ」が無ければ外す）。
⚠️ 打席数は店舗ページに無い → bays は None。機種はブランドトップに
   「OK ON GOLF / JOY GOLF SMART+（店舗により機種が異なる）」とあるだけで店舗ごとの確認が取れない → equipment は None。
⚠️ 一覧に「オープン準備室」の電話が書かれた店（甲府荒川・大井松田）は open=False（準備中）。
⚠️ 打席料は「店舗ごとに異なります」と公式が書いている。店舗ページの金額をそのまま入れ、無い店は入れない。

  python3 scripts/collect_mira.py            # 取得して data/mira.json に書く
  python3 scripts/collect_mira.py --limit 3  # 動作確認
"""
import argparse
import html
import json
import re
import subprocess
import time
import unicodedata
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
LIST_URL = "https://golf.mirafitness.jp/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "MIRA GOLF", "miragolf"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")

# 公式サイトの記載どうしが食い違っている箇所の直し。根拠を必ず書く。推測では直さない。
FIXES: dict[str, dict] = {}


def apply_fixes(store: dict) -> None:
    for k, v in FIXES.get(store["slug"], {}).items():
        if isinstance(v, tuple):
            if v[0] not in (store.get(k) or ""):
                print(f"  ⚠️ {store['name']}: 直す対象の記載が変わっている（{k}）。FIXES を見直す")
            store[k] = store[k].replace(v[0], v[1])
        else:
            store[k] = v


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


def lines(h: str) -> list[str]:
    """タグを改行に置き換えて行に分ける（店舗ページは見出し＋値が順に並ぶ）"""
    t = html.unescape(re.sub(r"[ \t　]+", " ", re.sub(r"<[^>]+>", "\n", strip_hidden(h))))
    return [x.strip() for x in t.split("\n") if x.strip()]


def listing() -> list[dict]:
    h = strip_hidden(get(LIST_URL))
    out = []
    # 一覧の各店は <div><a href="…"> または <div>\n<a href="…">（国吉田など4店は改行入り）
    for blk in re.split(r'<div>\s*<a href="', h)[1:]:
        url = blk.split('"', 1)[0]
        if "mirafitness.jp/shop/" not in url and "shop.mirafitness.jp/detail/" not in url:
            continue
        tit = re.search(r'class="tit">(.*?)</p>', blk, re.S)
        if not tit:
            continue
        ps = [text(p) for p in re.findall(r"<p>(.*?)</p>", blk, re.S)]
        pref, _, name = text(tit.group(1)).partition("｜")
        tel = next((p for p in ps if re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", p)), "")
        out.append({"url": url, "pref": pref, "name": name, "list_address": ps[0] if ps else "",
                    "list_tel": tel, "prep": "オープン準備室" in tel})
    return out


def parse_store(h: str) -> dict:
    L = lines(h)
    d: dict = {}

    def after(key: str, n: int = 1) -> list[str]:
        if key in L:
            i = L.index(key)
            return L[i + 1:i + 1 + n]
        return []

    a = after("住所", 2)
    if a:
        mz = re.match(r"〒\s*(\d{3})-?(\d{4})", a[0])
        if mz:
            d["zip"] = mz.group(1) + mz.group(2)
            d["address"] = a[1] if len(a) > 1 else None
        else:
            d["address"] = a[0]
    t = after("電話番号", 1)
    if t and re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", t[0]):
        d["tel"] = t[0]
    hs = after("営業時間", 4)
    if hs:
        # 「月〜日」「24時間営業」「スタッフアワー:11:00~15:00 16:00~20:00」「(金曜日・年末年始除く)」
        d["hours_raw"] = " ".join(hs)
        d["open_24h"] = "24時間" in d["hours_raw"]
        st = re.search(r"スタッフアワー[:：]?\s*([\d:~〜\-\s]+)", d["hours_raw"])
        note = re.search(r"\(([^)]*除く)\)", d["hours_raw"])
        hours = "24時間営業" if d["open_24h"] else hs[1] if len(hs) > 1 else hs[0]
        if st:
            hours += f"（スタッフアワー {st.group(1).strip().replace('~', '〜').replace(' ', '／')}"
            hours += f"、{note.group(1)}）" if note else "）"
        d["hours"] = hours
    # 施設・設備
    if "施設・設備" in L:
        i = L.index("施設・設備")
        j = L.index("サービス（取扱コンテンツ）") if "サービス（取扱コンテンツ）" in L[i:] else i + 8
        d["facilities"] = L[i + 1:j]
        k = L.index("マシンブランド") if "マシンブランド" in L[j:] else j + 30
        d["services"] = L[j + 1:k]
    # 設備一覧に「シミュレーションゴルフ」が無くても、ゴルフ別館の料金が載っていればゴルフ施設がある（富士宮弓沢）
    d["has_golf"] = ("シミュレーションゴルフ" in d.get("facilities", [])
                     or any(re.match(r"^ゴルフ(エリア|別館)利用プラン$", x) for x in L))
    d["parking"] = "無料駐車場" if "無料駐車場" in d.get("services", []) else None

    # ゴルフの料金。「ゴルフエリア利用プラン」以降の「◯◯会員」「・説明」「N円」「[税込M円]」の並び
    plans = []
    # 見出しは「ゴルフエリア利用プラン」が多いが、別棟の店は「ゴルフ別館利用プラン」（富士宮・犬山）
    head = next((x for x in L if re.match(r"^ゴルフ(エリア|別館)利用プラン$", x)), None)
    if head:
        i = L.index(head)
        seg = L[i + 1:i + 40]
        cur = None
        for x in seg:
            # 次の料金区分（■入会事務手数料／カフェラウンジエリア利用プラン）で止める
            if x.startswith("■") or (x.endswith("利用プラン") and "ゴルフ" not in x):
                break
            if x.startswith("※"):
                continue
            if re.search(r"会員$", x):
                cur = {"name": x}
            elif cur and re.match(r"\[税込([\d,]+)円\]", x):
                cur["fee"] = int(re.match(r"\[税込([\d,]+)円\]", x).group(1).replace(",", ""))
                plans.append(cur)
                cur = None
    d["plans"] = plans
    m = re.search(r"ゴルフ打席料（1回毎）\s*([\d,]+)円\s*\[税込([\d,]+)円\]", " ".join(L))
    d["bay_fee"] = int(m.group(2).replace(",", "")) if m else None
    if not m and re.search(r"打席料[^。]{0,10}無料", " ".join(L)):
        d["bay_fee"] = 0
    m = re.search(r"入会金\s+[\d,]+円\s*\[税込([\d,]+)円\]", " ".join(L))
    d["admission"] = int(m.group(1).replace(",", "")) if m else None
    m = re.search(r"登録事務手数料\s+[\d,]+円\s*\[税込([\d,]+)円\]", " ".join(L))
    d["registration"] = int(m.group(1).replace(",", "")) if m else None
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    items = listing()
    print(f"一覧 {len(items)}件（準備中 {sum(1 for x in items if x['prep'])}件）")
    today = date.today().isoformat()
    stores, problems = [], []
    for i, it in enumerate(items, 1):
        if a.limit and i > a.limit:
            break
        h = get(it["url"])
        d = parse_store(h) if h else {}
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', h or "")
        src = canon.group(1) if canon else it["url"]
        own = re.search(r"/(?:detail|shop)/([A-Za-z0-9_-]+)/?$", src)
        slug = own.group(1) if own else None
        if not h:
            problems.append(f"{it['name']}: 店舗ページが取れない（{it['url']}）")
        elif not d.get("has_golf"):
            problems.append(f"{it['name']}: 設備に「シミュレーションゴルフ」が無い → 入れない")
            continue
        # 公式の住所に全角数字が混ざる店がある（山梨田富「３６３４−２」）。NFKC で半角にそろえる
        addr = unicodedata.normalize("NFKC", d.get("address") or it["list_address"])
        addr = re.sub(r"(?<=\d)[−ー](?=\d)", "-", addr)
        mp = re.match(rf"({PREFS})", addr)
        pref = mp.group(1) if mp else it["pref"]
        fee = None
        if d.get("plans"):
            parts = [f"{p['name']} {p['fee']:,}円" for p in d["plans"]]
            extra = []
            if d.get("bay_fee") is not None:
                extra.append("打席料1回200円" if d["bay_fee"] == 200 else
                             ("打席料無料" if d["bay_fee"] == 0 else f"打席料1回{d['bay_fee']:,}円"))
            if d.get("admission") is not None:
                reg = f"＋登録事務手数料{d['registration']:,}円" if d.get("registration") else ""
                extra.append(f"入会金{d['admission']:,}円{reg}が別途")
            fee = "／".join(parts) + "（税込" + ("・" + "・".join(extra) if extra else "") + "）"
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG, "slug": slug,
            "name": f"MIRA GOLF {it['name']}",
            "pref": pref, "zip": d.get("zip"), "address": addr, "access": None,
            "tel": (d.get("tel") or (None if it["prep"] else it["list_tel"]) or None),
            "hours": d.get("hours") or ("24時間営業" if "24時間" in it.get("list_hours", "24時間営業") else None),
            "open_24h": d.get("open_24h", True), "closed": None,
            "bays": None, "bays_num": None, "private_room": None,
            "parking": d.get("parking"), "monthly_fee": fee,
            "equipment": None, "open": not it["prep"],
            "official": src, "source_url": src, "fetched_at": today,
        })
        apply_fixes(stores[-1])
        print(f"  {i:2d} {pref} {it['name']}  zip={d.get('zip')} tel={stores[-1]['tel']} "
              f"fee={'あり' if fee else '無し'} parking={d.get('parking')} open={not it['prep']}")
        time.sleep(1)

    out = DATA / "mira.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(stores)}件 → {out}")
    for p in problems:
        print("  ⚠️", p)


if __name__ == "__main__":
    main()
