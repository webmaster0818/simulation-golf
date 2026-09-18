# simulation-golf — シミュレーションゴルフ施設の比較サイト

Discord ch: `1545713475207041076`（#project-simulation-golf）／依頼者: MediaXAI
参考にした構造: BEST-FIT（https://bestfit-site.pages.dev ・239ブランド1,249店舗）
収益モデル: アフィリエイトによる店舗送客（サイトが育てば掲載も視野）

## 🚨 このサイトの原則（先に決めたこと）

- **公式サイトに書いてあることだけ載せる。** 書いていない項目は「公式サイトに記載なし」と出す。
  推測で埋めると一覧の見栄えは良くなるが、行ってみたら違う、が起きる。
- **口コミ・評価（★）は載せない。** 点数をつけると集めた店が有利になる。
  「どこに何があって、何が公開されているか」までに留める。
- **施設ごとに出典URLと取得日を必ず持つ**（`source_url` / `fetched_at`）。
- **「記載なし」は「設備が無い」ではない。** 文言でそう明示する。

## データの作り方

```
scripts/collect-toptracer.py      GDO トップトレーサー導入練習場 144件（2秒間隔）
scripts/normalize-toptracer.py    郵便番号分離・都道府県抽出・HTML残骸除去
scripts/collect_golfnext24.py     GOLF NEXT 24    29件（一覧1枚に全項目）
scripts/collect_swing247.py       SWING24/7       60件（営業中58・オープン予定2）
scripts/collect_golfeed24.py      GOLFEED24       20件（店舗ページの表）
scripts/collect_golfers24.py      GOLFERS24       11件（住所のみ公開・運営会社の行を除外済み）
scripts/collect_lahagolf24.py     ラハゴルフ24     22件（★店舗別の月会費あり）
scripts/collect_fit24.py          FiT24           28件（店舗検索のJSデータから）
scripts/build-romaji-slugs.py     日本語店名94件の地名ローマ字対応表 → data/slug-romaji.json
scripts/build-facilities.py       → data/facilities.json（314件）
```

### ハマったところ（次にブランドを足すとき読む）

- **住所に都道府県が無い施設がある**（「名古屋市北区…」「岡山市北区…」）。
  市名→都道府県の対応表で補う。推測できない市名は補わない。
- **郵便番号のハイフンに全角「ｰ」が混ざる**施設がある（大垣ゴルフレインジ）。
- **オープン予告の行が住所に見える**（「9月下旬町田店OPEN予定!!」＝町＋数字）。
  住所判定より先にオープン予告を判定する。
- **県セクションの見出し行**（「神奈川県」「Kanagawa」単体）が次の店舗ブロックに混ざる。
- **店名が日本語だけのブランドはslugが全店衝突する**（SWING24/7 等）。
  → URLは `{ブランド}-{地名ローマ字}` で全ブランド統一。地名は `scripts/build-romaji-slugs.py` の表。
  **郵便番号のカナから機械的にローマ字化する方法は失敗した**（三宿→mishu／新宿→shinju／
  本牧→honmokumiyabara／相模原→sagamiharashichuuou）。店名の地名と郵便番号の町域は一致しない。
  読みが怪しいものは日本語版Wikipediaの読み仮名で1件ずつ裏を取る（江古田=えこだ 等）。
  表に入れ忘れると郵便番号のままURLになるので、build-facilities.py が検知して警告する。
- **一覧の下にある運営会社を店舗として拾っていた**（GOLFERS24＝株式会社StudioX。12→11件に訂正）。
  店舗判定は「◯◯店」で終わること。住所に `&nbsp;` が混ざる点にも注意。
- **公式のURLが日本語のままの店舗がある**（ラハゴルフ24 /list/横浜東口店/）。
  URLエンコードされたパスになるので、こちらでローマ字を割り当てる。
- **出典側に金額が入っていないことがある**（Pacific GOLF CLUB の利用料が「円」だけ）。
  数字が無い金額は null にする。`150円` のように読める値を作らない。
- **「個室数」を打席数として扱うと個室の絞り込みから丸ごと漏れる**（GOLF NEXT 24 で29件漏れていた）。
  ブランドごとに項目の意味を確認する。
- **ラハゴルフ24は公式の「アクセス」欄に駐車場を混ぜて書いている**。
  駐車場で絞れるよう parking にも入れるが、原文は access に残す。

### 取得できなかったもの

- **ステップゴルフ（164店）**: 店舗ページの住所がJavaScriptで描画される。
  WordPress REST API（`/wp-json/wp/v2/store`）は slug と店名しか返さず、ACFも空。
  ブラウザを動かせば取れるが149ページぶんかかる。レッスンスクール業態で意図が違うため後回し。
- **i8 GOLF（7店）**: 規模が小さいため優先度を下げている。

## サイト

Next.js 15 / 静的書き出し（`output:'export'` `trailingSlash:true`）/ プレーンCSS。
366URL（TOP・エリア35・ブランド7・施設314・機材2・条件4・データ1・一覧2）。
施設ページのURLは `/facility/{ブランド}-{地名}/`（例: `/facility/swing247-ekoda/`）。

- **見た目の芯**: 「夜の無人インドア練習場」。暗い背景に弾道の軌跡。
  ライム（`--trace`）は**計測された数字にしか使わない**。装飾に使うと数字が埋もれる。
- 書体: Chakra Petch（英数字・計測器の気配）× Zen Kaku Gothic New（本文）。
- ⚠️ **layout.tsx に canonical を置かない**。置くと全ページがトップを正規URLとして宣言する
  （他サイトで実際に起きた事故）。canonical は各ページで個別に付ける。

## 未確定（MediaXAI回答待ち・2026-09-12時点）

1. ~~施設ページのURL~~ → **2026-09-12「Bで」＝ローマ字で確定・適用済み**
2. **リポジトリ作成とCloudflare Pages連携**（🚨 新規リポは必ず public。privateはCFの一覧に出ない）
3. **ドメイン**
