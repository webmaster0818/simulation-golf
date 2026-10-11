#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SWING24/7 の店舗データを公式の店舗一覧から取る。

一覧ページ1枚に全店舗が載っている。1店舗は <li> 1つで、
  <h3>店名 → (スケジュール span) → 住所 p.txt_l → 経路 p.icon.root → 駐車場 p.icon.parking → 電話 → リンク
の順。住所・経路は <br> で2行に割れている店舗がある。

⚠️ 「近日オープン予定」の店舗は open=False で持ち、掲載時に既存店と混ぜない。
   オープン前を営業中として数えるのは、利用者にとって実害のある誤りになる。
"""
import json
import re
import subprocess
from datetime import date
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
    html = curl(URL)
    today, out = date.today(), []
    for name, block in re.findall(r"<h3>(SWING24/7[^<]*店)</h3>([\s\S]*?)</li>", html):
        r = parse(block)
        rec = {
            "brand": "SWING24/7", "brand_slug": "swing247", "name": name.strip(),
            **{k: r[k] for k in ("zip", "address", "pref", "parking", "tel", "open", "note")},
            "access": r["access"],
            # 公式が全店「24時間365日・無人」と明記しているブランド
            "hours": "24時間365日（無人運営）", "open_24h": True,
            "source_url": URL, "fetched_at": today.isoformat(),
        }
        if not r["open"]:
            said = opened_on_store_site(r["site"], today)
            if said:
                rec.update(open=True, open_source_url=r["site"],
                           note=f"一覧は「{r['note']}」のまま。店舗公式サイトに「{said}」")
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
