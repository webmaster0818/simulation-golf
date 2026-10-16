#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLFTEC（ゴルフテック・GDO運営）の店舗を公式サイトから取る。

公式 https://golftec.golfdigest.co.jp/ 。屋内の完全個室マンツーマンレッスン。
公式の「テクノロジー」ページ（/concept/technology.html）に「ゴルフテックでは、3Dモーション解析、ハイスピード映像、
弾道測定データを組み合わせてスイングを分析します。」とあり、設備として OPTIMOTION（独自の3D動画解析）・弾道測定機・
「正面と飛球線後方に設置された2台のハイスピードカメラ」を挙げている＝ブランド全体の記述。
→ 全店の equipment にこの設備名を入れ、出典を equipment_source_url に残す。弾道測定機の機種名は書かれていないので
  「機種名は公式サイトに記載なし」を添える（トラックマン等の名前は付けない）。テクノロジーページから
  「弾道測定機」「OPTIMOTION」が消えたら None に戻す（取り直しのたびに確かめる）。
店舗一覧 /studio/ に /studio/<地域>/<店>/ が並ぶ（2026-10-16 時点 11店）。

店舗ページ:
  アクセス枠  p.studioAccess__detail__adress（〒＋住所＋<br>ビル名）／ 店舗TEL ／ studioAccess__detail__way（最寄り駅）
  詳細情報    dl.p-studioInfo__desc（営業時間・定休日・駐車場・施設設備・打席数・レンタル用品）
  紹介文      「すべて完全個室マンツーマン」→ private_room=True（店舗ページごとに書かれている）
⚠️ HTML コメント <!-- … --> の中に古い文面が残っている（キャンペーン・コーチ等）。先に消してから読む。
⚠️ 月額は無い。チケット回数制（10回 税込110,000円 等）で、公式に「入会金をはじめ、会費…は一切かかりません」。
   monthly_fee は None（月額制ではないので）。/price/ の「プラクティス」も 都度3,300円・3か月30,030円（税込）で月額ではない。
   トップからリンクされた /info/price2312.html に「月額制プラクティスパス：月額22,000円（税込）」があるが、
   2024年1月改定の告知で、現在の /price/ の料金（10回 110,000円 等）と合わない古い表＝使わない。
⚠️ TEL は予約センター 0570-041-109 と店舗TEL がある。tel には店舗TEL を入れる。

  python3 scripts/collect_golftec.py
"""
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://golftec.golfdigest.co.jp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "GOLFTEC", "golftec"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def text(s: str, br: str = " ") -> str:
    s = re.sub(r"<br\s*/?>", br, s)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return "\n".join(re.sub(r"[ \t　]+", " ", x).strip() for x in s.split("\n")).strip()


def info(h: str) -> dict:
    out = {}
    for lab, val in re.findall(r'<dt class="p-studioInfo__desc__label">(.*?)</dt>\s*'
                               r'<dd class="p-studioInfo__desc__content">(.*?)</dd>', h, re.S):
        k = re.sub(r"\s+", "", text(lab))
        out[k] = re.sub(r"\s+", " ", text(val)).replace("（ ", "（").replace(" ）", "）").strip()
    return out


TECH_URL = f"{BASE}/concept/technology.html"


def brand_equipment():
    h = re.sub(r"(?s)<!--.*?-->", "", get(TECH_URL))
    t = re.sub(r"\s+", " ", text(h))
    if "ゴルフテックでは、3Dモーション解析、ハイスピード映像、弾道測定データを組み合わせて" in t \
            and "OPTIMOTION" in t and "弾道測定機" in t and "2台のハイスピードカメラ" in t:
        return "OPTIMOTION（3D動画解析）／弾道測定機（機種名は公式サイトに記載なし）／ハイスピードカメラ2台"
    print("  ⚠️ テクノロジーページの記述が変わった → equipment は None")
    return None


def main() -> None:
    equipment = brand_equipment()
    time.sleep(1.5)
    listing = get(f"{BASE}/studio/")
    paths = sorted(set(re.findall(r'href="(/studio/[a-z_]+/[a-z_]+/)"', listing)))
    print(f"店舗候補 {len(paths)}件")
    today = date.today().isoformat()
    stores, skipped = [], []
    for i, p in enumerate(paths, 1):
        url = BASE + p
        h = re.sub(r"(?s)<!--.*?-->", "", get(url))
        am = re.search(r'<p class="studioAccess__detail__adress">(.*?)</p>', h, re.S)
        if not am:
            skipped.append(p)
            continue
        lines = [x for x in text(am.group(1), "\n").split("\n") if x]
        zipc, addr = None, " ".join(lines)
        z = re.match(r"〒\s*(\d{3})-?(\d{4})\s*(.*)", addr)
        if z:
            zipc, addr = z.group(1) + z.group(2), z.group(3).strip()
        tel = re.search(r'店舗TEL：</span>\s*<a href="tel:[^"]*"[^>]*>([^<]+)</a>', h)
        way = re.search(r'<p class="studioAccess__detail__way">(.*?)</p>', h, re.S)
        access = None
        if way:
            wl = [x for x in text(way.group(1), "\n").split("\n") if x and x != "最寄り駅"
                  and not re.fullmatch(r"アクセスマップは\s*こちら", x)]   # 横浜のリンク文言
            access = "／".join(wl) or None
        head = re.search(r'<h2 class="studioAccess__head">(.*?)\s*アクセス</h2>', h, re.S)
        shop = text(head.group(1)) if head else p.rstrip("/").rsplit("/", 1)[-1]
        r = info(h)
        bn = re.search(r"\d+", r.get("打席数", ""))
        bays_num = int(bn.group(0)) if bn else None
        intro = text(re.search(r'studioIntroduce__detail">(.*?)</div>', h, re.S).group(1)) \
            if re.search(r'studioIntroduce__detail">', h) else ""
        pref = re.match(rf"({PREFS})", addr)
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": p.rstrip("/").rsplit("/", 1)[-1].replace("_", "-"),
            "name": f"ゴルフテック {shop}",
            "pref": pref.group(1) if pref else None,
            "zip": zipc,
            "address": addr,
            "access": access,
            "tel": tel.group(1).strip() if tel else None,
            "hours": r.get("営業時間"),
            "open_24h": False,
            "closed": r.get("定休日"),
            "bays": f"{bays_num}打席" if bays_num else None, "bays_num": bays_num,
            "private_room": True if "完全個室" in intro else None,
            "parking": r.get("駐車場"),
            "monthly_fee": None,
            "equipment": equipment,
            "equipment_source_url": TECH_URL if equipment else None,
            "note": "計測の設備はブランド共通の記載（ゴルフテックテクノロジーのページ）" if equipment else None,
            "open": not re.search(r"OPEN予定|オープン予定", intro),
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        print(f"  {i:3}/{len(paths)} {stores[-1]['name']} … {stores[-1]['pref'] or '県不明'}")
        time.sleep(1.5)

    out = DATA / "golftec.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件 → {out}")
    nopref = [s["name"] for s in stores if not s["pref"]]
    if nopref:
        print("  ⚠️ 都道府県が取れなかった店:", nopref)
    if skipped:
        print(f"  住所が無く除外: {skipped}")


if __name__ == "__main__":
    main()
