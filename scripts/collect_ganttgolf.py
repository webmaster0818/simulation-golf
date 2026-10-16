#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GANTT GOLF（ガントゴルフ）の店舗を公式サイトから取る。

公式 https://ganttgolf.com/ 。運営は株式会社ダイバーシティ（特商法表記）。
弾道測定器＋大型シミュレーションを使う屋内のゴルフスクール（セルフ練習場も併設）。
2026-10-16 時点で 江坂店（/esaka/）・千里中央店（/senrichuo/）の2店。

店舗の見つけ方: トップページから「/<店>/…access/」へのリンクがある <店> を店舗とみなす。
アクセスページ下部の ACCESS 枠（p-access__*）に 店名・営業時間・特徴タグ・住所・電話 がある。
⚠️ 江坂店は本文で弾道測定器を「GOLFZON WAVE」と書き、ACCESS 枠のタグは「Sky Trak」。
   公式内で食い違うので機種は載せない（None）。食い違いは警告に出す。
⚠️ 月額は店舗トップの「プラン/料金」に税抜と税込が並んで書かれている。税込の値を使う。

  python3 scripts/collect_ganttgolf.py
"""
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://ganttgolf.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "GANTT GOLF", "ganttgolf"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")

# 公式の表記ゆれ → 機種名。ここに無い名前は機種として扱わない（警告に出す）。
KNOWN_MODELS = {
    "gcquad": "GCQuad", "fullswingkit": "Full Swing KIT", "golfzonwave": "GOLFZON WAVE",
    "skytrak": "SkyTrak", "trackman": "TrackMan",
}
NOT_MODEL = {"artrayswing", "puttview"}   # カメラ・パター用。弾道測定器ではない


def model_key(s: str) -> str:
    s = re.split(r"[（(]", s)[0]
    return re.sub(r"[^a-z]", "", s.lower())


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


def main() -> None:
    today = date.today().isoformat()
    top = get(f"{BASE}/")
    access_links = sorted(set(re.findall(rf'href="{re.escape(BASE)}/([a-z0-9-]+)/([a-z0-9-]*access[a-z0-9-]*)/"', top)))
    print(f"店舗候補 {len(access_links)}件 {access_links}")
    stores, warns = [], []
    for slug, acc in access_links:
        store_url = f"{BASE}/{slug}/"
        acc_url = f"{BASE}/{slug}/{acc}/"
        h = re.sub(r"(?s)<!--.*?-->", "", get(store_url)); time.sleep(1.5)
        a = re.sub(r"(?s)<!--.*?-->", "", get(acc_url)); time.sleep(1.5)

        shop = re.search(r'p-access__shop-name[^"]*">(.*?)</div>', a, re.S)
        shop_txt = text(shop.group(1)) if shop else ""
        tags = [text(t) for t in re.findall(r'p-access__character[^"]*">(.*?)</p>', a, re.S)]
        addr_m = re.search(r'p-access__address">(.*?)</p>', a, re.S)
        zipc = addr = None
        if addr_m:
            z = re.search(r"〒\s*(\d{3})-?(\d{4})", addr_m.group(1))
            zipc = z.group(1) + z.group(2) if z else None
            addr = text(re.sub(r'<span class="p-access__number">.*?</span>', "", addr_m.group(1)))
        if not addr:
            warns.append(f"{slug}: 住所が取れない → 除外")
            continue
        tel = re.search(r'href="tel:([0-9-]+)"', a)

        h1 = re.search(r"<h1>(.*?)</h1>", h, re.S)
        name = text(h1.group(1)).split("｜")[-1] if h1 else f"GANTT GOLF {shop_txt.split('(')[0]}"

        # 「(年中無休 営業時間: 6:00-25:00）」「(営業時間:10:00-22:00  定休日:不定休）」
        hm = re.search(r"営業時間\s*[:：]\s*([0-9:：\-～〜]+)", shop_txt)
        hours = hm.group(1) if hm else None
        cm = re.search(r"定休日\s*[:：]\s*([^）)\s]+)", shop_txt)
        closed = cm.group(1) if cm else ("なし（年中無休）" if "年中無休" in shop_txt else None)

        bay_tag = next((t for t in tags if "打席" in t), None)
        bays_num = None
        if bay_tag:
            b = re.search(r"(\d+)\s*ブース", bay_tag)
            bays_num = int(b.group(1)) if b else None
        private_room = True if any("個室" in t for t in tags) else None

        # 駐車場: アクセスページの見出し・本文から「駐車場」を含む文だけ
        parking = None
        exp = [(text(t), text(d)) for t, d in re.findall(
            r'p-senri-experience__title">(.*?)</p>\s*<p class="p-senri-experience__detail">(.*?)</p>', a, re.S)]
        for t, d in exp:
            if "駐車場" in t:
                d2 = re.sub(r"お車でお越しの方\s*", "", d)
                d2 = d2.split("徒歩でお越しの方")[0].strip()
                parking = f"{t} {d2}".strip()
        access = None
        for t, d in exp:
            m = re.search(r"徒歩でお越しの方\s*(.*?)(?:。|$)", d)
            if m:
                # 見出しが「徒歩でお越しの方」なので、それを付けて残す（分数だけだと手段が分からない）
                access = "徒歩: " + m.group(1).strip()
            elif "駅" in d and "徒歩" in d and "駐車場" not in t:
                access = d.strip().rstrip("。").replace("のアクセスしやすいロケーションです", "")

        # 弾道測定器: 本文の「弾道測定器「X」」と ACCESS 枠タグを突き合わせる
        body_models = []
        for m in re.findall(r"弾道測定器「([^」]+)」", text(h)):
            k = model_key(m)
            if k in KNOWN_MODELS:
                if KNOWN_MODELS[k] not in body_models:
                    body_models.append(KNOWN_MODELS[k])
            elif k not in NOT_MODEL:
                warns.append(f"{slug}: 見覚えのない機種名『{m}』")
        tag_models = [KNOWN_MODELS[model_key(t)] for t in tags if model_key(t) in KNOWN_MODELS]
        equipment = None
        if body_models and tag_models and not set(body_models) & set(tag_models):
            warns.append(f"{slug}: 公式内で機種が食い違う 本文={body_models} ACCESS枠={tag_models} → 載せない")
        elif body_models:
            equipment = "／".join(body_models)
        elif tag_models:
            equipment = "／".join(tag_models)

        # 月額（税込）: 「月額会員」「通い放題プラン」の行
        plan_txt = text(h)
        fees = []
        for m in re.finditer(r"(\d+)\s*回/月\s*[\d,]+\s*円\s*([\d,]+)円\(税込\)", plan_txt):
            fees.append(f"月{m.group(1)}回 {m.group(2)}円")
        m = re.search(r"通い放題\s*[\d,]+\s*円\s*([\d,]+)円\(税込\)", plan_txt)
        if m:
            fees.append(f"通い放題 {m.group(1)}円")
        for m in re.finditer(r"月\s*(\d+)\s*回\s*[\d,]+\s*円\s*([\d,]+)円\(税込\)", plan_txt):
            fees.append(f"月{m.group(1)}回 {m.group(2)}円")
        for m in re.finditer(r"(ライトプラン|デイプラン)\s*[\d,]+\s*円\s*([\d,]+)円\(税込\)", plan_txt):
            fees.append(f"セルフ練習場 {m.group(1)} {m.group(2)}円")
        # 「プラン/料金」直後の見出し（セミパーソナル／マンツーマンレッスン）
        km = re.search(r"plan プラン/料金\s*(\S+)", plan_txt)
        lesson_kind = km.group(1) if km else "レッスン"
        seen, fees_u = set(), []
        for f in fees:
            if f not in seen:
                seen.add(f); fees_u.append(f)
        lesson = [f for f in fees_u if not f.startswith("セルフ")]
        self_ = [f for f in fees_u if f.startswith("セルフ")]
        parts = []
        if lesson:
            parts.append(f"{lesson_kind} " + "／".join(lesson))
        parts += self_
        monthly_fee = ("／".join(parts) + "（税込）") if parts else None

        # 駐車場がアクセスページに無い店（江坂）は、店舗の FAQ（/<店>/faq-<店>/）の答えを読む。
        #   江坂 FAQ「駐車場／駐輪場はありますか？ お近くのコインパーキングをご利用ください。」
        parking_url = None
        if not parking:
            fm = re.search(rf'href="({re.escape(BASE)}/{slug}/faq-[a-z0-9-]*/)"', h)
            if fm:
                time.sleep(1.5)
                fq = text(re.sub(r"(?s)<!--.*?-->|<script.*?</script>|<style.*?</style>", "", get(fm.group(1))))
                pm = re.search(r"駐車場[／/]?駐輪場はありますか？\s*(.+?。)", fq)
                if pm:
                    parking, parking_url = pm.group(1).strip(), fm.group(1)

        pref = re.match(rf"({PREFS})", addr)
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": slug,
            "name": name,
            "pref": pref.group(1) if pref else None,
            "zip": zipc,
            "address": addr,
            "access": access,
            "tel": tel.group(1) if tel else None,
            "hours": hours,
            "open_24h": False,
            "closed": closed,
            "bays": bay_tag, "bays_num": bays_num,
            "private_room": private_room,
            "parking": parking,
            **({"parking_source_url": parking_url} if parking_url else {}),
            "monthly_fee": monthly_fee,
            "equipment": equipment,
            "open": True,
            "official": store_url,
            "source_url": acc_url, "fetched_at": today,
        })
        print(f"  {name} … {stores[-1]['pref']}")

    out = DATA / "ganttgolf.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件 → {out}")
    for w in warns:
        print("  ⚠️", w)


if __name__ == "__main__":
    main()
