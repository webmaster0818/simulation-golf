#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lounge Range（会員制・完全個室・24時間のインドアゴルフ）の店舗を公式サイトから取る。

店舗一覧 https://lounge-range.com/courses/ に `<div class="storeBox" id="...">` が並び、
店名・Since・住所・店舗詳細リンクが入っている。店舗詳細の <th>/<td> に
住所・営業時間・駐車場・定休日・電話番号・打席、本文に機種名（『…』）がある。

⚠️ 一覧のアンカーid と店舗詳細のURLは別物（#matsue2 → /matsue-training1/）。
   idからURLを組み立てると404になる。必ず一覧のリンクを使う。
⚠️ 一覧にはコメントアウトされた店舗詳細リンクが残っている（河口湖）。
   コメントを先に落としてからリンクを探す。
⚠️ **誰でも入会して使える店だけを載せる。** 一覧には次のものが混ざっている。
     ・宿泊者専用の店（河口湖＝「宿泊の際のみのご利用」）
     ・ゴルフではない業態（Conditioning ＝ 打席が無い）
     ・パター練習専用の店（武蔵小山＝「会員制インドアパターゴルフ場」）
     ・他施設との共同企画（鳥居崎＝食事・宿泊と合わせて使う会員特典）
   これらは除外し、除外した理由を表示する。
⚠️ 公式に書いていない項目は None のままにする。推測で埋めない。
⚠️ 料金は店舗ページではなく `<店舗>/price/` にある。最初は「店舗ページに無い＝非公開」と
   扱いかけたが、それだとサイトに「このブランドは料金を公開していません」と事実と違う文が出る。
   取れなかった店は警告に出るので、目で見て確認する。

  python3 scripts/collect_loungerange.py            # 取得して data/loungerange.json に書く
  python3 scripts/collect_loungerange.py --limit 3  # 動作確認
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
BASE = "https://lounge-range.com"
LIST_URL = f"{BASE}/courses/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BRAND, BRAND_SLUG = "Lounge Range", "lounge-range"

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


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def strip_hidden(h: str) -> str:
    return re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>",
                  "", h, flags=re.S)


def rows(page_html: str) -> dict:
    out = {}
    for m in re.finditer(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", page_html, re.S):
        k, v = text(m.group(1)), text(m.group(2))
        if k and v and k not in out:
            out[k] = v
    return out


# 専用ページを lounge-range.com に持たず、店舗自身のサイトに飛ぶ店。
# 一覧からは店名と住所しか取れないので、その店のサイトを読んで確認した値を入れる。
# ⚠️ 値を足すときは source_url（その店自身のページ）と確認日を必ず書く。
OVERRIDES = {
    "tsubamesanjo": {   # 2026-10-02 確認。Lounge Range が運営を引き継いだ既存施設
        "zip": "9591232",
        "address": "新潟県燕市井土巻4丁目282",
        "hours": "5:00〜22:00（全日）",
        "open_24h": False,
        "bays": "12打席（完全個室4打席／オープン8打席）", "bays_num": 12,
        "private_room": True,
        "parking": "無料駐車場 約60台",
        "monthly_fee": ("スタンダードプラン（オープン打席のみ）レギュラー 16,500円・ウィークデイ 11,000円・"
                        "ライト（月3回）7,700円／VIPプラン（全打席）レギュラー 22,000円・ウィークデイ 16,500円・"
                        "ライト（月3回）11,000円（税込・入会金11,000円が別途）"),
        "fee_source_url": "https://ts-golfpark.com/price/",
        "equipment": "GOLFZON GDR／DITECT Prizm Pro",
        "official": "https://ts-golfpark.com/",
        "source_url": "https://ts-golfpark.com/",
    },
    "shinagawa": {      # 2026-10-02 確認。品川島津山は専用サイトを持つ
        "zip": "1410022",
        "address": "東京都品川区東五反田1-2-43-1F",
        "access": "都営地下鉄「高輪台」駅 徒歩約3分、「五反田駅」徒歩約5分",
        "hours": "24時間",
        "open_24h": True,
        "closed": "毎週月曜日 早朝3:00〜昼12:00は休止・メンテナンス",
        "private_room": True,
        "monthly_fee": "11,000円〜41,800円（税込・全7プラン・レギュラー 41,800円）",
        "fee_source_url": "https://www.lr-shinagawashimazuyama.com/",
        "official": "https://www.lr-shinagawashimazuyama.com/",
        "source_url": "https://www.lr-shinagawashimazuyama.com/",
    },
}

# --reapply で落とす店（通常の取得では一覧の文言で判定して除外される）
REAPPLY_DROP = {"toriizaki"}

# 弾道計測・シミュレーターではないもの（スイング撮影カメラ・パター練習機・提携先・人物紹介）
NOT_EQUIP = re.compile(r"アートレイ|PuttView|TourPutt|那須|ホテル|小学生")
GOLFZON_MODELS = ("GDR PLUS MULTI", "TWOVISION NX", "TWOVISION", "T2 VISION PLUS",
                  "VISION PLUS", "GDR PLUS")


def equipment(body: str) -> tuple[str | None, list[str]]:
    """本文の『…』から機種名を拾う。返り値は（表記, 見覚えのない名前）。

    ⚠️ 『…』には機種以外も入っている（『アートレイカメラ』『スーパー小学生』等）ので、
       そのまま連結すると機材欄に人物紹介の語が混ざる。既知の機種だけを通し、
       見覚えのない名前は捨てずに警告として出す（目で見て判断する）。
    """
    names = [re.sub(r"\s+", " ", n).strip() for n in re.findall(r"『\s*([^』]+?)\s*』", body)]
    names = list(dict.fromkeys(n for n in names if not NOT_EQUIP.search(n)))
    up = [n.upper() for n in names]
    out, unknown = [], []
    gz = [m for m in GOLFZON_MODELS if m in up]
    if "GDR PLUS MULTI" in gz:      # VISION PLUS と GDR PLUS は MULTI の切り替えモード
        gz = [m for m in gz if m not in ("VISION PLUS", "GDR PLUS")]
    out += [f"GOLFZON {m}" for m in gz]
    if "GOLFZON" in up and not gz:
        out.append("GOLFZON")
    if any("GARMIN" in n for n in up) and "APPROACH R50" in up:
        out.append("GARMIN Approach R50")
    known = {"SDR GOLF SIMULATOR": "SDR Golf Simulator", "OK ON GOLF": "OK ON GOLF",
             "FULL SWING": "FULL SWING", "GC QUAD": "GC Quad", "EYE XO2": "EYE XO2",
             "QEDゴルフシミュレーター": "QEDゴルフシミュレーター", "TRACKMAN": "TRACKMAN"}
    for n, u in zip(names, up):
        if u in known:
            out.append(known[u])
        elif u in GOLFZON_MODELS or u == "GOLFZON" or "GARMIN" in u or u == "APPROACH R50":
            continue
        else:
            unknown.append(n)
    return ("／".join(dict.fromkeys(out)) or None), unknown


def monthly_fee(price_html: str) -> str | None:
    """料金ページ（<店舗>/price/）の「プラン名｜利用時間｜月会費」の表から月会費を拾う。

    ⚠️ レッスン・オプション・チケットの表は見出しが「レッスン名」「オプション」なので拾わない。
       月会費ではない金額（1回6,600円のチケット等）を月会費として出さないため。
    ⚠️ プラン構成は店ごとに違う（3〜11プラン）。全部並べると読めないので、
       税込の最小〜最大とプラン数を出し、「レギュラー」があればその額を添える。
       金額はすべて公式の表にある税込額で、こちらで計算した値は無い。
    """
    plans = []
    for t in re.findall(r"<table.*?</table>", price_html, re.S):
        trs = re.findall(r"<tr.*?</tr>", t, re.S)
        if not trs:
            continue
        head = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", trs[0], re.S)]
        # 見出しは店により「プラン名」「プラン概要」。年会費だけの表（月会費の列が無い）は拾わない
        if not head or head[0] not in ("プラン名", "プラン概要") or "月会費" not in head:
            continue
        col = head.index("月会費")
        for tr in trs[1:]:
            cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            if len(cells) <= col:
                continue
            # 「38,000円 税込41,800円」と「12,100円 (税込)」の2通りの書き方がある
            m = (re.search(r"税込\s*([\d,]+)\s*円", cells[col])
                 or re.search(r"([\d,]+)\s*円\s*[（(]\s*税込\s*[）)]", cells[col]))
            if m:
                plans.append((cells[0], int(m.group(1).replace(",", ""))))
    if not plans:
        return None
    lo, hi = min(v for _, v in plans), max(v for _, v in plans)
    rng = f"{lo:,}円" if lo == hi else f"{lo:,}円〜{hi:,}円"
    reg = next((v for n, v in plans if n == "レギュラー"), None)
    tail = f"・レギュラー {reg:,}円" if reg and len(plans) > 1 else ""
    return f"{rng}（税込・全{len(plans)}プラン{tail}）"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reapply", action="store_true",
                    help="取得し直さず、保存済みの結果に OVERRIDES と除外だけ当て直す")
    a = ap.parse_args()

    if a.reapply:
        out = DATA / "loungerange.json"
        d = json.loads(out.read_text(encoding="utf-8"))
        d["stores"] = [s for s in d["stores"] if s["slug"] not in REAPPLY_DROP]
        for s in d["stores"]:
            s.update(OVERRIDES.get(s["slug"], {}))
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"当て直し {len(d['stores'])}件 → {out}")
        return

    listing = strip_hidden(get(LIST_URL))
    blocks = re.split(r'<div class="storeBox" id="', listing)[1:]
    print(f"一覧の店舗ブロック {len(blocks)}件")

    today = date.today().isoformat()
    stores, excluded, problems = [], [], []
    for i, b in enumerate(blocks, 1):
        if a.limit and len(stores) >= a.limit:
            break
        anchor = b[: b.index('"')]
        mname = re.search(r'<p class="bold[^"]*">(.*?)<span', b, re.S)
        name = text(mname.group(1)) if mname else anchor
        # 共同企画店は <span> の位置が違い「燕三条 ×」で切れる。段落全体から取り直す
        if name.endswith("×") or name.startswith("Lounge Range"):
            mfull = re.search(r'<p class="bold[^"]*">(.*?)</p>', b, re.S)
            name = re.sub(r"^Lounge Range\s*", "", text(mfull.group(1)) if mfull else name)
            name = re.split(r"\s*(?:共同企画店舗|Since|\d{4}年)", name)[0].strip(" /")
        msince = re.search(r"Since\s*([\d.]+)", b)
        maddr = re.search(r"<address[^>]*>(.*?)</address>", b, re.S)
        # 一覧の住所は <span>県名</span> の後ろに空白が入る。県名の直後だけ詰める
        list_addr = re.sub(rf"^({PREFS})\s+", r"\1", text(maddr.group(1))) if maddr else None
        mnote = re.search(r'<div class="[^"]*villa[^"]*">(.*?)</div>', b, re.S)
        note = text(mnote.group(1)) if mnote else None
        mlink = re.search(r'<a[^>]*href="([^"]+)"[^>]*>\s*店舗詳細', b)
        link = mlink.group(1) if mlink else None

        if note and "宿泊" in note:
            excluded.append(f"{name}（宿泊者専用: {note}）")
            continue
        if "共同企画" in text(b):
            # 鳥居崎＝料理旅館のゴルフ施設を、会員が食事・宿泊と合わせて使える特典。入会できる店ではない
            excluded.append(f"{name}（他施設との共同企画・会員特典としての利用）")
            continue
        if "Conditioning" in name:
            excluded.append(f"{name}（ゴルフ打席ではない業態）")
            continue

        own_page = bool(link and link.startswith(BASE))
        r, equip, private, page, fee, fee_url = {}, None, None, "", None, None
        if own_page:
            page = strip_hidden(get(link))
            title = text((re.search(r"<title>(.*?)</title>", page, re.S) or ["", ""])[1])
            if "パター" in title:   # 武蔵小山＝「会員制インドアパターゴルフ場」。打席が無い
                excluded.append(f"{name}（パター練習専用: {title[:40]}）")
                time.sleep(2)
                continue
            fee_url = link.rstrip("/") + "/price/"
            fee = monthly_fee(strip_hidden(get(fee_url)))
            if not fee:
                problems.append(f"{name}: 料金表が取れなかった（{fee_url}）")
                fee_url = None
            time.sleep(2)
            r = rows(page)
            body = text(page)
            equip, unknown = equipment(body)
            if unknown:
                problems.append(f"{name}: 機種か判断できない名前 {unknown}（{link}）")
            private = True if "完全個室" in body else None
            time.sleep(2)   # 公式サイトに負荷をかけない

        addr = r.get("住所") or list_addr
        if not addr:
            problems.append(f"{name}: 住所なし")
            continue
        zipc = None
        mz = re.match(r"〒?\s*(\d{3})-?(\d{4})\s*", addr)
        if mz:
            zipc = mz.group(1) + mz.group(2)
            addr = addr[mz.end():].strip()
        mp = re.match(rf"({PREFS})", addr)
        if not mp and list_addr:
            # 店舗ページの住所に都道府県が無い店は、一覧に公式が書いている都道府県で補う
            ml = re.match(rf"({PREFS})", list_addr)
            if ml:
                addr, mp = ml.group(1) + addr, ml
        hours = r.get("営業時間")
        tel = r.get("電話番号")
        slug = link.rstrip("/").rsplit("/", 1)[-1] if own_page else anchor
        # Since が未来、または一覧に「予定」とあれば準備中
        is_open = True
        if msince:
            y, mo, d_ = (msince.group(1).split(".") + ["1", "1"])[:3]
            is_open = f"{int(y):04d}-{int(mo):02d}-{int(d_):02d}" <= today
        if re.search(r"予定|Coming", text(b)):
            is_open = False
        stores.append({
            "brand": BRAND, "brand_slug": BRAND_SLUG,
            "slug": slug,
            "name": f"Lounge Range {name}",
            "pref": mp.group(1) if mp else None,
            "zip": zipc,
            "address": addr,
            "access": None,
            "tel": tel,
            "hours": hours,
            "open_24h": True if (hours and "24時間" in hours) else None,
            "closed": r.get("定休日"),
            "bays": r.get("打席"), "bays_num": None,
            "private_room": private,
            "parking": r.get("駐車場"),
            "monthly_fee": fee, "fee_source_url": fee_url,
            "equipment": equip,
            "open": is_open,
            "since": msince.group(1) if msince else None,
            # 専用ページが無い店（外部サイトに飛ぶ店）は一覧ページが出典
            "official": link or LIST_URL,
            "source_url": link if own_page else LIST_URL,
            "fetched_at": today,
        })
        s = stores[-1]
        s.update(OVERRIDES.get(anchor, {}))
        if own_page and not r:
            problems.append(f"{name}: 店舗ページから表が取れなかった（{link}）")
        print(f"  {i:3}/{len(blocks)} {s['name'][:30]} … {s['pref'] or '県不明'}"
              f" / {s['hours'] or '時間なし'} / {s['equipment'] or '機種なし'}"
              f"{'' if s['open'] else ' / 準備中'}")

    out = DATA / "loungerange.json"
    out.write_text(json.dumps({"brand": BRAND, "fetched_at": today, "stores": stores},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n書き出し {len(stores)}件 → {out}")
    for e in excluded:
        print("  除外:", e)
    nopref = [s["name"] for s in stores if not s["pref"]]
    if nopref:
        print("  ⚠️ 都道府県が取れなかった店:", nopref)
    for p in problems:
        print("  ⚠️", p)
    slugs = [s["slug"] for s in stores]
    dup = {x for x in slugs if slugs.count(x) > 1}
    if dup:
        print("  ⚠️ slug重複:", dup)


if __name__ == "__main__":
    main()
