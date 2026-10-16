#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HYPERION GOLF STUDIO（ヒューペリオン・完全個室のシミュレーションゴルフ／運営 株式会社Anything）を公式サイトから取る。

公式 https://hyperion-golf.com/ は静的HTML。
  トップ        /                              … 特徴（トラックマン・24時間365日・完全個室）・会員プラン・FAQ・店舗一覧
  店舗ページ    /studio/studio-<slug>.html     … 住所・最寄り駅・設備のアイコン列（弾道計測機/スイング解析機/右打席…）
店舗一覧はトップの「店舗情報」欄（StudioMap・表示されている部分）から作る（2026-10-16 時点 4店・すべて東京都）。
⚠️ トップから店舗ページ（/studio/studio-*.html）へのリンク「店舗詳細」は <!-- --> で隠されている。
   店舗ページ自体は公開されていて、住所はトップと一致する。最寄り駅と設備はそこにしか無いので読む。
   店名 → 店舗ページの対応は、コメント内のリンクと店舗ページの h3 で突き合わせる（住所が食い違えば警告）。

⚠️ トップのHTMLには、古い料金表（スポット会員11,000円・プラチナ77,550円 など）が <!-- --> の中に残っている。
   コメントを落とさずにテキスト化すると、表示されていない料金を拾う。必ずコメントを除いてから読む。
⚠️ 打席（部屋）数は公式に記載なし（「1フロア貸し切り制」とだけある）。bays は null。
⚠️ 電話番号はトップの「無料体験 電話申込」ボタン（画像・tel: リンク）だけで、店舗ごとの番号は無い。
   全店共通の申込窓口として注記つきで入れる。
⚠️ 営業時間・駐車場・料金はトップに全店共通として書かれている（店舗ページには無い）。
⚠️ 公式URLの西新宿は「nishishinjyuku」（訓令式混じり）。slug はヘボン式 nishishinjuku にそろえる。

  python3 scripts/collect_hyperion.py      # 取得して data/hyperion.json に書く
"""
import html
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://hyperion-golf.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "HYPERION GOLF STUDIO", "hyperion"

PREFS = ("北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|"
         "東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|"
         "滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|"
         "香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県")

# 公式URLのローマ字 → slug の置き換え（ヘボン式にそろえる）
SLUG_FIX = {"nishishinjyuku": "nishishinjuku"}


def get(url: str) -> str:
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                           capture_output=True, text=True, timeout=60)
        if r.stdout and len(r.stdout) > 2000:
            return r.stdout
        time.sleep(3)
    return ""


def strip_hidden(h: str) -> str:
    return re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", "", h, flags=re.S)


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def dl(h: str, key: str) -> str | None:
    m = re.search(rf"<dt>\s*<span>{key}</span>\s*</dt>\s*<dd>(.*?)</dd>", h, re.S)
    return text(m.group(1)) if m else None


def main() -> None:
    today = date.today().isoformat()
    problems = []
    top_raw = get(BASE + "/")
    if not top_raw:
        raise SystemExit("トップが取れなかった")
    top = strip_hidden(top_raw)
    top_t = text(top)

    # 全店共通: 営業時間（「24時間365日利用可能」）
    is24 = "24時間365日" in top_t
    hours = "24時間365日利用可能" if re.search(r"24時間365日\s*利用可能", top_t) else None
    closed = None  # 「定休日」「年中無休」の語は無い。365日利用可能は hours に残す

    # 全店共通: 料金（表示されているゴールドプラン＝月定額。※金額は全て税込です。）
    fee = None
    mg = re.search(r"ゴールドプラン おすすめ .*?入会金 ([\d,]+)円 →初回限定キャンペーン0円 打席利用料 "
                   r"キャンペーンで10％OFF ([\d,]+)円/月 →([\d,]+)円/月 利用店舗 (\S+) 1回の利用時間 (\d+)分 "
                   r"1日予約可能数 (\S+) 月間予約可能数 (\S+)", top_t)
    tax = "税込" if "金額は全て税込" in top_t else "税込・税抜の別は公式サイトに記載なし"
    if mg:
        fee = (f"ゴールドプラン 月額{mg.group(2)}円（{tax}・キャンペーンで{mg.group(3)}円）。"
               f"{mg.group(4)}・1回{mg.group(5)}分・{mg.group(6)}・{mg.group(7)}。"
               f"入会金{mg.group(1)}円（初回限定キャンペーン0円）")
    else:
        problems.append("料金（ゴールドプラン）が取れなかった")
    mv = re.search(r"ビジタープラン おすすめ 単発利用したい方向け 入会金 ([\d,]+)円 打席利用料 ([\d,]+)円/1回（1コマ）", top_t)
    if fee and mv:
        fee += f"／ビジタープラン 1回{mv.group(2)}円（{tax}・入会金{mv.group(1)}円）"

    # 全店共通: 駐車場（FAQ）
    parking = None
    mp_ = re.search(r"駐車場／駐輪場はありますか？\s*(.+?。.+?。)", top_t)
    if mp_:
        parking = mp_.group(1).strip()

    # 全店共通: 電話（「無料体験 電話申込」ボタンの tel: リンク）
    tel = None
    mt = re.search(r'href="tel:(\d{10,11})"[^>]*>\s*<img[^>]*alt="([^"]*電話[^"]*)"', top)
    if mt:
        d = mt.group(1)
        tel = f"{d[:3]}-{d[3:7]}-{d[7:]}（{mt.group(2).replace(' ', '・')}・全店共通）"

    equipment = "トラックマン" if re.search(r"トラックマン\s*導入店", top_t) else None
    private = True if "完全個室" in top_t else None

    # 表示されている店舗一覧（トップの StudioMap）
    listed = []
    for m in re.finditer(r'<div class="StudioMap-address">\s*<strong>.*?>([^<]+?店)</a></strong>\s*<p>(.*?)</p>', top, re.S):
        listed.append((text(m.group(1)), text(re.sub(r"<br\s*/?>", " ", m.group(2)))))
    if not listed:
        raise SystemExit("店舗一覧が見つからない")
    # 店舗ページ（リンクはコメント内にしか無い）
    paths = sorted(set(re.findall(r'href="\./(studio/studio-[a-z0-9-]+\.html)"', top_raw)),
                   key=lambda p: top_raw.find(p))
    pages = {}
    for p in paths:
        time.sleep(1.5)
        h = strip_hidden(get(f"{BASE}/{p}"))
        mh = re.search(r"<h3>\s*HYPERION GOLF STUDIO\s*<span[^>]*>(.*?)</span>", h, re.S)
        if mh:
            pages[text(mh.group(1))] = (p, h)
        else:
            problems.append(f"{p}: 店名が取れなかった")

    stores = []
    for shop, top_addr in listed:
        if shop not in pages:
            problems.append(f"{shop}: 店舗ページが見つからない")
            continue
        p, h = pages[shop]
        url = f"{BASE}/{p}"
        own = re.search(r"studio-([a-z0-9-]+)\.html", p).group(1)
        slug = SLUG_FIX.get(own, own)
        addr = dl(h, "住所") or ""
        zipc = None
        mz = re.match(r"〒?\s*(\d{3})-?(\d{4})\s*", addr)
        if mz:
            zipc = mz.group(1) + mz.group(2)
            addr = addr[mz.end():].strip()
        if re.sub(r"\s|〒", "", top_addr) != re.sub(r"\s|〒", "", (mz.group(0) if mz else "") + addr):
            problems.append(f"{slug}: トップと店舗ページで住所が違う（{top_addr} ／ {addr}）")
        mpref = re.match(rf"({PREFS})", addr)
        if not mpref:
            problems.append(f"{slug}: 住所に都道府県が無い（{addr}）")
        facil = [text(x) for x in re.findall(r"<li>(.*?)</li>",
                 (re.search(r'class="studio-facility">(.*?)</div>', h, re.S) or [None, ""])[1], re.S)]
        facil = [f.rstrip("※ ").strip() for f in facil]
        bays = "右打席のみ" if "右打席" in facil and "左打席" not in facil else None

        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": slug,
            "name": f"{BRAND} {shop}",
            "pref": mpref.group(1) if mpref else None,
            "zip": zipc,
            "address": addr,
            "access": dl(h, "最寄り駅"),
            "tel": tel,
            "hours": hours,
            "open_24h": is24 if hours else None,
            "closed": closed,
            "bays": bays, "bays_num": None,
            "private_room": private,
            "parking": parking,
            "monthly_fee": fee,
            "equipment": equipment,
            "facilities": "／".join(facil) if facil else None,
            "open": True,
            "official": url,
            "source_url": url, "fetched_at": today,
        })
        s = stores[-1]
        print(f"  {s['name']} … {s['zip']} {s['address']} / {s['access']} / {s['facilities']}", flush=True)

    out = DATA / "hyperion.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n共通: {hours} / {fee} / {parking} / {tel} / {equipment}")
    print(f"書き出し {len(stores)}件 → {out}")
    for p in problems:
        print("  ⚠️", p)


if __name__ == "__main__":
    main()
