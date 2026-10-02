#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""インドアゴルフクラブ（IGC・福井/北陸中心の会員制24時間インドアゴルフ）の店舗を公式サイトから取る。

店舗一覧 https://indoorgolfclub.jp/studio/ に ./stores/<slug>.html のリンクが並ぶ。
店舗ページの <th>/<td> に 店舗名・住所・電話番号・駐車場、
`store-detail__booth-panel` に打席（打席数と個室の別）、`card` に会員プランと月額会費がある。

⚠️ 営業時間という行は無い。会員プランごとに「利用時間」が書かれているので、
   24時間使えるプランがある店だけ open_24h を True にし、hours にはプランによる旨を添える。
⚠️ 機種（OK ON GOLF）はトップページにブランド全体の説明として書かれているだけで、
   店舗ページには無い。店舗ごとの確認が取れないので equipment は None のままにする。
   例外は三国店で、打席の欄に「トラックマンルーム」とあるのでトラックマンと入れる。
⚠️ 法人会員は月会費の一覧に入れない（個人で入会する人が比べる金額ではないため）。
   あることだけ末尾に添える。

  python3 scripts/collect_igc.py            # 取得して data/igc.json に書く
  python3 scripts/collect_igc.py --limit 3  # 動作確認
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
BASE = "https://indoorgolfclub.jp"
LIST_URL = f"{BASE}/studio/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "インドアゴルフクラブ", "igc"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


# 公式サイトの記載どうしが食い違っている箇所の直し。郵便番号検索（zipcloud）で突き合わせて見つけた。
# ⚠️ 「公式に書いてあることだけ載せる」の例外なので、根拠を必ず書く。推測では直さない。
FIXES = {
    # 住所が「越前町大屋町」だが、同じページの郵便番号 915-0042 は越前市大屋町。
    # 越前町（丹生郡）は別の自治体で、そのまま載せるとエリア集計で別の町に入る。
    "takefu": {"address": ("福井県越前町大屋町", "福井県越前市大屋町")},
    # 郵便番号が kyusyu 店と同じ 880-0946（＝宮崎市福島町）。青葉町の番号ではないので載せない。
    "aoba": {"zip": None},
}


def apply_fixes(store: dict) -> None:
    for k, v in FIXES.get(store["slug"], {}).items():
        if isinstance(v, tuple):
            if v[0] not in store[k]:
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


def rows(page_html: str) -> dict:
    out = {}
    for m in re.finditer(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", page_html, re.S):
        k, v = text(m.group(1)), text(m.group(2))
        if k and v and k not in out:
            out[k] = v
    return out


def booths(page_html: str) -> tuple[str | None, int | None, str | None]:
    """打席の表記・合計・店舗ページに書かれた機種。公式の書き方をそのまま並べる。

    ⚠️ 書き方が店ごとに違う（「3打席(右打)」「計4打席（右打3／両打1）」「1室のみ」、
       打席数の札が無く「1番打席 両打ち半個室」だけの店もある）。
       合計は、全部の札が「N打席」と読めるときだけ出す。読めない札が1つでもあれば None。
    """
    i, j = page_html.find('class="store-detail__booth"'), page_html.find("store-detail__middle")
    if i < 0:
        return None, None, None
    seg = page_html[i:j if j > i else None]
    parts, nums = [], []
    for blk in re.split(r'<div class="store-detail__booth-panel">', seg)[1:]:
        label = re.search(r'booth-label">(.*?)</p>', blk, re.S)
        fig = re.search(r'booth-figure">(.*?)</p>', blk, re.S)
        lab = text(label.group(1)) if label else ""
        fg = text(fig.group(1)) if fig else ""
        if not (lab or fg):
            continue
        part = f"{fg}：{lab}" if (lab and fg) else (fg or lab)
        if part not in parts:
            parts.append(part)
            m = re.match(r"計?\s*(\d+)\s*打席", lab)
            nums.append(int(m.group(1)) if m else None)
    if not parts:
        # 札の無い店は booth-figure だけが並ぶ
        for fig in re.findall(r'booth-figure">(.*?)</p>', seg, re.S):
            fg = text(fig)
            if fg and fg not in parts:
                parts.append(fg)
        nums = [None]
    total = sum(nums) if nums and all(n is not None for n in nums) else None
    equip = "トラックマン" if "トラックマン" in text(seg) else None
    return ("／".join(parts) or None), total, equip


def plans(page_html: str) -> list[dict]:
    out = []
    for c in re.split(r'<div class="card card--', page_html)[1:]:
        name = re.search(r'card__title-ja">(.*?)</p>', c, re.S)
        area = (re.search(r'card__area">(.*?)</p>', c, re.S)
                or re.search(r'card__discription">(.*?)</p>', c, re.S))
        price = re.search(r'card__price">(.*?)</p>', c, re.S)
        hours = re.search(r'card__label">\s*利用時間\s*</p>(.*?)</div>', c, re.S)
        if not (name and price):
            continue
        m = re.search(r"([\d,]+)\s*円", text(price.group(1)))
        if not m:
            continue
        out.append({"name": text(name.group(1)), "fee": int(m.group(1).replace(",", "")),
                    "area": text(area.group(1)) if area else None,
                    "hours": text(hours.group(1)) if hours else None})
    # 同名プランが複数ある店（武生店のゴールド会員）は、利用できる範囲を添えて区別する
    #   範囲の説明まで同じ（かほく店のジュニア会員1が2つ）なら、公式の表記のまま並べる。
    names = [p["name"] for p in out]
    for p in out:
        same = [q for q in out if q is not p and names[out.index(q)] == names[out.index(p)]]
        if same and p["area"] and all(q["area"] != p["area"] for q in same):
            p["name"] = f'{p["name"]}（{p["area"]}）'
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reapply", action="store_true", help="取得し直さず FIXES だけ当て直す")
    a = ap.parse_args()

    if a.reapply:
        out = DATA / "igc.json"
        d = json.loads(out.read_text(encoding="utf-8"))
        for s in d["stores"]:
            apply_fixes(s)
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"当て直し {len(d['stores'])}件 → {out}")
        return

    listing = strip_hidden(get(LIST_URL))
    paths = list(dict.fromkeys(re.findall(r'href="\./(stores/[^"]+\.html)"', listing)))
    print(f"店舗ページ {len(paths)}件")

    today = date.today().isoformat()
    stores, problems = [], []
    for i, path in enumerate(paths, 1):
        if a.limit and i > a.limit:
            break
        url = f"{LIST_URL}{path}"
        h = strip_hidden(get(url))
        r = rows(h)
        addr = r.get("住所")
        if not addr:
            problems.append(f"{path}: 住所なし")
            continue
        zipc = None
        mz = re.match(r"〒?\s*(\d{3})-?(\d{4})\s*", addr)
        if mz:
            zipc = mz.group(1) + mz.group(2)
            addr = addr[mz.end():].strip()
        mp = re.match(rf"({PREFS})", addr)
        # 店名は「インドアゴルフクラブ文京店(IGC文京店)」。カッコ内の短い表記を使う
        full = r.get("店舗名", "")
        mn = re.search(r"[（(]\s*(IGC[^）)]+)[）)]", full)
        name = mn.group(1).strip() if mn else full
        bays, bays_num, equip = booths(h)
        pl = plans(h)
        personal = [p for p in pl if "法人" not in p["name"]]
        fee = None
        if personal:
            seen, items = set(), []
            for p in personal:
                key = (p["name"], p["fee"])
                if key not in seen:
                    seen.add(key)
                    items.append(f'{p["name"]} {p["fee"]:,}円')
            ent = re.search(r"入会金[^<]*</p>\s*<p>([\d,]+)", h)
            tail = "税込"
            if ent:
                tail += f"・入会金{ent.group(1)}円が別途"
            if len(personal) < len(pl):
                tail += "・ほかに法人会員あり"
            fee = "／".join(items) + f"（{tail}）"
        any24 = any(p["hours"] and "24時間" in p["hours"] for p in pl)
        limited = any(p["hours"] and "24時間" not in p["hours"] for p in pl)
        hours = None
        if any24:
            hours = "24時間（利用できる時間は会員プランによる）" if limited else "24時間"
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": path.rsplit("/", 1)[-1].replace(".html", ""),
            "name": name,
            "pref": mp.group(1) if mp else None,
            "zip": zipc,
            "address": addr,
            "access": None,
            "tel": r.get("電話番号"),
            "hours": hours,
            "open_24h": True if any24 else None,
            "closed": None,
            "bays": bays, "bays_num": bays_num,
            "private_room": None,
            "parking": r.get("駐車場"),
            "monthly_fee": fee,
            "equipment": equip,
            "open": True,
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        s = stores[-1]
        apply_fixes(s)
        if not pl:
            problems.append(f"{name}: 会員プランが取れなかった（{url}）")
        if not bays:
            problems.append(f"{name}: 打席が取れなかった（{url}）")
        print(f"  {i:2}/{len(paths)} {s['name']} … {s['pref'] or '県不明'} / {s['bays']} / {s['hours']} / {s['monthly_fee']}")
        time.sleep(2)   # 公式サイトに負荷をかけない

    out = DATA / "igc.json"
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
