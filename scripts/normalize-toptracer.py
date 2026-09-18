#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""収集した施設データを整える（郵便番号の分離・都道府県/市区町村の抽出・HTML残骸の除去）。

⚠️ 値の書き換えはしない。分解と除去だけ。
   「￥220-」のような表記ゆれもそのまま残す（正規化すると一次情報から離れる）。
   判定に使う数値だけ別フィールドに持つ。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREF = ("北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 "
        "神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 "
        "大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 "
        "福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県").split()


# 住所に都道府県が無い施設の補完（GDO掲載の市名→都道府県。いずれも一意）
CITY_PREF = {"岡山市": "岡山県", "鎌倉市": "神奈川県", "大阪市": "大阪府"}


def clean(v):
    """取得時に混ざった HTML コメントの断片を落とす。"""
    if not isinstance(v, str):
        return v
    return re.sub(r"\s*(-->|<!--)\s*", "", v).strip()


def main() -> None:
    d = json.loads((ROOT / "data" / "toptracer.json").read_text(encoding="utf-8"))
    out = []
    for x in d["facilities"]:
        x = {k: clean(v) for k, v in x.items()}
        addr = x.get("address") or ""
        m = re.match(r"〒?\s*(\d{3}[-‐ｰ−]?\d{4})\s*(.*)", addr)
        if m:
            x["zip"], addr = m.group(1), m.group(2).strip()
            x["address"] = addr
        pref = next((p for p in PREF if addr.startswith(p)), None)
        if not pref:
            # 都道府県が省略された表記。市名が一意に定まるものだけ補う。
            for city, p_ in CITY_PREF.items():
                if city in addr:
                    pref, addr = p_, p_ + addr[addr.index(city):]
                    x["address"] = addr
                    break
        x["pref"] = pref
        if pref:
            c = re.match(r"(.+?[市区町村])", addr[len(pref):])
            x["city"] = c.group(1) if c else None
        # ⚠️ 出典側が「円」とだけ書いていて金額が入っていない施設がある
        #    （Pacific GOLF CLUB。該当行がHTMLコメント内で、金額が抜けている）。
        #    金額として使えないので、無い扱いにする。勝手に推測しない。
        fee = x.get("ttr_fee")
        if fee and fee != "無料" and not re.search(r"\d", fee):
            fee = None
        x["ttr_fee"] = fee
        # 料金は「無料かどうか」だけを判定に使う。金額の表記はそのまま残す。
        x["ttr_free"] = fee == "無料"
        # 打席数は「45（120）」＝トップトレーサー45打席/全120打席。前者だけ数値化。
        b = re.match(r"(\d+)", x.get("ttr_bays") or "")
        x["ttr_bays_num"] = int(b.group(1)) if b else None
        n = re.match(r"(\d+)", x.get("distance") or "")
        x["distance_yard"] = int(n.group(1)) if n else None
        out.append(x)

    nopref = [x["name"] for x in out if not x["pref"]]
    d["facilities"] = out
    (ROOT / "data" / "toptracer.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"整形 {len(out)}件 / 都道府県不明 {len(nopref)}件 {nopref}")
    from collections import Counter
    c = Counter(x["pref"] for x in out if x["pref"])
    print(f"都道府県 {len(c)}種 上位: {c.most_common(10)}")
    print(f"無料で使える施設: {sum(1 for x in out if x['ttr_free'])}/{len(out)}")


main()
