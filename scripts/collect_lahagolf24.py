#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ラハゴルフ24 の店舗データを各店舗ページから取る。

店舗ページに 店舗名／住所／営業時間／アクセス／電話番号／月会費 が並ぶ。
**月会費が店舗ごとに載っている数少ないブランド**なので、料金比較の実データになる。

⚠️ 定休日・機種・打席数は「店舗情報」の表には無い（2026-10-16 に取りこぼしを直した）:
   - 定休日: 店舗ページ上部のアイコン列（ul.service_list の img alt）に「年中無休」がある店だけ closed="年中無休"。
     FAQ にも「定休日はありますか？→施設は24時間年中無休でご利用いただけます。」（/faq/）。
   - 機種・打席: タブ「シミュレーター紹介」（div.detai_list の4つ目）の「…を N台設置」「設置シミュレーター 全N台」等。
     bays_num は ①ページ内の「全N打席／全N台」「N打席完備/設置」 ②機種の行が1つならその台数（「うち1台は…」の内訳は数えない）
     ③全機種の行に台数があるときだけ合計（AIGIA＝スイング分析機・TOURPUTT＝パター専用は数えない）。
     どれにも当たらない店（「全打席に設置」だけ等）は None。
     ⚠️ 西調布店は「・全11打席 調布市最大級」と「EXpand GOLFシミュレーターを9台設置」が並ぶ。打席の合計の記載（11）を採る。
   - 個室: 「完全個室」「個室打席」と書いてある店だけ private_room=True（半個室だけの店は None）。
⚠️ 月会費は「10,900円（税抜）」「11,990円(税込)」と税表記が店舗で揃っていない。
   数値だけ取り出さず、税表記ごとそのまま残す（税抜と税込を並べて比べさせない）。
"""
import json
import re
import subprocess
import time
import unicodedata
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = "https://laha-golf24.com/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")
LABELS = ["店舗名", "住所", "地図", "営業時間", "アクセス", "電話番号", "メールアドレス", "月会費"]
KEY = {"地図": None, "店舗名": "name", "住所": "address", "営業時間": "hours", "アクセス": "access",
       "電話番号": "tel", "メールアドレス": "email", "月会費": "monthly_fee"}


# 公式のURLが日本語のままの店舗が1件ある（/list/横浜東口店/）。
# 日本語のURLは共有やログで壊れやすいので、こちらでローマ字を割り当てる。
SLUG_FIX = {"横浜東口店": "yokohama-higashiguchi"}


def slug_of(url: str) -> str:
    raw = urllib.parse.unquote(url.rstrip("/").rsplit("/", 1)[-1])
    return SLUG_FIX.get(raw, raw)


def _split_outside_parens(s: str, seps: str) -> list:
    out, buf, depth = [], "", 0
    for ch in s:
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth = max(0, depth - 1)
        if ch in seps and depth == 0:
            if buf.strip():
                out.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf.strip())
    return out


def parking_from_access(access: str | None) -> str | None:
    """このブランドは公式の「アクセス」欄に駐車場の案内を混ぜて書いている。

    例: 「茅ヶ崎駅南口より徒歩5分 駐車場2台 駐輪場5台有」
    駐車場の有無で絞り込めるようにしたいので、駐車場に触れている部分だけを
    取り出して parking にも入れる。⚠️ 原文は access にそのまま残す（改変しない）。
    ⚠️ 括弧の中や「自転車/バイク」の「/」で切ると文が途中で切れる（相模原千代田・浦和）。
       空白（括弧の外）で区切り、駐車に触れた塊は「、」の前の駅の案内だけ落とす。
    """
    if not access or "駐車" not in access:
        return None
    hit = []
    for tok in _split_outside_parens(access, " 　"):
        if "駐車" not in tok:
            continue
        parts = _split_outside_parens(tok, "、,")
        k = next(i for i, x in enumerate(parts) if "駐車" in x)
        hit.append("、".join(parts[k:]))
    return " ".join(hit) if hit else access


# 機種の表記ゆれ → 載せる名前。⚠️ 既知のものだけ通す（CLAUDE.md「本文の『…』を機種名として拾うと…」）
MACHINES = [
    (r"EXpand\s*GOLF|EXPANDGOLF", "EXpand GOLF"),
    (r"DITECT|ディテクト|Golf swing better|POD", "DITECT"),
    (r"GOLF\s*NAVI|Golf navi|ゴルフナビ", "GOLF NAVI"),
    (r"TWOVISION\s*NX", "TWOVISION NX"),
    (r"UNEEKOR|ユニコ", "UNEEKOR EYE XO"),
    (r"TOURPUTT", "TOURPUTT（パター専用）"),
]
NOT_BAY = ("TOURPUTT", "AIGIA")   # 打席に数えない（パター専用・スイング分析機）
ICON_MACHINE = {"DITECT": "DITECT", "ゴルフナビ": "GOLF NAVI"}


def nk(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def tabs_of(html: str) -> list:
    """div.detai_list の子 div（店舗情報・お知らせ・キャンペーン・シミュレーター紹介）を行のリストで返す。"""
    i = html.find('<div class="detai_list">')
    if i < 0:
        return []
    return [lines_of(p) for p in re.split(r"\n\t\t\t<div>", html[i:])[1:]]


def icons_of(html: str) -> list:
    m = re.search(r'<ul class="service_list">([\s\S]*?)</ul>', html)
    return list(dict.fromkeys(re.findall(r'alt="([^"]+)"', m.group(1)))) if m else []


def machines(html: str, all_lines: list) -> tuple:
    """(equipment, bays, bays_num) をシミュレーター紹介タブとページ本文から。"""
    tabs = tabs_of(html)
    sim = [x for x in (tabs[3] if len(tabs) > 3 else []) if x != "店舗一覧に戻る"]
    # 「Golf navi(ゴルフナビ社）」の次の行が「9台」だけ、という書き方がある（川崎南幸町）
    merged = []
    for x in sim:
        if merged and re.fullmatch(r"\d+\s*台", nk(x)):
            merged[-1] += " " + x
        else:
            merged.append(x)
    names, mlines = [], []
    for x in merged:
        if re.search(r"こちら|https?://|使い方", x):
            continue
        found = [n for pat, n in MACHINES if re.search(pat, x, re.I)]
        for n in found:
            if n not in names:
                names.append(n)
        if found or re.search(r"全\s*\d+\s*台", nk(x)) or any(w in x for w in NOT_BAY):
            mlines.append(x)
    for ic in icons_of(html):
        if ic in ICON_MACHINE and ICON_MACHINE[ic] not in names:
            names.append(ICON_MACHINE[ic])
    equipment = "／".join(names) or None

    # 台数
    total, total_line = None, None
    for x in all_lines:
        if "予定" in x:   # 「●6打席設置予定」（武蔵新城）は開業前の告知の残り
            continue
        m = (re.search(r"全\s*(\d+)\s*(?:打席|台)", nk(x))
             or re.search(r"(\d+)\s*打席\s*(?:完備|設置)", nk(x)))
        if m:
            total, total_line = int(m.group(1)), x.lstrip("・●◎ ")
            break
    # 「さらにうち1台はGOLF NAVI GTR…」（下北沢）は内訳なので数えない
    counted = [x for x in mlines if not any(w in x for w in NOT_BAY) and "うち" not in x
               and [n for pat, n in MACHINES if re.search(pat, x, re.I)]]
    nums = [re.search(r"(\d+)\s*台", nk(x)) for x in counted]
    if total is None and counted and all(nums):
        total = sum(int(m.group(1)) for m in nums)
    bays_parts = ([total_line] if total_line and total_line not in mlines else []) + \
                 [x for x in mlines if "AIGIA" not in x and re.search(r"\d+\s*(?:台|打席)", nk(x))]
    bays = "／".join(bays_parts) or None
    return equipment, bays, total


def get(url: str) -> str:
    return subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                          capture_output=True, text=True).stdout


def lines_of(html: str) -> list:
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip()
                        for v in re.sub(r"<[^>]+>", "\n", t).split("\n")) if x]


def main() -> None:
    idx = get(LIST)
    urls = sorted(set(re.findall(r"https://laha-golf24\.com/list/[^\"'\s]+/", idx)))
    print(f"店舗ページ: {len(urls)}件")

    today, out, ng = date.today().isoformat(), [], []
    for n, u in enumerate(urls, 1):
        page = get(u)
        ls = lines_of(page)
        rec, i = {}, 0
        while i < len(ls):
            if ls[i] in LABELS:
                vals = []
                for k in range(i + 1, len(ls)):
                    if ls[k] in LABELS or ls[k] == "店舗一覧に戻る":
                        break
                    vals.append(ls[k])
                if KEY[ls[i]]:
                    rec[KEY[ls[i]]] = vals
                i += len(vals) + 1
            else:
                i += 1
        if "address" not in rec:
            ng.append(u); time.sleep(2); continue
        # 住所は「336-0021」と「埼玉県…」の2行に分かれている
        parts = rec["address"]
        zipc = next((p.replace("〒", "") for p in parts
                     if re.fullmatch(r"〒?\d{3}-?\d{4}", p)), None)
        addr = "".join(p for p in parts if not re.fullmatch(r"〒?\d{3}-?\d{4}", p))
        pm = re.search(f"({PREF})", addr)
        equipment, bays, bays_num = machines(page, ls)
        access = " ".join(rec.get("access", [])) or None
        # 駐車場をアクセス欄ではなく住所の欄に書いている店がある（藤沢遠藤「…3F 無料駐車場5台完備」）
        parking = parking_from_access(access) or parking_from_access(addr)
        joined = " ".join(ls)
        private = True if re.search(r"完全個室|個室打席", joined) else None
        out.append({
            "brand": "ラハゴルフ24", "brand_slug": "lahagolf24",
            "name": (rec.get("name") or [u])[0],
            "slug": slug_of(u),
            "zip": zipc, "address": addr, "pref": pm.group(1) if pm else None,
            "hours": " ".join(rec.get("hours", [])) or None,
            "open_24h": "24時間" in " ".join(rec.get("hours", [])),
            "access": access,
            "parking": parking,
            "closed": "年中無休" if "年中無休" in icons_of(page) else None,
            "bays": bays, "bays_num": bays_num, "private_room": private,
            "equipment": equipment,
            "tel": next((p for p in rec.get("tel", []) if re.match(r"^0\d", p)), None),
            "monthly_fee": (rec.get("monthly_fee") or [None])[0],
            "source_url": u, "fetched_at": today,
        })
        if n % 5 == 0 or n == len(urls):
            print(f"  [{n}/{len(urls)}]", flush=True)
        time.sleep(2)

    (ROOT / "data" / "brand-lahagolf24.json").write_text(
        json.dumps({"brand": "ラハゴルフ24", "source_url": LIST, "fetched_at": today,
                    "count": len(out), "stores": out, "failed": ng},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ラハゴルフ24: {len(out)}店舗 / 取得失敗 {len(ng)}")
    for k in ("address", "pref", "hours", "access", "tel", "monthly_fee",
              "closed", "bays", "bays_num", "private_room", "parking", "equipment"):
        print(f"  {k}: {sum(1 for x in out if x.get(k))}/{len(out)}")
    for x in out[:4]:
        print("   ", x["name"], "|", x["pref"], "|", x["monthly_fee"], "|", x["hours"])
    for x in out:
        print("   ", x["slug"], "|", x["equipment"], "|", x["bays_num"], "|", x["bays"], "|", x["parking"], "|", x["private_room"])


main()
