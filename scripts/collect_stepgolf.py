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
   旧サイトは全店に**弾道測定機（スカイトラック）とスイング解析機**があると明記していた。
   2026-10 のリニューアル後はスカイトラックの記載が消え、店ごとのタグ（弾道解析・シミュレーター）と
   紹介文の機種名（GDR・GTRAK）だけになった。「弾道を計測できる屋内施設」という軸では対象に入る。
   そこで segment を 'lesson' として、屋内シミュレーションゴルフ（indoor）や
   弾道計測つき練習場（range）と**混ぜずに区別する**。探している人の目的が違う。
"""
import json
import re
import subprocess
import sys
import time
import unicodedata
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


def page_text(html):
    """RSCペイロードの手前の本文（紹介文の Richtext は <span style=…> なので spans() では拾えない）"""
    t = html.split("self.__next_f")[0]
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", t)
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return unescape(t)


NEWS_LISTS = ["/news", "/news/open"]


def news_facts():
    """公式ニュース（出店のプレスリリース）の「■打席数：5打席」「全5打席に弾道測定器（GTRAK…）」。
    記事1本＝1店のときだけ、その店の 打席数・機材 として使う（根拠URLは field_notes に残す）。
    「5打席の店舗をベースに全国713打席」のような全社の数字は店ごとの値にしない。"""
    paths = set()
    for lp in NEWS_LISTS:
        h = fetch(BASE + lp)
        paths |= set(re.findall(r'href="(/news/\d{10})"', h))
        time.sleep(1.2)
    out = {}
    for p in sorted(paths):
        h = fetch(BASE + p)
        time.sleep(1.2)
        t = re.sub(r"\s+", " ", page_text(h))
        # 記事の下に他の記事の見出し（『…店』）が並ぶので、店名は 店舗概要の「店舗名：」か記事タイトルから取る
        names = set(re.findall(r"■?店舗名[：:]\s*([^■]+?)\s*(?:■|所在地)", t))
        if not names:
            ttl = unescape((re.search(r"<title>([^<]*)", h) or [None, ""])[1])
            names = {x for x in re.findall(r"『([^』]+)』", ttl) if re.search(r"(店|EXtra .+)$", x)}
        # 「■店舗名：ステップゴルフプラス川越駅前店 https://…/store/kawagoe-ekimae_top」のように URL が続く記事がある
        names = {re.sub(r"\s+", "", unicodedata.normalize("NFKC", re.sub(r"https?://\S+", "", x))) for x in names}
        if len(names) != 1:
            continue
        name = names.pop()
        rec = {"url": BASE + p}
        # 開業前の判定（2026-10-18）: 新店の店舗ページには開業予定の記載が無く、普通の店として出る
        # （川越駅前・守口大日・横浜元町）。予定はニュースの店舗概要にだけある:
        #   「★グランドオープン：2026年12月4日（金）予定」／日付の無い記事は「■先行入会＆プレオープン：9月3日（木）～ 11月16日（月）」。
        # グランドオープン日が今日より後（日付が無ければプレオープンの最終日が今日以降）なら準備中にする。
        today = date.today()
        g = re.search(r"グランドオープン[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日", t)
        pre = re.search(r"プレオープン[：:][^■★]*?[～〜~]\s*(\d{1,2})月(\d{1,2})日", t)
        if g:
            if date(int(g[1]), int(g[2]), int(g[3])) > today:
                rec["not_open"] = f"{BASE + p} 「{g.group(0)}」"
        elif pre:
            pd = re.search(r"/news/(\d{2})(\d{2})", p)          # /news/2610030900 → 2026年10月の記事
            yr = 2000 + int(pd[1]) if pd else today.year
            if pd and int(pre[1]) < int(pd[2]):
                yr += 1                                        # 記事の月より前の月＝翌年
            if date(yr, int(pre[1]), int(pre[2])) >= today:
                rec["not_open"] = f"{BASE + p} 「{pre.group(0).strip()}」"
        m = (re.search(r"打席数[：:]\s*([0-9０-９]+)打席", t) or re.search(r"全([0-9０-９]+)打席に", t)
             or re.search(r"([0-9０-９]+)打席すべてに", t))
        if m:
            rec.update({"bays_num": int(unicodedata.normalize("NFKC", m.group(1))),
                        "equipment": "GTRAK" if "GTRAK" in t else ("GOLFZON GDR" if "GDR" in t else None),
                        "quote": t[max(0, m.start() - 10): m.end() + 30].strip()})
        if m or rec.get("not_open"):
            out[name] = rec
    return out


def _norm_name(x):
    x = re.sub(r"（[^）]*）$", "", x or "")
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", x))


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
        # 営業時間が「平日 / 12:00～20:00 / 土日祝 / 9:00～19:00」と曜日別に並ぶ店がある（福山御幸ほか・2026-10-20）。
        # 直前の1項目だけ取ると土日祝の時間だけが「店舗営業」になる → 「営業時間」の見出しから並びごと読む。
        h0 = max((k for k in range(max(0, i - 8), i) if sp[k] == "営業時間"), default=None)
        blk = sp[h0 + 1:i] if h0 is not None else []
        if len(blk) > 1 and all(x in ("平日", "土日祝") or (TIME.search(x) and len(x) < 20) for x in blk):
            parts.append("店舗営業 " + " ".join(f"［{x}］" if x in ("平日", "土日祝") else x for x in blk))
        elif store_h == "24時間営業" or TIME.search(store_h):
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
            elif x in ("平日", "土日祝", "土日・祝", "土・祝", "休憩", "土曜", "日曜", "祝日", "日祝", "土日"):
                # 「土・祝」（赤坂見附・2026-10-20）が無いと、そこで読むのを止めて以降のレッスンタイムが落ちていた
                parts.append("［" + x + "］")
            elif x.startswith("レッスンタイム以外は"):
                # 2026-10-16 に時刻の並びの後ろへ「レッスンタイム以外はセルフ営業となります」が入った。
                # 住所と取り違えないよう読み飛ばす（49店の住所の頭に混ざった）。
                pass
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
            if x.endswith(("プラン", "オプション", "会員")):   # Green Jacket 青葉台は「カジュアル会員」
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
    # 定休日: 店舗情報に「※コーチ定休日：」＋曜日（全150店）。店舗そのものの定休日の行は無い
    # （24時間営業の店もある＝その曜日もセルフ営業）。公式の語のまま「コーチ定休日」と書く。
    for n in range(len(sp) - 1):
        if sp[n].startswith("※コーチ定休日"):
            d["closed"] = "コーチ定休日：" + sp[n + 1]
            break
    # 駐車場: 店名の下のタグ「駐車場(提携含む）」と、店舗情報の住所・アクセス欄の駐車場の文。
    # タグも文も無い店は null（「無い」とは書かれていない。FAQ は「店舗によって異なります」）。
    if "店舗情報" in sp:
        i0 = sp.index("店舗情報")
        badges = [x for x in sp[:i0] if x in BADGES]
        d["features"] = badges or None
        i1 = sp.index("店舗の最新情報はこちら", i0) if "店舗の最新情報はこちら" in sp[i0:] else len(sp)
        lines = []
        for x in sp[i0:i1]:
            if "駐車" not in x or len(x) > 150:
                continue
            if re.search(r"駐車場[^ ]*ビル", x):      # 建物名（下関「シーモール駐車場新館ビル1階」）
                continue
            if "【お車" in x:
                x = x[x.index("【お車"):]
            elif not x.startswith(("★", "※")):
                toks = re.split(r"(?<=[ 、])", x)
                k = next(n for n, tk in enumerate(toks) if "駐車" in tk)
                x = "".join(toks[k:]).strip()
            lines.append(x)
        parts = (["駐車場(提携含む）"] if "駐車場(提携含む）" in badges else []) + lines
        if parts:
            d["parking"] = " ／ ".join(parts)
    # 機材: 店舗ページの紹介文に機種名を書いている店だけ（「全打席シミュレーション機器（GDR）設置」
    # 「全打席「GOLFZON社製GDR」シミュレーター完備」「ゴルフシミュレーターGTRAK全打席完備」）。
    # ⚠️ 以前は全店「スカイトラック」としていたが、2026-10 のリニューアル後の公式サイトにはどこにも
    #    スカイトラックの記載が無い（トップ・/system・全店舗ページ・ニュースを確認）。機種名の無い店は null。
    full = page_text(html)
    if "GTRAK" in full:
        d["equipment"] = "GTRAK"
    elif re.search(r"GDR", full):
        d["equipment"] = "GOLFZON GDR"
    if d.get("equipment"):
        d["equipment_quote"] = next((ln.strip() for ln in full.split("\n") if re.search(r"GTRAK|GDR", ln)), None)
    # 打席数: 店舗ページに「（9打席）」と書く店がある（2ブランド合併店舗）
    m = re.search(r"([0-9０-９]+)打席）", full)
    if m:
        n = int(unicodedata.normalize("NFKC", m.group(1)))
        d["bays"], d["bays_num"] = f"{n}打席", n
        d["bays_quote"] = re.sub(r"\s+", " ", full[max(0, m.start() - 20): m.end()]).strip()
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

    news = news_facts()
    print(f"ニュースの店舗概要（打席数）: {len(news)}本")
    used_news = set()

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
            "closed": x.get("closed"),
            "parking": x.get("parking"),
            "bays": x.get("bays"),
            "bays_num": x.get("bays_num"),
            "private_room": None,       # 個室の記載なし
            "equipment": x.get("equipment"),
            "features": x.get("features"),   # 店名の下のタグ（スイング解析・弾道解析・シミュレーター 等）
            "open": x.get("open", True),
            "official": url,
            "source_url": url,
            "fetched_at": date.today().isoformat(),
        }
        notes = {}
        nf = news.get(_norm_name(rec["name"]))
        if nf:
            used_news.add(_norm_name(rec["name"]))
            if nf.get("not_open"):
                rec["open"] = False
                rec["note"] = "公式ニュース " + nf["not_open"]
            if not rec["bays_num"] and nf.get("bays_num"):
                rec["bays"], rec["bays_num"] = f"{nf['bays_num']}打席", nf["bays_num"]
                notes["bays"] = f"{nf['url']} 「{nf['quote']}」"
            if not rec["equipment"] and nf.get("equipment"):
                rec["equipment"] = nf["equipment"]
                notes["equipment"] = f"{nf['url']} 「{nf['quote']}」"
        if x.get("equipment_quote"):
            notes["equipment"] = f"{url} 「{x['equipment_quote']}」"
        if x.get("bays_quote"):
            notes["bays"] = f"{url} 「{x['bays_quote']}」"
        if rec["parking"]:
            notes["parking"] = f"{url} 店名の下のタグ「駐車場(提携含む）」／店舗情報の住所・アクセス欄"
        if rec["closed"]:
            notes["closed"] = "店舗ページの店舗情報「※コーチ定休日：」（レッスンタイム以外はセルフ営業）"
        if notes:
            rec["field_notes"] = notes
        out.append(rec)
        if i % 25 == 0 or i == len(paths):
            print(f"  {i}/{len(paths)}")
        time.sleep(1.0)
    if gone:
        print("店舗ページが無いURL:", gone)

    p = ROOT / "data" / "stepgolf.json"
    p.write_text(json.dumps({"generated_at": date.today().isoformat(),
                             "count": len(out), "stores": out}, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    ok = sum(1 for x in out if x["pref"])
    print(f"\n保存: {p} ({len(out)}店 / 都道府県を取れた {ok}店 / "
          f"営業時間 {sum(1 for x in out if x['hours'])} / 電話 {sum(1 for x in out if x['tel'])} / "
          f"月会費 {sum(1 for x in out if x['monthly_fee'])} / 定休日 {sum(1 for x in out if x['closed'])} / "
          f"駐車場 {sum(1 for x in out if x['parking'])} / 打席 {sum(1 for x in out if x['bays_num'])} / "
          f"機材 {sum(1 for x in out if x['equipment'])})")
    unused = set(news) - used_news
    if unused:
        print("  ニュースの店名が店舗データと一致しなかった:", sorted(unused))
    miss = [x["name"] for x in out if not x["pref"]]
    if miss:
        print("  都道府県を取れなかった店（住所の書式が違う）:", miss[:5])
    return 0


if __name__ == "__main__":
    sys.exit(main())
