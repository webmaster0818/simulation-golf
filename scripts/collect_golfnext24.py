#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLF NEXT 24 の店舗データを公式の店舗一覧＋各店舗ページから取る。

一覧ページ1枚に全店舗の 住所・個室数・営業時間・駐車場 が載っている。
⚠️ 2026-10-16: 一覧だけ読んでいたため、店舗ページにある 電話番号・料金・機種・アクセス が
   「公式サイトに記載なし」になっていた。店舗ページ（一覧の「◯◯店のページはこちら」）も読む。
   - 店舗情報の <dl>: 住所・個室数・営業時間・電話番号・駐車場・その他。
     営業時間・電話番号は店舗ページの値を使う（一覧は「24時間営業/050-…」と1欄にまとめている）。
   - 「その他」に店ごとの機種（「シミュレーター２種（OKONGOLF：3台／GOLFNAVI：2台）」「シミュレーター：OKon／GOLFNAVI」）
     や駅からの道のり（「中川駅　徒歩9分」）が書いてある店がある。駅＋徒歩の文だけ access に入れる。
   - 機種の書いていない店も、店舗ページ本文に「OK ON GOLFでは10種の練習モードを搭載」とある → OK ON GOLF。
     ⚠️ この本文は店ごとに違う（狭山・橋本・相模原は「GOLF NAVIでは4種の練習モードを搭載」）。全店同じと決めつけない。
   - 料金は店舗ページの「PRICE 料金案内」（「一部店舗で料金とプランが異なります。各店舗ページをご覧ください」）。
     月会費に税込・税抜の表記は無い（入会金だけ「11,000円（税込）」）。
   - 定休日はどこにも書いていない → None（24時間営業から年中無休を作らない）。

⚠️ 書いていない項目は埋めない。「駐車場 有（提携）」のような曖昧表記も
   そのまま残す。台数に丸めると事実から離れる。
"""
import html as html_
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://golfnext24.jp/stores/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


def lines_of(html: str) -> list:
    """タグを落として空行を除いた行の並びにする。

    ⚠️ 住所は「〒300-0811」と「茨城県…」で改行されている店舗があるので、
       行に割ってから 住所〜Google MAP の間を連結して1つに戻す。
    """
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", "\n", t)
    return [x for x in (re.sub(r"[ \t　]+", " ", v).strip() for v in t.split("\n")) if x]


def zen2han(v: str) -> str:
    return v.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def field(ls: list, i: int, label: str, stop: tuple) -> str | None:
    """ls[i] 以降から label を探し、次の見出しが来るまでを値として返す。"""
    for j in range(i, min(i + 14, len(ls))):
        if ls[j] == label:
            vals = []
            for k in range(j + 1, len(ls)):
                if ls[k] in stop or ls[k] in LABELS:
                    break
                vals.append(ls[k])
            return "".join(vals) if label == "住所" else " ".join(vals)
    return None


LABELS = {"住所", "個室数", "営業時間", "駐車場", "店舗ページ", "Google MAP"}


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                           capture_output=True, text=True)
        if r.stdout and len(r.stdout) > 5000:
            return r.stdout
        time.sleep(3)
    return ""


def clean(s: str) -> str:
    return html_.unescape(re.sub(r"[ \t　\n]+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def store_info(h: str) -> dict:
    """店舗ページの最初の店舗情報 <dl>（住所〜その他）を dt→dd で読む。"""
    m = re.search(r"<dl[^>]*>\s*<dt>住所</dt>(.*?)</dl>", h, re.S)
    if not m:
        return {}
    out = {}
    for k, v in re.findall(r"<dt>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", "<dt>住所</dt>" + m.group(1), re.S):
        v = re.sub(r"<a [^>]*class=\"link_btn\".*?</a>", " ", v, flags=re.S)   # LINE公式アカウントのボタン
        out[clean(k)] = clean(v)
    return out


NAMES = [(r"OK\s?ON\s?GOLF|OKONGOLF|OKON|OKon", "OK ON GOLF"), (r"GOLF\s?NAVI|NAVI", "GOLFNAVI")]


def equipment(info: dict, page_text: str):
    other, rooms = info.get("その他", ""), info.get("個室数", "")
    eq = []
    m = re.search(r"シミュレーター(?:２種|2種)?[（(：:]\s*([^）)]+)", other)
    if m:
        for part in re.split(r"[／/、,]", m.group(1)):
            part = part.strip()
            for pat, name in NAMES:
                if re.match(pat, part):
                    n = re.search(r"(\d+)台", zen2han(part))
                    eq.append(f"{name}（{n.group(1)}台）" if n else name)
                    break
            else:
                if part:
                    print(f"    ⚠️ 見覚えのない機種: {part}")
    else:
        # 店舗ページの本文は店ごとに機種が違う（狭山・橋本・相模原は「GOLF NAVIでは4種の練習モードを搭載」）
        if "OK ON GOLFでは" in page_text:
            eq.append("OK ON GOLF")
        if "GOLF NAVIでは" in page_text:
            eq.append("GOLFNAVI")
    if "BIGTILT" in rooms:
        eq.append("BIGTILT（パットシミュレーター）")
    if "AIGIA" in other:
        eq.append("AIGIA（AI骨格診断）")
    return "／".join(eq) or None


def fees(page_lines: list):
    """PRICE 欄の月会費（使い放題3種＋月4の3種）。"""
    try:
        i, j = page_lines.index("PRICE"), page_lines.index("HOW TO USE")
    except ValueError:
        return None
    ls = page_lines[i:j]
    out = []
    starts = [k for k, v in enumerate(ls) if v == "月会費"]
    for k in starts:
        # 月会費の直前の見出し行がプラン名（「おすすめ」は飾り）
        names, b = [], k - 1
        while b > 0 and not re.search(r"利用料制|繰り越す", ls[b]):
            if ls[b] != "おすすめ":
                names.insert(0, ls[b])
            b -= 1
        vals = []
        for v in ls[k + 1:]:
            if not re.fullmatch(r"[\d,.]+円", v):
                break
            vals.append(re.sub(r"^(\d+)\.(\d{3})円$", r"\1,\2円", v))   # 公式の「6.600円」は 6,600円 の打ち間違い
        if len(names) == len(vals):
            out += [f"{n} {v}" for n, v in zip(names, vals)]
    if not out:
        return None
    entry = next((v for v in ls if v.startswith("入会金")), "")
    return ("／".join(out) + "（月会費・税込/税抜の別は公式サイトに記載なし"
            + (f"。{entry}" if entry else "") + "）")


def main() -> None:
    html = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, URL],
                          capture_output=True, text=True).stdout
    ls = lines_of(html)
    # 「◯◯店のページはこちら」→ 店舗ページURL
    urls = {clean(t): u for u, t in re.findall(r'<a href="(https://golfnext24\.jp/[^"]+)">([^<]*のページはこちら)</a>', html)}

    today, out = date.today().isoformat(), []
    for i, v in enumerate(ls):
        if v != "住所" or i == 0:
            continue
        name = ls[i - 1]
        addr = re.sub(r"\s+", "", field(ls, i, "住所", ("Google MAP",)) or "")
        zm = re.match(r"〒?(\d{3}-?\d{4})(.*)", addr)
        zipc, addr = (zm.group(1), zm.group(2)) if zm else (None, addr)
        pm = re.search(f"({PREF})", addr)
        rooms = field(ls, i, "個室数", ()) or ""
        hours = field(ls, i, "営業時間", ()) or ""
        rn = re.match(r"(\d+)", zen2han(rooms))
        # この店舗ブロックの「◯◯店のページはこちら」
        page_url = None
        for k in range(i, min(i + 20, len(ls))):
            if ls[k].endswith("のページはこちら"):
                page_url = urls.get(ls[k])
                break
        info, page_lines, page_text = {}, [], ""
        if page_url:
            ph = get(page_url)
            info = store_info(ph)
            page_lines = lines_of(ph)
            page_text = " ".join(page_lines)
            time.sleep(1.5)   # 公式サイトに負荷をかけない
        other = info.get("その他", "")
        acc = re.search(r"(\S+駅\S*\s*徒歩\s*\d+分)", other)
        tel = info.get("電話番号")
        out.append({
            "brand": "GOLF NEXT 24",
            "brand_slug": "golf-next-24",
            "name": re.sub(r"\s*（[^）]*）\s*$", "", name).strip(),
            "zip": zipc,
            "address": addr,
            "pref": pm.group(1) if pm else None,
            # このブランドは全店が完全個室。公式の項目名も「個室数」なので、
            # 打席数ではなく個室数として持つ（4打席ではなく4室）。
            "bays": f"個室{rooms}" if rooms else None,
            "bays_num": None,
            "private_room": True,
            "rooms": rooms,
            "rooms_num": int(rn.group(1)) if rn else None,
            "hours": info.get("営業時間") or hours,
            "open_24h": "24時間" in (info.get("営業時間") or hours),
            "parking": field(ls, i, "駐車場", ()) or "",
            "access": acc.group(1) if acc else None,
            "tel": tel,
            "closed": None,
            "monthly_fee": fees(page_lines),
            "equipment": equipment(info, page_text),
            "official": page_url,
            "source_url": page_url or URL,
            "fetched_at": today,
        })

    res = list({x["name"]: x for x in out}.values())
    (ROOT / "data" / "brand-golf-next-24.json").write_text(
        json.dumps({"brand": "GOLF NEXT 24", "source_url": URL, "fetched_at": today,
                    "count": len(res), "stores": res}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"GOLF NEXT 24: {len(res)}店舗")
    miss = [x["name"] for x in res if not x["pref"]]
    if miss:
        print(f"  ⚠️ 都道府県が取れない: {miss}")
    print(f"  24時間営業 {sum(1 for x in res if x['open_24h'])} / "
          f"個室数あり {sum(1 for x in res if x['rooms_num'])}")
    for x in res[:4]:
        print("   ", x["name"], "|", x["pref"], "|", x["rooms"], "|", x["parking"][:24])


main()
