#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLFERS24 の店舗データを公式の店舗一覧から取る。

一覧ページに「店名 → 〒 → 住所」が並ぶだけの単純な作り。
営業時間・個室の有無は一覧に無いので取らない（ブランド共通の説明文から
推測して各店に書くと、実際と違う店が出る）。

2026-10-16 追加: 一覧の各店リンク（/store/<地域>/<店>）の店舗ページに「店舗情報」表
（TEL・住所・アクセス・営業時間・駐車場・ブース数・その他）と店舗別の料金プランがある。
一覧の店と店舗ページは郵便番号で突き合わせる（店名・住所は一覧のまま）。
- closed: 公式FAQ（/questions）「定休日はありますか？」→「定休日はなく、原則として365日・24時間・
  年中無休でご利用いただけます。」= 全店に当てる（note に出典）。
- equipment: 公式FAQ「シミュレーターマシンの特徴は？」→「世界シェアNo.1メーカー、GOLFZONのマシンを
  設置しています。」と「※大森山王店のみ…GC3…」。例外が名指しなので、それ以外の店は GOLFZON。
- private_room: 各店舗ページの特徴欄「全店舗で完全個室ご用意。」= 全店 true（ブース数の原文は bays に残す）。
- monthly_fee: 店舗ページの「月額 N 円 (税込)」のプラン（レギュラー・年割・VIP 等）を店の表記のまま。
  曜日・時間指定プラン・回数券プランは件数が多いので「ほかに…あり」とだけ書く。
- TEL は全店同じ番号（03-4400-6499）が店舗ページに載っている。
"""
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://www.golfers24.jp/store"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PREF = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|"
        "神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|"
        "大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|"
        "福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


BASE = "https://www.golfers24.jp"
FAQ = BASE + "/questions"
LABELS = ("店舗名", "TEL", "住所", "アクセス", "Mail", "営業時間", "駐車場", "ブース数", "その他")


def get(url: str) -> str:
    return subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                          capture_output=True, text=True).stdout


def lines_of(html: str) -> list:
    import html as H
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    return [H.unescape(x) for x in (re.sub(r"[ \t　]+", " ", v).strip()
                                    for v in re.sub(r"<[^>]+>", "\n", t).split("\n")) if x]


def zip7(v: str) -> str:
    return re.sub(r"\D", "", v or "")


def info_of(ls: list) -> dict:
    """店舗ページの「店舗情報」表を ラベル→値（複数行は「／」でつなぐ）にする。"""
    try:
        a = ls.index("店舗名")
        b = ls.index("無料体験予約の流れ", a)
    except ValueError:
        return {}
    rec, cur = {}, None
    for v in ls[a:b]:
        if v in LABELS:
            cur = v
            rec[cur] = []
        elif cur:
            rec[cur].append(v.strip())
    return {k: "／".join(x for x in v if x) for k, v in rec.items()}


def fee_of(ls: list):
    plans, tax = [], []
    for i, v in enumerate(ls):
        if v != "月額" or i + 3 >= len(ls) or not re.fullmatch(r"[\d,]+", ls[i + 1]) or ls[i + 2] != "円":
            continue
        j, extra = i - 1, ""
        if ls[j].startswith("*"):            # 「*20%オフ」
            extra, j = f"（{ls[j].lstrip('*')}）", j - 1
        name = ls[j]
        if name.startswith("("):             # 「(オープンブース)」「(プレミアムルーム)」
            name = ls[j - 1] + name
        plans.append(f"{name} {ls[i + 1]}円{extra}")
        tax.append("税込" in ls[i + 3])
    if not plans:
        return None
    out = "／".join(plans) + ("（月額・税込）" if all(tax) else "（月額）")
    rest = [k for k in ("曜日・時間指定プラン", "回数券プラン") if k in ls]
    if rest:
        out += "・ほかに" + "、".join(rest) + "あり"
    return out


def bays_num_of(v: str):
    v = (v or "").translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    n = [int(x) for x in re.findall(r"(\d+)\s*(?:ブース|打席)", v)]
    return sum(n) if n else None


def faq_answer(faq: list, q: str) -> str:
    return faq[faq.index(q) + 1] if q in faq else ""


def main() -> None:
    html = get(URL)
    ls = lines_of(html)
    links = sorted({BASE + "/" + h.lstrip("/") for h in
                    re.findall(r'href="/?(store/[a-z_]+/[a-z_]+)"', html)})
    print(f"店舗ページ: {len(links)}件")
    pages = {}
    for u in links:
        pl = lines_of(get(u))
        inf = info_of(pl)
        zm = re.search(r"\d{3}\D?\d{4}", inf.get("住所", ""))
        z = zip7(zm.group(0)) if zm else None
        if z:
            pages[z] = (u, pl, inf)
        time.sleep(1.5)

    faq = lines_of(get(FAQ))
    closed_a = faq_answer(faq, "定休日はありますか？")
    equip_a = faq_answer(faq, "シミュレーターマシンの特徴は？")
    closed_v = "定休日なし（原則として365日・24時間・年中無休）" if "定休日はなく" in closed_a else None
    equip_v = "GOLFZON" if "GOLFZONのマシンを設置" in equip_a else None
    exc = next((v for v in faq if v.startswith("※") and "店のみ" in v and "シミュレーター" in v), "")
    exc_store = re.match(r"※(\S+?店)のみ", exc).group(1) if exc else None
    print("FAQ:", closed_a, "/", equip_a, "/ 例外:", exc_store)

    today, out = date.today().isoformat(), []
    for i, v in enumerate(ls):
        if not re.fullmatch(r"〒\d{3}-?\d{4}", v) or i == 0:
            continue
        name = ls[i - 1]
        # ⚠️ 一覧の下に運営会社の住所が同じ形で載っている。店舗ではないので除く。
        if not name.endswith("店"):
            continue
        addr = (ls[i + 1] if i + 1 < len(ls) else "").replace("&nbsp;", "").strip()
        if not re.search(f"^({PREF})", addr):
            continue
        m = re.search(f"({PREF})", addr)
        rec = {
            "brand": "GOLFERS24", "brand_slug": "golfers24",
            "name": name, "zip": v.lstrip("〒"), "address": addr,
            "pref": m.group(1), "source_url": URL, "fetched_at": today,
        }
        pg = pages.get(zip7(v))
        if pg:
            u, pl, inf = pg
            notes = []
            rec.update({
                "access": inf.get("アクセス") or None,
                "tel": inf.get("TEL") or None,
                "hours": inf.get("営業時間") or None,
                "open_24h": "24時間" in (inf.get("営業時間") or ""),
                "bays": inf.get("ブース数") or None,
                "bays_num": bays_num_of(inf.get("ブース数")),
                "parking": inf.get("駐車場") or None,
                "monthly_fee": fee_of(pl),
                "other": inf.get("その他") or None,
                "official": u, "source_url": u,
            })
            if any("全店舗で完全個室ご用意。" in x for x in pl):
                rec["private_room"] = True
                notes.append("個室は店舗ページの特徴欄「全店舗で完全個室ご用意。」から（ブランド全体の記載）")
            if closed_v:
                rec["closed"] = closed_v
                notes.append(f"定休日は公式FAQ（{FAQ}）「定休日はありますか？」→「{closed_a}」（ブランド全体の記載）")
            if equip_v and exc_store != name:
                rec["equipment"] = equip_v
                notes.append(f"機種は公式FAQ（{FAQ}）「シミュレーターマシンの特徴は？」→「{equip_a}」"
                             f"（例外は{exc_store}のみと明記）")
            rec["note"] = "／".join(notes) or None
        else:
            print("  ⚠️ 店舗ページが見つからない:", name)
        out.append(rec)

    res = list({(x["name"], x["address"]): x for x in out}.values())
    (ROOT / "data" / "brand-golfers24.json").write_text(
        json.dumps({"brand": "GOLFERS24", "source_url": URL, "fetched_at": today,
                    "count": len(res), "stores": res}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    from collections import Counter
    print(f"GOLFERS24: {len(res)}店舗  {Counter(x['pref'] for x in res).most_common()}")
    for k in ("access", "tel", "hours", "closed", "bays", "bays_num", "private_room",
              "parking", "monthly_fee", "equipment"):
        print(f"  {k}: {sum(1 for x in res if x.get(k) not in (None, ''))}/{len(res)}")
    listed = {x.get("official") for x in res}
    for z, (u, _, inf) in pages.items():
        if u not in listed:
            print("  一覧に無い店舗ページ（載せない）:", u, inf.get("店舗名"))
    for x in res[:4]:
        print("   ", x["name"], "|", x["address"], "|", x.get("bays"), "|", x.get("monthly_fee"))


main()
