#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ブランド別に集めたデータを1つの施設マスタにまとめる。

⚠️ ブランドによって取れている項目が違う。無い項目は null のまま出す。
   「たぶん24時間だろう」といった穴埋めはしない。ページ側で
   「公式サイトに記載なし」と出すほうが読者にとって正確。

業態（segment）で分ける:
  indoor  … 屋内のシミュレーションゴルフ施設（本サイトの主対象）
  range   … 屋外の打ちっぱなし練習場にトップトレーサーが入っているもの
  lesson  … コーチ付き・完全予約制・月会費制のインドアゴルフスクール（弾道測定機あり）
            ⚠️ 2026-09-23追加。indoor と混ぜない。「好きな時間に打ちに行きたい」人と
               「教わりたい」人では探しているものが違う。機材の軸では対象に入るが、
               一覧で並べると「24時間で空いている施設」を探している人の邪魔になる。
"""
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def slugify(brand_slug: str, brand: str, name: str, own: str | None, zipc: str | None,
            i: int) -> str:
    """店舗ページのURL。全ブランドで `{ブランド}-{地名}` の形にそろえる。

    ブランド名を必ず前に付ける理由は、地名だけだと別ブランドの同名店と衝突するため
    （浦和・東灘・中川などは複数ブランドにある）。

    地名の部分は、
      ① data/slug-romaji.json（日本語店名のため読みを1件ずつ確認して作った表）
      ② ブランド公式サイトのURLに使われているローマ字
      ③ どちらも無ければ郵便番号
    の順で決める。
    """
    def norm(v: str) -> str:
        v = unicodedata.normalize("NFKC", v).replace("_", "-")
        return re.sub(r"[^0-9A-Za-z]+", "-", v).strip("-").lower()

    place = None
    if own:
        place = norm(own)
        # 公式のslugにブランド名が入っている場合は落とす（indoorgolf_misato → misato）
        for pre in ("indoorgolf-", "golf-", norm(brand) + "-"):
            if place.startswith(pre) and len(place) > len(pre):
                place = place[len(pre):]
                break
        if place == norm(brand) or not place:
            place = None
    if not place:
        place = (zipc or "").replace("-", "") or str(i)
    return f"{brand_slug}-{place}"


def main() -> None:
    romaji_path = DATA / "slug-romaji.json"
    ROMAJI = json.loads(romaji_path.read_text(encoding="utf-8")) if romaji_path.exists() else {}
    out = []

    for f in sorted(DATA.glob("brand-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for i, s in enumerate(d["stores"], 1):
            out.append({
                "segment": "indoor",
                "brand": s["brand"], "brand_slug": s["brand_slug"],
                "slug": slugify(s["brand_slug"], s["brand"], s["name"], s.get("slug"), s.get("zip"), i),
                "name": s["name"], "pref": s.get("pref"), "zip": s.get("zip"),
                "address": s.get("address"), "access": s.get("access"),
                "tel": s.get("tel"), "hours": s.get("hours"),
                "open_24h": s.get("open_24h"), "closed": s.get("closed"),
                "bays": s.get("bays") or s.get("rooms"),
                "bays_num": s.get("bays_num") or s.get("rooms_num"),
                "private_room": s.get("private_room"),
                "parking": s.get("parking"), "monthly_fee": s.get("monthly_fee"),
                "equipment": None, "open": s.get("open", True),
                "official": None,
                "source_url": s["source_url"], "fetched_at": s["fetched_at"],
            })

    for f in out:
        if f["slug"] in ROMAJI:
            f["slug"] = ROMAJI[f["slug"]]

    tt = json.loads((DATA / "toptracer.json").read_text(encoding="utf-8"))
    for i, s in enumerate(tt["facilities"], 1):
        out.append({
            "segment": "range",
            "brand": None, "brand_slug": None,
            "slug": "toptracer-" + s["slug"].lower().replace("_", "-"),
            "name": s["name"], "pref": s.get("pref"), "zip": s.get("zip"),
            "address": s.get("address"), "access": None,
            "tel": s.get("tel"), "hours": None, "open_24h": None, "closed": None,
            "bays": s.get("ttr_bays"), "bays_num": s.get("ttr_bays_num"),
            "private_room": None, "parking": None,
            # トップトレーサーの利用料。月会費ではないので別項目にする。
            "monthly_fee": None, "usage_fee": s.get("ttr_fee"),
            "equipment": "トップトレーサー・レンジ",
            "distance_yard": s.get("distance_yard"),
            "open": True, "official": s.get("official"),
            "source_url": s["source_url"], "fetched_at": s["fetched_at"],
        })

    # --- ステップゴルフ（レッスンスクール）/ i8 GOLF（24時間インドア） ---
    # slugは公式サイトのURLに使われているローマ字をそのまま使う。
    # 日本語店名を音訳する方法は過去に失敗している（三宿→mishu 等）ので、
    # 公式が付けているローマ字があるならそれが一番確かな読み。
    for fname, seg in (("stepgolf.json", "lesson"), ("i8golf.json", "indoor"),
                       ("doortogolf.json", "indoor"), ("zengolf.json", "lesson")):
        fp = DATA / fname
        if not fp.exists():
            continue
        d = json.loads(fp.read_text(encoding="utf-8"))
        for i, s in enumerate(d["stores"], 1):
            own = s.get("slug")
            if not own:
                m = re.search(r"/(?:store/)?([A-Za-z0-9_-]+)/?$", s["source_url"])
                if m:
                    own = re.sub(r"(_top|_extra|-ex|_ex|-extra|_premium|-premium)$", "", m.group(1))
            out.append({
                "segment": seg,
                "brand": s["brand"], "brand_slug": s["brand_slug"],
                "slug": slugify(s["brand_slug"], s["brand"], s["name"], own, s.get("zip"), i),
                "name": s["name"], "pref": s.get("pref"), "zip": s.get("zip"),
                "address": s.get("address"), "access": s.get("access"),
                "tel": s.get("tel"), "hours": s.get("hours"),
                "open_24h": s.get("open_24h"), "closed": s.get("closed"),
                "bays": s.get("bays"), "bays_num": s.get("bays_num"),
                "private_room": s.get("private_room"),
                "parking": s.get("parking"), "monthly_fee": s.get("monthly_fee"),
                "equipment": s.get("equipment"), "open": s.get("open", True),
                "official": s.get("official"),
                "source_url": s["source_url"], "fetched_at": s["fetched_at"],
            })

    # --- チェーンに属さない単独施設 ---
    # ⚠️ 0件の県はチェーンが出店していないだけで、施設が無いわけではない（2026-10-01に判明）。
    #    チェーンの店舗一覧を回る方式では構造的に拾えないので、公式サイトを1件ずつ読んで入れる。
    ip = DATA / "independents.json"
    if ip.exists():
        d = json.loads(ip.read_text(encoding="utf-8"))
        for s_ in d["facilities"]:
            out.append({
                "segment": s_.get("segment", "indoor"),
                "brand": None, "brand_slug": None,
                "slug": s_["slug"],
                "name": s_["name"], "pref": s_.get("pref"), "zip": s_.get("zip"),
                "address": s_.get("address"), "access": s_.get("access"),
                "tel": s_.get("tel"), "hours": s_.get("hours"),
                "open_24h": s_.get("open_24h"), "closed": s_.get("closed"),
                "bays": s_.get("bays"), "bays_num": s_.get("bays_num"),
                "private_room": s_.get("private_room"), "parking": s_.get("parking"),
                "monthly_fee": s_.get("monthly_fee"), "usage_fee": s_.get("usage_fee"),
                "equipment": s_.get("equipment"),
                "distance_yard": s_.get("distance_yard"),
                "open": s_.get("open", True), "official": s_.get("official"),
                "source_url": s_["source_url"], "fetched_at": s_["fetched_at"],
            })

    # slugがぶつかったら、後から来たほうに連番を足す（URLは1つに1つ）
    seen = {}
    for x in out:
        if x["slug"] in seen:
            seen[x["slug"]] += 1
            x["slug"] = f'{x["slug"]}-{seen[x["slug"]]}'
        else:
            seen[x["slug"]] = 1

    dup = [k for k, v in __import__("collections").Counter(x["slug"] for x in out).items() if v > 1]
    # 読みの表に入れ忘れると郵便番号のままURLになる。必ず気づけるようにする。
    zipslug = [(x["slug"], x["name"]) for x in out if re.search(r"\d{7}", x["slug"])]
    (DATA / "facilities.json").write_text(json.dumps(
        {"generated_at": date.today().isoformat(), "count": len(out), "facilities": out},
        ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    print(f"施設マスタ: {len(out)}件（slug重複 {len(dup)}件 {dup[:5]}）")
    if zipslug:
        print(f"  🚨 郵便番号のままのURL {len(zipslug)}件 → scripts/build-romaji-slugs.py の表に追加する")
        for sl, nm in zipslug:
            print("     ", sl, "|", nm)
    print("  業態:", Counter(x["segment"] for x in out).most_common())
    print("  ブランド:", Counter(x["brand"] for x in out if x["brand"]).most_common())
    print("  都道府県:", len({x["pref"] for x in out if x["pref"]}), "種 /",
          Counter(x["pref"] for x in out if x["pref"]).most_common(8))
    print("  都道府県不明:", sum(1 for x in out if not x["pref"]))
    for k in ("address", "tel", "hours", "bays", "parking", "monthly_fee", "access"):
        print(f"    {k}: {sum(1 for x in out if x.get(k))}/{len(out)}")


main()
