#!/usr/bin/env python3
"""ステップゴルフ（www.stepgolf.co.jp）の店舗を収集する。

⚠️ 2026-10-14: 公式サイトが Next.js（Yappli CMS）に作り直され、旧パーサは0店になった。
   一覧の HTML は100店まで・住所/営業時間/料金は店舗ページの <span> に見出し無しで並ぶ。
   一覧＋公式マイマップ（/store/map の KML）＋前回データのURL の和集合を見に行く。

⚠️ CLAUDE.md に「店舗ページの住所がJavaScriptで描画される／ブラウザを動かせば取れるが
   149ページぶんかかる」と書いてあったが、2026-09-23に実測したら**両方とも違った**。
   - 店舗一覧 https://www.stepgolf.co.jp/store/ に**全店の店名と住所がHTMLで入っている**
     （`storeList__listItemLinkHeader` と `storeList__listItemLinkTxt`）。
   - 店舗ページの住所も curl でそのまま取れる。JS描画ではない。
   当時の調査時はドメインを step-golf.co.jp と誤っていた可能性が高い（正は stepgolf.co.jp）。

⚠️ 業態がこのサイトの他の施設と違う。ステップゴルフは**完全予約制・コーチ付き・月会費制の
   レッスンスクール**で、自分の好きな時間に打ちに行く場所ではない。
   ただし全店に**弾道測定機（スカイトラック）とスイング解析機**があると公式が明記しており、
   「弾道を計測できる屋内施設」という軸では対象に入る。
   そこで segment を 'lesson' として、屋内シミュレーションゴルフ（indoor）や
   弾道計測つき練習場（range）と**混ぜずに区別する**。探している人の目的が違う。
"""
import json
import re
import subprocess
import sys
import time
from html import unescape
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.stepgolf.co.jp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CACHE = ROOT / "data" / ".stepgolf-cache"


def fetch(url, timeout=40, min_len=5000):
    """同じ日の取り直しだけキャッシュを使う（日付ごとのディレクトリ）。
    ⚠️ 以前は日付なしのキャッシュで、一度取った店は二度と取り直されなかった。"""
    import hashlib
    cp = CACHE / date.today().isoformat() / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    if cp.exists():
        return cp.read_text(encoding="utf-8", errors="ignore")
    r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True, timeout=timeout + 15)
    h = r.stdout or ""
    if len(h) > min_len:
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(h, encoding="utf-8")
    return h


def text_of(html):
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html)
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


PREFS = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県",
         "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県",
         "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府",
         "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県",
         "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県",
         "鹿児島県", "沖縄県"]


# 住所に都道府県が書かれていない店がある（例:「横浜市港北区新羽町…」）。
# 推測できる市名だけを表にする。表に無いものは補わない（当てずっぽうで県名を作らない）。
CITY_PREF = {"横浜市": "神奈川県", "川崎市": "神奈川県", "相模原市": "神奈川県",
             "名古屋市": "愛知県", "大阪市": "大阪府", "京都市": "京都府", "神戸市": "兵庫県",
             "札幌市": "北海道", "仙台市": "宮城県", "さいたま市": "埼玉県", "千葉市": "千葉県",
             "広島市": "広島県", "福岡市": "福岡県", "北九州市": "福岡県", "岡山市": "岡山県",
             "熊本市": "熊本県", "新潟市": "新潟県", "静岡市": "静岡県", "浜松市": "静岡県",
             "堺市": "大阪府"}

ZIP = re.compile(r"^〒?\s*(\d{3}-?\d{4})\s*")


def split_zip(addr):
    """先頭の郵便番号を住所から切り離す。〒が付くものと付かないものが混在している。"""
    m = ZIP.match(addr)
    if not m:
        return None, addr
    z = m.group(1)
    z = z if "-" in z else f"{z[:3]}-{z[3:]}"
    return z, addr[m.end():].strip()


def pref_of(addr):
    for p in PREFS:
        if addr.startswith(p):
            return p
    for city, p in CITY_PREF.items():
        if addr.startswith(city):
            return p
    return None


def spans(html):
    """2026-10 のリニューアル後（Next.js＋Yappli CMS）。本文は <span> に1項目ずつ入っている。
    後ろの self.__next_f（RSCペイロード）に同じ文字列が重複して入るので、その手前だけを見る。"""
    html = html.split("self.__next_f")[0]
    out = []
    for x in re.findall(r"<span>([^<]*)</span>", html):
        x = re.sub(r"\s+", " ", unescape(x)).strip()
        if x:
            out.append(x)
    return out


def parse_index(html):
    """店舗一覧のカードから URL / 店名 / 住所 を取る。
    ⚠️ 2026-10-14 実測: 一覧の HTML には**100店しか入っていない**（150店中）。残りはクライアント側で
       描画される。そこで店舗一覧ページに埋め込まれた公式の Google マイマップ（/store/map）の
       KML からも店舗URLを集め、和集合をとる。"""
    out = {}
    body = html.split("self.__next_f")[0]
    for c in re.split(r'<a data-cms-type="card"', body)[1:]:
        m = re.search(r'href="(/store/[A-Za-z0-9_-]+)"', c)
        if not m:
            continue
        sp = [unescape(x).strip() for x in re.findall(r"<span>([^<]*)</span>", c.split("</a>")[0])]
        sp = [x for x in sp if x and x != "NEW"]
        rec = {"url": BASE + m.group(1)}
        if len(sp) >= 3:
            rec["name"] = sp[0] + sp[1]
            rec["address"] = sp[2] + (" " + sp[3] if len(sp) > 3 and not is_badge(sp[3]) else "")
        out[m.group(1)] = rec
    return out


BADGES = {"駐車場(提携含む）", "スイング解析", "弾道解析", "シミュレーター", "24時間営業", "NEW"}


def is_badge(x):
    return x in BADGES


MAP_MID = "1gnzwSI0U9O8y7MexlXvjyAwd1TmB76U"   # /store/map に埋め込まれているマイマップ


def map_store_paths():
    k = fetch(f"https://www.google.com/maps/d/kml?mid={MAP_MID}&forcekml=1", min_len=1000)
    paths = set()
    for d in re.findall(r"<description>(.*?)</description>", k, re.S):
        m = re.search(r"stepgolf\.co\.jp(/store/[A-Za-z0-9_-]+)", d)
        if m:
            paths.add(m.group(1))
    return paths


# 新サイトの店舗ページに「市区町村から」書いていない店。旧サイト（2026-09-23 取得）の住所の市まで補う。
ADDR_PREFIX = {"moriguchi_dainichi_top": "大阪府守口市"}

# 公式の誤記（与那原町に「宇東浜」は無い。正しくは 字東浜／旧サイトは「東浜」）
ADDR_TYPO = {"family-okinawa_top": [("与那原町宇東浜", "与那原町東浜")]}


def _street(a):
    """建物名を除いた番地まで（全角/半角・空白・ハイフンの揺れをならす）"""
    import unicodedata
    a = unicodedata.normalize("NFKC", a or "")
    a = re.sub(r"[\s　‐‑–—−ー－]", "", a.replace("丁目", "-").replace("番地", "").replace("番", "-").replace("号", ""))
    m = re.match(r"(.*?\d+(?:-\d+)*)", a)
    return m.group(1) if m else a


TIME = re.compile(r"\d{1,2}[:：]\d{2}")


def parse_store(html, path):
    sp = spans(html)
    d = {}
    if "店舗情報" in sp:
        i = sp.index("店舗情報")
        d["name"] = sp[i + 1] + sp[i + 2]
        if re.match(r"0\d", sp[i + 3]):
            d["tel"] = re.sub(r"[ｰ₋−－]", "-", sp[i + 3])
    # 営業時間: 「レッスンタイム」の直前が店舗の営業時間（24時間営業 / 6:00～23:00）。
    # そこから住所の手前までが レッスンタイム の見出しと時刻の並び。
    if "レッスンタイム" in sp:
        i = sp.index("レッスンタイム")
        parts = []
        store_h = sp[i - 1]
        if store_h == "24時間営業" or TIME.search(store_h):
            parts.append(f"店舗営業 {store_h}")
        parts.append("レッスンタイム")
        j = i + 1
        label_next = False
        while j < len(sp):
            x = sp[j]
            if label_next:
                parts.append(x); label_next = False
            elif x.startswith("※") and x.endswith(("：", ":")):
                parts.append("［" + x.strip("※：:") + "］"); label_next = True
            elif TIME.search(x) and len(x) < 40:
                parts.append(x)
            elif x in ("平日", "土日祝", "土日・祝", "休憩", "土曜", "日曜", "祝日", "日祝", "土日"):
                parts.append("［" + x + "］")
            else:
                break
            j += 1
        d["hours"] = " ".join(parts)
        # 住所: 時刻の並びの直後。「店舗の最新情報はこちら」までに 住所・建物・アクセス が並ぶ（建物・アクセスは無い店もある）
        tail = []
        while j < len(sp) and sp[j] not in ("店舗の最新情報はこちら", "友だちを追加", "店長兼コーチ®"):
            tail.append(sp[j]); j += 1
        if tail:
            d["page_address"] = tail[0]
            rest = tail[1:]
            acc = [x for x in rest if re.search(r"(駅|徒歩|車で|バス|IC|インター)", x)]
            # 「★駐車場8台完備★ 必ず地下駐車場を…」のような案内文が住所の並びに入る店がある（宮内店）
            bld = [x for x in rest if x not in acc and not re.search(r"[★※]|ご遠慮|ご利用ください", x)]
            if bld:
                d["page_address"] += " " + " ".join(bld)
            if acc:
                d["access"] = " ".join(acc)
    # 料金: 「料金プラン」から「店舗情報」まで。プラン名のあとに ￥ 税抜 〜 税込 ￥ 税込額 が並ぶ。
    # 月会費は従来どおり最安のプラン（オプションは単体で契約できないので除く）。
    if "料金プラン" in sp and "店舗情報" in sp:
        seg = sp[sp.index("料金プラン") + 1: sp.index("店舗情報")]
        plans, name = [], None
        k = 0
        while k < len(seg):
            x = seg[k]
            if x.endswith("プラン") or x.endswith("オプション"):
                name = x
            elif x == "￥" and name and k + 1 < len(seg):
                price = seg[k + 1]
                tax = None
                for m in range(k + 2, min(k + 8, len(seg) - 1)):
                    if seg[m] == "￥":
                        tax = seg[m + 1]; break
                frm = "〜" if k + 2 < len(seg) and seg[k + 2] == "〜" else ""
                # セルフタイムのプラン/オプションは月会費の最安に入れない（朝霞店の「全日セルフタイムプラン
                # 1,980円」はレッスンプランへの上乗せ。旧サイト時代も月会費は平日デイ(タイム)プランだった）
                if not re.search(r"セルフ|ジュニア", name) and not name.endswith("オプション") and tax:
                    plans.append((int(price.replace(",", "")), f"・{name} {price}円{frm}(税込{tax}円{frm})"))
                name = None
                k = m + 2 if tax else k + 2
                continue
            k += 1
        if plans:
            d["monthly_fee"] = min(plans)[1]
    t = " ".join(sp)
    # 旧サイトでは「グランドオープン予定 YYYY年M月D日」を本文に書いていた。新サイトでも同じ語を見る。
    # ⚠️ ヘッダ/フッタの「オープン準備中」は全店共通なので使わない（旧サイトで全店が準備中になった）。
    d["open"] = not re.search(r"(近日オープン|OPEN予定|オープン予定)", t)
    return d


def main():
    idx = fetch(f"{BASE}/store/")
    if len(idx) < 50000:
        print("店舗一覧を取得できませんでした", file=sys.stderr)
        return 1
    listing = parse_index(idx)
    mp = map_store_paths()
    # 前回のデータの店舗URLも見に行く（一覧の100店にもマイマップにも出ない店がある＝西条店・2026-10-14）。
    # 店舗ページが残っていれば載せ、404 なら落とす。
    prev, prev_rec = set(), {}
    pp = ROOT / "data" / "stepgolf.json"
    if pp.exists():
        for x in json.loads(pp.read_text(encoding="utf-8"))["stores"]:
            m = re.search(r"(/store/[A-Za-z0-9_-]+)", x["official"])
            if m:
                prev.add(m.group(1))
                prev_rec[re.sub(r"_top$", "", m.group(1))] = x
    paths = sorted((set(listing) | mp | prev) - {"/store/map"})
    print(f"一覧 {len(listing)}店 ／ マイマップ {len(mp)}店 ／ 前回 {len(prev)}店 ／ 和集合 {len(paths)}店")

    out, gone = [], []
    for i, path in enumerate(paths, 1):
        url = BASE + path
        h = fetch(url)
        if "店舗情報" not in h:
            gone.append(path)      # 404（マイマップに古いURLが残っている等）
            continue
        slug = path.rsplit("/", 1)[-1]
        x = parse_store(h, path)
        li = listing.get(path, {})
        raw = li.get("address") or x.get("page_address") or ""
        if slug in ADDR_PREFIX and not raw.startswith(ADDR_PREFIX[slug]):
            raw = ADDR_PREFIX[slug] + raw
        for a, b in ADDR_TYPO.get(slug, ()):
            raw = raw.replace(a, b)
        zipcode, addr = split_zip(raw)
        # 新サイトは郵便番号も店名の括弧書き（「（TSUTAYA札幌菊水店内）」等）も出さない。
        # 店名は前回の表記を保つ（slug・ページタイトルを揺らさない）。郵便番号は住所の番地まで同じときだけ引き継ぐ。
        pv = prev_rec.get(re.sub(r"_top$", "", path)) or prev_rec.get(re.sub(r"_top$", "", path) + "_top")
        if pv:
            x["name"] = pv["name"]
            if not zipcode and pv.get("zip") and _street(pv["address"]) == _street(addr):
                zipcode = pv["zip"]
        rec = {
            "segment": "lesson",
            "brand": "ステップゴルフ",
            "brand_slug": "stepgolf",
            "name": x.get("name") or li.get("name"),
            "pref": pref_of(addr),
            "zip": zipcode,
            "address": addr,
            "access": x.get("access"),
            "tel": x.get("tel"),
            "hours": x.get("hours"),
            "open_24h": False,          # 完全予約制のスクール。24時間営業ではない
            "monthly_fee": x.get("monthly_fee"),
            # 公式が全店「弾道測定機（スカイトラック）・スイング解析機 完備」と明記
            "equipment": "スカイトラック（弾道測定機）",
            "open": x.get("open", True),
            "official": url,
            "source_url": url,
            "fetched_at": date.today().isoformat(),
        }
        out.append(rec)
        if i % 25 == 0 or i == len(paths):
            print(f"  {i}/{len(paths)}")
        time.sleep(0.4)
    if gone:
        print("店舗ページが無いURL:", gone)

    p = ROOT / "data" / "stepgolf.json"
    p.write_text(json.dumps({"generated_at": date.today().isoformat(),
                             "count": len(out), "stores": out}, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    ok = sum(1 for x in out if x["pref"])
    print(f"\n保存: {p} ({len(out)}店 / 都道府県を取れた {ok}店 / "
          f"営業時間 {sum(1 for x in out if x['hours'])} / 電話 {sum(1 for x in out if x['tel'])} / "
          f"月会費 {sum(1 for x in out if x['monthly_fee'])})")
    miss = [x["name"] for x in out if not x["pref"]]
    if miss:
        print("  都道府県を取れなかった店（住所の書式が違う）:", miss[:5])
    return 0


if __name__ == "__main__":
    sys.exit(main())
