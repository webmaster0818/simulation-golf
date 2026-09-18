#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日本語の店名しか無い施設に、地名のローマ字URLを割り当てる。

■ なぜ表を手で持つのか
  郵便番号から住所のカナを取って機械的にローマ字化する方法を最初に試したが、
  使えなかった。実際に出た誤りが以下:
    ・三宿(ﾐｼｭｸ) → 末尾の「ク」を行政区画の「区」と誤認して mishu
    ・新宿 → shinju / 両国 → ryougo （同じ原因）
    ・本牧店 → honmokumiyabara（郵便番号の町域が「本牧宮原」だったため）
    ・相模原店 → sagamiharashichuuou（市区町村名をまるごと拾った）
  店名の地名と、郵便番号が指す町域は一致しないことが多い。
  URLは公開後に変えると検索評価が失われるので、1件ずつ確認した表を持つ。

■ 読みの裏取り
  読み間違えやすいものは日本語版Wikipediaの冒頭の読み仮名で確認した（2026-09-12）:
    江古田=えこだ（練馬区・西武池袋線。中野区の「えごた」ではない）
    高座渋谷=こうざしぶや / 本厚木=ほんあつぎ / 武蔵中原=むさしなかはら
    希望ヶ丘=きぼうがおか / 荒川沖=あらかわおき / 黄金町=こがねちょう
    四軒家=しけんや / 千音寺=せんのんじ / 豊山=とよやま / 大口=おおぐち
    鮫洲=さめず / 茅場町=かやばちょう / 西長堀=にしながほり
    桜ノ宮=さくらのみや / 今里=いまざと / 堺東=さかいひがし

■ 表記の方針
  長音は伸ばさない（Tokyo方式）。大船=ofuna、府中=fuchu、本郷=hongo。
  建物名・商業施設名が店名に入っている場合は、探されるのは地名なので地名を採る
  （「ミロクジーナ藤沢店」→ fujisawa、「イオンモール土浦店」→ tsuchiura）。

■ 出力
  data/slug-romaji.json … {郵便番号slug: ローマ字slug}
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 郵便番号slug → 地名のローマ字
PLACE = {
    # GOLF NEXT 24
    'golf-next-24-0010908': 'shinkotoni',            # DCM新琴似
    'golf-next-24-4860818': 'sendai-nishikigaoka',   # 仙台錦ケ丘
    'golf-next-24-3000811': 'tsuchiura',             # イオンモール土浦
    'golf-next-24-3360926': 'higashi-urawa',
    'golf-next-24-3540021': 'tsuruse',               # 鶴瀬
    'golf-next-24-3501305': 'sayama',
    'golf-next-24-3430034': 'koshigaya',
    'golf-next-24-3590046': 'tokorozawa',
    'golf-next-24-1870002': 'nishi-tokyo',           # 有賀園ゴルフ西東京
    'golf-next-24-2080034': 'musashi-murayama',
    'golf-next-24-2110053': 'musashi-nakahara',
    'golf-next-24-2150004': 'shin-yurigaoka',
    'golf-next-24-2310804': 'honmoku',               # 本牧
    'golf-next-24-2240001': 'nakagawa',
    'golf-next-24-2591331': 'hadano-shibusawa',      # 秦野渋沢
    'golf-next-24-2520142': 'hashimoto',
    'golf-next-24-2520216': 'sagamihara',
    'golf-next-24-2850850': 'yukarigaoka',           # ユーカリが丘
    'golf-next-24-4910872': 'ichinomiya',
    'golf-next-24-5740026': 'suminodo',              # 住道
    'golf-next-24-5810872': 'yao',                   # フォレストモール八尾
    'golf-next-24-6580027': 'higashinada',           # 東灘
    'golf-next-24-6830805': 'yonago',

    # GOLFERS24
    'golfers24-1310033': 'mukojima',                 # 向島
    'golfers24-1030002': 'nihonbashi-bakurocho',     # 日本橋馬喰町
    'golfers24-1410031': 'gotanda',
    'golfers24-1010047': 'otemachi',
    'golfers24-3700073': 'takasaki',
    'golfers24-3210954': 'utsunomiya-higashiguchi',  # 宇都宮駅東口
    'golfers24-3300852': 'omiya',
    'golfers24-5600003': 'toyonaka',
    'golfers24-5500013': 'nishi-nagahori',           # 西長堀
    'golfers24-8150082': 'hirao-takamiya',           # 平尾高宮
    'golfers24-8100074': 'fukuoka-ohorikoen',        # 福岡大濠公園

    # SWING24/7
    'swing247-1940013': 'machida',
    'swing247-1760004': 'ekoda',                     # 江古田（えこだ）
    'swing247-2410825': 'kibogaoka',                 # 希望ヶ丘
    'swing247-2420023': 'koza-shibuya',              # 高座渋谷駅前
    'swing247-2510016': 'fujisawa',                  # ミロクジーナ藤沢
    'swing247-2430031': 'atsugi',                    # アツギトレリス
    'swing247-2270062': 'aobadai',                   # パルテ青葉台
    'swing247-2160006': 'miyamaedaira',
    'swing247-2310053': 'koganecho',                 # 黄金町・本店
    'swing247-2470056': 'ofuna',                     # 大船
    'swing247-2240007': 'tsuzuki-kohoku',            # 都筑・港北ニュータウン
    'swing247-2110014': 'kawasaki-hirama',           # 川崎平間
    'swing247-2510047': 'tsujido',                   # 辻堂
    'swing247-2440811': 'totsuka',
    'swing247-2300077': 'yokohama-tsurumi',          # ウェイクロード横浜鶴見
    'swing247-2240001': 'nakagawa',
    'swing247-2210044': 'higashi-kanagawa',
    'swing247-2400013': 'hodogaya',                  # 保土ヶ谷
    'swing247-2430018': 'hon-atsugi',                # 本厚木
    'swing247-2140014': 'noborito',                  # 登戸・向ヶ丘遊園
    'swing247-2110053': 'musashi-nakahara',
    'swing247-2320014': 'yoshinocho',                # 吉野町
    'swing247-1730014': 'itabashi-kuyakushomae',     # 板橋区役所前
    'swing247-1410032': 'osaki',                     # 大崎
    'swing247-1140015': 'komagome',
    'swing247-1830045': 'fuchu',                     # 府中
    'swing247-1400011': 'samezu',                    # 鮫洲
    'swing247-1130021': 'hon-komagome',
    'swing247-1440052': 'kamata',
    'swing247-1040033': 'kayabacho',                 # 茅場町
    'swing247-1400013': 'omori',
    'swing247-1670043': 'ogikubo',
    'swing247-1600022': 'shinjuku',
    'swing247-1130024': 'kasuga',
    'swing247-1130033': 'hongo',                     # 本郷
    'swing247-1540005': 'mishuku',                   # 三宿
    'swing247-1300026': 'ryogoku',                   # 両国
    'swing247-1050014': 'mita',
    'swing247-1350042': 'kiba',
    'swing247-1770033': 'nerima-takanodai',
    'swing247-3630012': 'okegawa',
    'swing247-3502203': 'tsurugashima',
    'swing247-2600031': 'chiba',
    'swing247-3200033': 'utsunomiya',
    'swing247-3001152': 'arakawaoki-higashi',        # 荒川沖東
    'swing247-9591244': 'tsubame',                   # 燕
    'swing247-4800201': 'toyoyama',                  # 豊山
    'swing247-4800141': 'oguchi',                    # 大口
    'swing247-4540972': 'sennonji',                  # 千音寺アズタウン
    'swing247-4630032': 'shikenya',                  # 四軒家
    'swing247-4620841': 'kurokawa',                  # 黒川
    'swing247-5340027': 'sakuranomiya',              # 桜ノ宮
    'swing247-5900074': 'sakai-higashi',             # 堺東
    'swing247-5760041': 'katano',                    # 交野
    'swing247-5330032': 'osaka-awaji',               # 大阪淡路
    'swing247-5370014': 'imazato',                   # 今里
    'swing247-7210973': 'fukuyama-zao',              # 福山蔵王
    'swing247-8140022': 'fukuoka-hara',
    'swing247-8120054': 'fukuoka-hakozaki',
    'swing247-8160814': 'fukuoka-kasuga',
}


def main() -> None:
    """表だけから対応表を書き出す。

    ⚠️ facilities.json を読んで突き合わせない。
       facilities.json は既にこの表を適用したあとの状態になり得るため、
       「対象0件」と誤判定する（実際に一度それで表を壊しかけた）。
       取りこぼしの検出は build-facilities.py 側（郵便番号が残っていないか）で行う。
    """
    out = {}
    for key, place in PLACE.items():
        m = re.fullmatch(r"(.+)-(\d{7})", key)
        if not m:
            raise SystemExit(f"キーの形が違う: {key}")
        out[key] = f"{m.group(1)}-{place}"

    dup = [v for v, n in __import__("collections").Counter(out.values()).items() if n > 1]
    (ROOT / "data" / "slug-romaji.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    print(f"対応表 {len(out)}件 → data/slug-romaji.json")
    if dup:
        raise SystemExit(f"🚨 ローマ字slugが重複している: {dup}")
    print("✅ 重複なし")


main()
