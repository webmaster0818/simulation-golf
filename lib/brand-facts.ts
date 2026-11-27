/**
 * ブランドページ冒頭の「答え」に使う、公式サイトで確認した事実。
 * ⚠️ ここに書く値は、公式ページを開いて確認した日（checked）とURLを必ず持つ。
 *    推測・第三者サイトの値は入れない。確認できない項目は書かない（null）。
 * 2026-11-02 追加（GSC で「ステップゴルフ」「マイゴル」が店舗ページに着地し、
 * 「door to golf」はブランドページで7〜8位。表記ゆれ・料金・店舗数・体験を冒頭で答える）。
 */
export type BrandFact = {
  /** 検索で使われる別表記（英字／カナ）。title・h1 に併記する */
  alt: string
  /** 公式サイトが自ら示している店舗数（無ければ null＝当サイトの掲載件数だけを出す） */
  officialCount: { text: string; url: string } | null
  /** 体験の案内（公式の文言どおり） */
  trial: { text: string; url: string } | null
  /** 運営会社（公式の会社概要・特商法表記で確認できたものだけ） */
  company: { text: string; url: string } | null
  /** 公式の店舗一覧（店舗検索）ページ */
  storeList: string
  checked: string
  /** 月会費の範囲を掲載データから計算できないブランド（プラン別の金額が monthly_fee に無い）で、公式の全店舗の料金表を読んだ値 */
  feeFixed?: { min: number; minSlug: string; minName: string; minPlan: string; max: number; maxSlug: string; maxName: string; n: number }
  /** 月会費のほかにかかる費用の注記（title の「月会費」だけで安く見えないように） */
  feeNote?: string
  /** 店舗ページ冒頭のブランド一覧への導線を出さない（ブランドページだけ変えて効果を切り分けるとき） */
  noStoreJump?: boolean
  /** 店舗数の「公式の数には、当サイトで…確認できていない店舗が含まれる場合があります」を出さない（公式の数が掲載より少ないとき） */
  countNoteOff?: boolean
  /** title の「の店舗一覧」の前に入れる語（例 '料金・' → 「◯◯の料金・店舗一覧」）。検索語に「料金」があるブランドだけ */
  titleWord?: string
  /**
   * meta description を差し替える（任意）。feeNote は /guide/golf-subscription/ にも出るので、
   * ブランドページだけで料金の答えを description に出したいときはこちらを使う（2026-11-27 追加）
   */
  description?: string
  /**
   * 掲載データから月会費を計算できない（公式に金額が無い）ブランドの title の「｜」以降（任意）。
   * これがあると feeRange が null でも「名称（別表記）の…店舗一覧N件｜<titleTail>」の title にする（2026-11-27 チキンゴルフ）
   */
  titleTail?: string
  /**
   * ブランドページの h1 直下に出す「◯◯の答え」の早見表（任意・このフィールドがあるブランドだけに出る）。
   * feeMin/feeMax は公式の料金表全体の幅（掲載データの feeRange は各店の代表プランだけなので、ブランドページの title・lead はこちらを使う）。
   * 店舗ページの「全◯店舗（月会費…）」は feeRange のまま（店舗ページは動かさない）。
   */
  answer?: {
    heading: string
    rows: { k: string; v: string }[]
    sources: { label: string; url: string }[]
    checked: string
    feeMin?: number
    feeMax?: number
  }
}

export const BRAND_FACTS: Record<string, BrandFact> = {
  stepgolf: {
    alt: 'STEP GOLF',
    officialCount: {
      text: '公式サイトのトップページでは「店舗数 165店舗」「打席数 853打席」と案内されています',
      url: 'https://www.stepgolf.co.jp/',
    },
    trial: {
      text: '公式サイトに「体験レッスン無料」「まずは無料体験へお越しください」との案内があります',
      url: 'https://www.stepgolf.co.jp/',
    },
    company: null,
    storeList: 'https://www.stepgolf.co.jp/store/',
    checked: '2026-11-12',
    // 2026-11-12 公式の料金ページ（/system）の入会初期費用。プラン別の料金のしくみは page-official-tables の brand/stepgolf
    feeNote: '別途 入会初期費用 税込43,780円（体験後7日以内の入会は32,780円）。',
  },
  mygol: {
    alt: 'MYGOL',
    officialCount: {
      text: '公式サイトのお知らせ（2026年10月15日）では「浅草1号店オープンから4年で80店舗」と案内されています',
      url: 'https://www.mygol.jp/news/20261015/',
    },
    trial: {
      text: '公式サイトに無料体験の案内（「まずはお気軽に無料体験からご予約いただき」）があります',
      url: 'https://www.mygol.jp/',
    },
    company: null,
    storeList: 'https://www.mygol.jp/shop/',
    checked: '2026-11-02',
    // 2026-11-25 「マイゴル」16@13.2・「マイゴル 店舗」15@6.7・「店舗数は？」。公式の店舗一覧（/shop/）を数え、
    // 営業中のマイゴル・マイゴルフレーン72店の店舗トップ・料金ページとマイゴルフレンジ12店のページを 11/25 に取得して集計
    titleWord: '料金・',
    feeNote: '別途 入会金 税込11,000円・登録料 税込5,500円（多くの店舗。キャンペーンで無料の店舗あり）。',
    answer: {
      heading: 'マイゴル（MYGOL）の答え（店舗数・月会費・入会金・体験・24時間）',
      checked: '2026-11-25',
      feeMin: 4400,
      feeMax: 69300,
      sources: [
        { label: '公式の店舗一覧', url: 'https://www.mygol.jp/shop/' },
        { label: '料金ページの例（八戸店）', url: 'https://www.mygol.jp/shop/hachinohe/price/' },
        { label: '金沢竪町通り店の料金', url: 'https://www.mygol.jp/shop/kanazawatatemachi/price/' },
        { label: 'マイゴルフレンジ赤坂1st店', url: 'https://www.mygol.jp/range/shop/akasaka1.php' },
        { label: '無料体験のご利用方法', url: 'https://www.mygol.jp/freetrial' },
        { label: 'よくある質問', url: 'https://www.mygol.jp/faq/' },
      ],
      rows: [
        { k: '店舗数', v: '公式の店舗一覧に92店（マイゴル・マイゴルフレーン80店＋マイゴルフレンジ12店）。うち7店は開業準備中（越谷せんげん台駅東口・竹ノ塚・横浜藤が丘・ヨークタウン仙台小松島・大宮日進・池尻大橋の各店が2026年12月、長岡駅前店が1月23日の予定）で、営業中は85店。当サイトの掲載は営業中84店です（11月21日オープンのららぽーと横浜店は未掲載）' },
        { k: '月会費（税込）', v: '4,400円〜69,300円。最も低いのは金沢竪町通り店の朝活プラン（4:00〜10:00）4,400円、最も高いのはマイゴルフレンジの法人プラン 69,300円。24時間使えるプランの例は八戸店のリミテッドプラン 13,200円。公式に「店舗によって月額は変わります」とあります' },
        { k: '入会金・登録料', v: '料金ページを確認した79店のうち78店が入会金10,000円・登録料5,000円（店舗トップの表記は「入会金 税抜10,000円（税込11,000円）」「登録料 税抜5,000円（税込5,500円）」）。川口店は入会金20,000円・登録料10,000円' },
        { k: '入会キャンペーン', v: '営業中のマイゴル・マイゴルフレーン72店のうち38店の店舗トップに「入会金・登録料無料」などのキャンペーン表示（2026年11月25日時点・条件は店舗ごと）' },
        { k: '体験', v: '無料体験あり（店舗ページの「体験予約」から予約）。クラブは無料レンタル、シューズ・グローブの貸し出しは店舗により異なる。当日の体験予約は空きがあれば可（コールセンター 0120-150-562）' },
        { k: '24時間営業か', v: '営業中のマイゴル・マイゴルフレーン72店のうち67店の店舗ページが「24時間営業」。八千代台駅前店・柿生駅前店は5時〜25時、川口店は7時〜24時、ブランチ茅ヶ崎店は7時〜22時、ららぽーと横浜店は8時〜23時。マイゴルフレンジ12店は「24時間年中無休」' },
        { k: '他店の利用・支払い', v: '月額プランによって利用できる店舗が変わる（都度払いのチケットもあり）。支払いはクレジットカード（マイゴルアプリで入会手続き）' },
      ],
    },
  },
  doortogolf: {
    alt: 'ドアトゥゴルフ',
    officialCount: null,
    trial: {
      text: '公式サイトに「¥0 体験予約」の案内があり、「新規入会で初回60分のレッスン体験が3,000円（対象店舗がございます）」とされています',
      url: 'https://doortogolf.com/',
    },
    company: {
      text: '運営会社は株式会社イースリー（本社所在地 東京都渋谷区桜丘町3-2 渋谷サクラステージ SAKURAタワー7階）です',
      url: 'https://doortogolf.com/company',
    },
    storeList: 'https://doortogolf.com/shop/',
    // 2026-11-23 体験（公式トップ）・運営会社（/company）を再確認。「door to golf 料金」15@8.5 → title に「料金・」
    checked: '2026-11-23',
    titleWord: '料金・',
  },
  // 2026-11-04 掲載の monthly_fee は各店のレッスン会員・全日だけなので、下限は全60店の公式の料金表（店舗ページ・/price/）を読んだ値を持つ
  zengolf: {
    alt: 'ゼンゴルフ／ZENGOLF',
    officialCount: {
      text: '公式サイトのトップページでは ZENGOLF RANGE を「首都圏60店舗以上」、ZENGOLF ACADEMY を「首都圏7店舗」と案内しています。公式の店舗一覧には RANGE 54店（12月1日開業予定の新百合ヶ丘店を含む）・ACADEMY 7店・ZENGOLF LOUNGE 1店（六本木）が載っています',
      url: 'https://zengolf.jp/',
    },
    trial: {
      text: '公式の店舗ページに「2026年11月のお得なキャンペーン」として「体験レッスン 3,300円⇒0円」との案内があります',
      url: 'https://zengolf.jp/ageo/',
    },
    company: {
      text: '販売業者はツリーベル株式会社（本社所在地 東京都目黒区三田1丁目4-2 恵比寿ガーデンテラス壱番館2階）です',
      url: 'https://zengolf.jp/legal-notice/',
    },
    storeList: 'https://zengolf.jp/location/',
    // 2026-11-14 店舗数（トップ）・体験（上尾店）・販売業者（特商法表記）を再確認
    checked: '2026-11-14',
    feeFixed: {
      min: 8580, minSlug: 'zengolf-chibachuo', minName: 'ZEN GOLF RANGE 千葉中央店', minPlan: 'レンジ会員 ナイト（24:00〜翌6:55）',
      max: 22000, maxSlug: 'zengolf-ebisu', maxName: 'ZEN GOLF RANGE 恵比寿店', n: 60,
    },
    feeNote: '多くの店舗で、月会費とは別に打席料（55分 税込550円）がかかります。',
    noStoreJump: true,
    // 2026-11-26 「ゼンゴルフ」20@11.3・「zengolf 店舗」7@9.7（GSC 11/10〜11/23）。h1 直下に会員種別ごとの料金・入会費・体験・24時間・店舗数の早見表。
    // 公式トップ・店舗一覧と、掲載60店の店舗ページ（料金表・キャンペーン・営業時間）を 11/26 に取得して集計。
    // feeMin/feeMax は入れない（title・lead は feeFixed のまま＝title を変えない）
    answer: {
      heading: 'ZEN GOLF RANGE（ゼンゴルフ／ZENGOLF）の答え（会員種別ごとの月会費・入会費・体験・24時間・店舗数）',
      checked: '2026-11-26',
      sources: [
        { label: '公式トップ', url: 'https://zengolf.jp/' },
        { label: '公式の店舗一覧', url: 'https://zengolf.jp/location/' },
        { label: '料金表の例（上尾店）', url: 'https://zengolf.jp/ageo/' },
        { label: '料金表の例（千葉中央店）', url: 'https://zengolf.jp/chibachuo/' },
        { label: '料金表の例（恵比寿店）', url: 'https://zengolf.jp/ebisu/' },
      ],
      rows: [
        { k: '会員種別', v: 'レッスン会員（専属プロのレッスンが受け放題）とレンジ会員（レッスンなし・シミュレーターが使い放題）。それぞれに全日・デイ（平日の日中）・ナイトなどの区分があり、設定のある区分は店舗により異なります' },
        { k: 'レッスン会員の月会費（税込）', v: '全日 14,080円〜22,000円／デイ 15,400円〜18,700円（デイの設定がある店舗のみ）' },
        { k: 'レンジ会員の月会費（税込）', v: '全日 10,780円〜16,500円／デイ・ナイト 8,580円〜13,200円（設定のある店舗のみ。8,580円は千葉中央店・新子安店のナイト 24:00〜翌6:55 など）' },
        { k: '入会費', v: '税込22,000円（掲載60店の料金表すべてで同額）。2026年11月のキャンペーンでは、体験レッスン後に当日入会すると、43店で入会金100%OFF（0円）、17店（恵比寿・川崎・御徒町・赤羽・用賀ほか）で50%OFF（11,000円）です。割引率は各店舗ページでご確認ください' },
        { k: '打席料', v: '55分 税込550円（55店の料金表に記載。永福町・富士見台・春日・仙川・下井草の5店は料金表に打席料の行がありません）' },
        { k: '体験', v: '体験レッスンは通常3,300円。2026年11月のキャンペーンでは、掲載60店すべての店舗ページに「体験レッスン 3,300円⇒0円」とあります。体験の予約は公式サイトから24時間受付' },
        { k: '24時間営業か', v: '掲載60店のうち28店の店舗ページが「24時間営業」。そのほかの店舗は7:00〜23:00、10:05〜21:00など店舗ごとに異なります。「24プラス」等のオプション（月 税込3,080円〜4,400円）で、24時間営業の店舗の深夜・早朝枠を相互利用できると料金表に記載があります' },
        { k: '店舗数', v: '公式トップでは ZENGOLF RANGE を「首都圏60店舗以上」と案内。公式の店舗一覧は RANGE 54店（12月1日開業予定の新百合ヶ丘店を含む）・ACADEMY 7店・LOUNGE 1店（六本木）。当サイトの掲載は営業中の60店です（新百合ヶ丘店・LOUNGE 六本木店は未掲載）' },
        { k: '他店の利用', v: '公式に「全てのブランドで店舗相互利用が可能」とあり、所属店舗以外の店舗でもレッスンを受講できます' },
      ],
    },
  },
  // 2026-11-20 「ラハゴルフ24」63@6.1・「ラハゴルフ」23@7.4 がブランドページに着地。公式の店舗一覧・店舗ページ・よくある質問・特商法表記を 11/20 に確認。
  // 月会費は税込表記のある店舗（15店）の範囲。税抜表記のみの5店（茅ヶ崎南口・岡崎上里・草加・浦和・福知山）と、
  // 「12月より会費￥9,900円（税込）」の藤沢遠藤店は範囲に含めず、page-official-tables の brand/lahagolf24 に別記。
  // 店舗ページ冒頭のブランド導線は出さない（未クロールの店舗頁を動かさない）
  lahagolf24: {
    alt: 'LAHAGOLF24',
    officialCount: {
      text: '公式サイトの店舗一覧には21店舗が載っています。鶴間店（神奈川県大和市）は、公式のお知らせ（2026年10月2日）で「2026年10月31日（土）をもって営業を終了」と案内されています（当サイトの掲載件数には鶴間店が含まれています）',
      url: 'https://laha-golf24.com/news/3980/',
    },
    trial: {
      text: '公式サイトに「見学・体験予約」の案内があり、よくある質問では、グランドオープン後の店舗は「見学・体験予約」ボタンから申し込めること（会員登録が必要）とされています。体験の料金は公式サイトに記載がありません',
      url: 'https://laha-golf24.com/faq/',
    },
    company: {
      text: '販売事業者は株式会社LAHAGOLF（本社所在地 神奈川県川崎市中原区小杉町3-441 2F）です。公式のお知らせ（2026年7月7日）によると、会社分割により株式会社原トラストから事業を承継しています',
      url: 'https://laha-golf24.com/law/',
    },
    storeList: 'https://laha-golf24.com/list/',
    checked: '2026-11-20',
    feeFixed: {
      min: 10890, minSlug: 'lahagolf24-kawasaki-minamisaiwaicho', minName: 'ラハゴルフ24 川崎南幸町店', minPlan: '月会費 9,900円（税込10,890円）',
      max: 17930, maxSlug: 'lahagolf24-funabashi-natsumidai', maxName: 'ラハゴルフ24 船橋夏見台店', n: 15,
    },
    feeNote: '別途 入会金 税込11,000円・セキュリティ管理料 税込3,300円（年1回）。',
    noStoreJump: true,
    countNoteOff: true,
  },
  // 2026-11-27（16時遅れ挽回）「サンクチュアリゴルフ」31@23.4・「サンクチュアリゴルフ 店舗」5@7.6 で店舗頁（大宮）が上に出る。
  // 公式の /schools・/fees（料金表画像）・/trial・/company と range の料金表画像（千葉中央・渋谷・大宮）を 11/27 に確認。
  // collect_sanctuarygolf.py を /tmp で実行し、料金表画像は 10/16 と同じファイル（月会費の掲載値は変わっていない）ことを確認。
  // 店舗ページは動かさない（noStoreJump）。feeNote・feeFixed は /guide・/lesson にも出るので使わない
  sanctuarygolf: {
    alt: 'SANCTUARY GOLF',
    officialCount: {
      text: '公式サイトの店舗一覧には24店舗が載っており、うち銀座新橋店は「閉店いたしました」と案内されています（営業中は23店舗で、当サイトの掲載と同じです）',
      url: 'https://www.sanctuarygolf.jp/schools/',
    },
    trial: {
      text: '公式サイトの初回体験レッスンのページに、インストラクターとのマンツーマン式レッスンを50分受けられ、体験レッスン代は2,000円（料金表では税込2,200円）とあります',
      url: 'https://www.sanctuarygolf.jp/trial/',
    },
    company: {
      text: '運営会社は株式会社サンクチュアリゴルフ（本社 東京都港区六本木7-4-4 六本木アートシェル6階・7階）です',
      url: 'https://www.sanctuarygolf.jp/company/',
    },
    storeList: 'https://www.sanctuarygolf.jp/schools/',
    checked: '2026-11-27',
    titleWord: '料金・',
    noStoreJump: true,
    countNoteOff: true,
    description:
      'サンクチュアリゴルフ（SANCTUARY GOLF）の料金：月会費は税込7,590円〜29,590円（レンジ会員〜フルタイム会員・店舗と男女で異なる）、入会金 税込11,000円（大宮店は22,000円）、体験レッスン50分 税込2,200円。全23店舗の料金を公式どおりに掲載。',
    answer: {
      heading: 'サンクチュアリゴルフ（SANCTUARY GOLF）の答え（会員種別ごとの月会費・入会金・体験・営業時間・店舗数）',
      checked: '2026-11-27',
      sources: [
        { label: '公式の店舗一覧', url: 'https://www.sanctuarygolf.jp/schools/' },
        { label: '料金について', url: 'https://www.sanctuarygolf.jp/fees/' },
        { label: 'レンジ＆スクール店の料金表', url: 'https://range.sanctuarygolf.jp/fees/' },
        { label: '初回体験レッスン', url: 'https://www.sanctuarygolf.jp/trial/' },
        { label: '公式トップ', url: 'https://www.sanctuarygolf.jp/' },
      ],
      rows: [
        { k: '会員種別', v: 'フルタイム会員（店休日以外すべて）・デイタイム会員（平日のみ9:00〜17:00）と、練習だけのレンジ会員（デイレンジ・ナイトレンジなど。設定のない店舗もあります）。池袋駅前・六本木・銀座有楽町・新宿・渋谷青山・千葉中央など11店舗は男性と女性で料金が異なります' },
        { k: 'フルタイム会員（税込）', v: '15,290円〜29,590円。最も低いのは千葉中央店（女性）・つくば店、最も高いのは渋谷青山店（男性）' },
        { k: 'デイタイム会員（税込）', v: '10,890円〜25,190円。最も低いのは千葉中央店（女性）・つくば店、最も高いのは渋谷青山店（男性）' },
        { k: 'レンジ会員（税込）', v: '7,590円〜13,090円。最も低いのは千葉中央店のナイトレンジ会員、最も高いのは戸越銀座店・立川店のレンジ会員' },
        { k: '入会金', v: '10,000円（税込11,000円）。大宮店は20,000円（税込22,000円）' },
        { k: 'キャンペーン', v: '公式トップに「全店舗にて初月0円・入会金半額キャンペーン実施中！」とあります（料金ページの例：入会金 税込11,000円→5,500円、各会員の初月0円）。期間の記載はありません' },
        { k: '体験', v: 'インストラクターとのマンツーマン50分で、体験レッスン代2,000円（税込2,200円）。レッスンに必要なものはすべてレンタルできます' },
        { k: '営業時間', v: '公式の料金ページに「7：00-24：00（最大）」。当サイト掲載23店舗のうち16店舗の店舗ページが24時間営業（レンジの無人営業時間を含む）で、レッスンの時間は店舗ごとに異なります' },
        { k: '店舗数', v: '公式の店舗一覧に24店舗（銀座新橋店は閉店）。営業中の23店舗を当サイトに掲載しています' },
      ],
    },
  },
  // 2026-11-27（16時遅れ挽回）「チキンゴルフ」2@78.0・「チキンゴルフ 店舗一覧」1@11.0 で店舗頁（心斎橋）が上に出る。
  // 公式の /price/ は「入会金 35,000 円 ＋ お好きなプラン料金」でプランの金額なし（11/3 から）→ 月会費の範囲は出さず titleTail で答える
  chickengolf: {
    alt: 'Chicken Golf',
    officialCount: {
      text: '公式サイトの店舗一覧には27店舗が載っています。当サイトの掲載29件のうち岡山店・豊橋店は公式の一覧に無く、店舗ページのURLは公式の店舗一覧へ転送されます（2026年11月27日確認）',
      url: 'https://chicken-golf.com/schools/',
    },
    trial: {
      text: '公式サイトの料金ページに「無料カウンセリング」の案内があり、希望者は＋3,000円でお試しレッスンを受けられるとされています',
      url: 'https://chicken-golf.com/price/',
    },
    company: {
      text: '運営会社は株式会社Belle Vie（本社所在地 東京都渋谷区恵比寿4-20-3 恵比寿ガーデンプレイスタワー24階）です',
      url: 'https://chicken-golf.com/company/',
    },
    storeList: 'https://chicken-golf.com/schools/',
    checked: '2026-11-27',
    titleWord: '料金・',
    titleTail: '入会金35,000円＋プラン料金・無料カウンセリング',
    noStoreJump: true,
    countNoteOff: true,
    description:
      'チキンゴルフ（Chicken Golf）の料金：公式の料金ページは入会金35,000円＋プラン料金（無制限通い放題・デイタイム通い放題・回数プラン）で、プランの金額は掲載なし。無料カウンセリングあり、お試しレッスンは＋3,000円。全店舗の営業時間・アクセスを掲載。',
    answer: {
      heading: 'チキンゴルフ（Chicken Golf）の答え（料金のしくみ・プラン・体験・営業時間・店舗数）',
      checked: '2026-11-27',
      sources: [
        { label: '公式のプラン・料金', url: 'https://chicken-golf.com/price/' },
        { label: '公式の店舗一覧', url: 'https://chicken-golf.com/schools/' },
        { label: 'よくあるご質問', url: 'https://chicken-golf.com/faq/' },
        { label: '心斎橋店', url: 'https://chicken-golf.com/schools/osaka-shinsaibashi/' },
      ],
      rows: [
        { k: '料金のしくみ', v: '「入会金 35,000円 ＋ お好きなプラン料金」（公式の料金ページ。税込・税抜の別は記載なし）' },
        { k: 'プラン', v: '無制限通い放題（オールタイム）・デイタイム通い放題（平日9:00〜17:00）・回数プランの3つ。いずれもセミパーソナルレッスン50分で、1日最大1枠。通い放題の期間は2ヵ月から' },
        { k: '月会費・プランの金額', v: '公式の料金ページ・店舗ページに金額の記載はありません（全店共通の料金表は公開されていません）。料金ページには「最適な期間のご提案をさせて頂きます」とあり、金額は無料カウンセリングまたは店舗で確認する形です' },
        { k: '体験', v: '無料カウンセリング（カウンセリングのみも可）。希望者は＋3,000円でお試しレッスン。予約は公式LINEから' },
        { k: 'レンタル', v: 'ウェア・グローブ・シューズ・靴下・ゴルフクラブのレンタル無料（各プランの案内）。手ぶらで通えます' },
        { k: '営業時間', v: 'よくあるご質問に「営業時間は7:00-23:00、お休みは年末年始のみ」。心斎橋店の店舗ページは全日7:00〜23:00・定休日 年末年始（12/30〜1/3）' },
        { k: '対象年齢', v: '満16歳以上（満18歳未満は入会時に保護者の同意が必要）' },
        { k: '店舗数', v: '公式の店舗一覧に27店舗（北海道・東北2、東京6、関東6、中部2、関西9、九州・沖縄2）。当サイトの掲載は29件で、うち岡山店・豊橋店は公式の一覧に無く、店舗ページは店舗一覧へ転送されます' },
      ],
    },
  },
  // 2026-11-27（16時遅れ挽回）「インザゴルフ」16@14.0・「インザゴルフ 料金」1@7.0 で店舗頁（LITE筑後ほか）が上に出る。
  // 公式トップ・/price/・掲載23店の店舗ページを 11/27 に取得し、掲載の月会費は23店すべて公式と一致（訂正なし）
  inthegolf: {
    alt: 'inthegolf',
    officialCount: {
      text: '公式サイトのトップページでは、福岡県13・佐賀県2・長崎県1・大分県2・熊本県2・宮崎県2・鹿児島県1の計23店舗を掲載し、「掲載数には開業前の店舗を含みます」としています（2026年12月1日オープン予定のLITE筑後店を含む）',
      url: 'https://inthegolf.com/',
    },
    trial: {
      text: '公式サイトに無料体験（所要30分・クラブ無料レンタル）の案内があります',
      url: 'https://inthegolf.com/',
    },
    company: {
      text: '運営会社は株式会社イン・ザ・コム（INTHECOM inc.・所在地 佐賀県佐賀市卸本町4-1）です',
      url: 'https://inthegolf.com/company/',
    },
    storeList: 'https://inthegolf.com/list/',
    checked: '2026-11-27',
    titleWord: '料金・',
    noStoreJump: true,
    countNoteOff: true,
    description:
      'インザゴルフ（inthegolf）の料金：レッスン店舗の月会費は税込13,178円〜（平日デイ）・全日17,578円〜・VIP38,478円、LITE店舗は税込4,378円〜15,378円。入会金は通常 税込43,780円（キャンペーン10,000円）。無料体験30分。九州の店舗を掲載。',
    answer: {
      heading: 'インザゴルフ（inthegolf）の答え（会員種別ごとの月会費・入会金・体験・利用時間・店舗数）',
      checked: '2026-11-27',
      sources: [
        { label: '公式トップ', url: 'https://inthegolf.com/' },
        { label: '公式の料金', url: 'https://inthegolf.com/price/' },
        { label: '小倉店の料金', url: 'https://inthegolf.com/list/kokura/' },
        { label: 'LITE小郡店の料金', url: 'https://inthegolf.com/list/lite-ogori/' },
        { label: '公式の店舗一覧', url: 'https://inthegolf.com/list/' },
      ],
      rows: [
        { k: '店舗の種類', v: 'レッスン店舗（20店。レッスン料・ボール代・自主練習料が月額に含まれ、打席料なし）と、自主練習中心のLITE店舗（3店：久留米小森野・小郡・筑後〔2026年12月1日オープン予定〕。通い放題3プランにレッスン店舗で使えるグループレッスン月2回分つき）' },
        { k: 'レッスン店舗の月会費（税込）', v: '平日デイ会員 13,178円〜15,378円／全日会員 17,578円〜19,778円／土日祝会員 15,378円〜17,578円／VIP会員 38,478円（長崎スタジアムシティ店は32,780円）。高い方の料金は北九州本城・西鉄久留米・大野城桜並木の各店' },
        { k: 'LITE店舗の月会費（税込）', v: 'LITE平日デイ 10,978円／LITE全日（24時間365日）15,378円／LITE土日祝 13,178円／LITE月1 4,378円／LITE月2 7,678円（3店とも同じ）' },
        { k: '入会金', v: 'レッスン店舗20店の店舗ページで「通常 39,800円（税抜）／43,780円（税込）」「キャンペーン 10,000円（税込）」。LITEの久留米小森野店・小郡店は「入会金 22,000円 → 0円 さらに 初月会費無料」。入会時は入会金・初月の日割り料金・翌月会費を支払います（適用条件・期間は無料体験時に確認）' },
        { k: '体験', v: '無料体験30分（店舗の雰囲気・設備・コーチとの相性を確認）。クラブ無料レンタル。ゴルフをしやすい服装・靴で来店。契約時はクレジットカードかキャッシュカードが必要' },
        { k: '利用時間', v: '公式トップの基本料金の説明では、全日会員は24時間・全時間帯、平日デイ会員は平日8:00〜17:00、土日祝会員は土・日・祝8:00〜21:00（店舗により異なります）' },
        { k: '店舗数', v: '公式トップの掲載は九州7県の23店舗（開業前の店舗を含む）。当サイトは営業中の22店舗と、開業準備中のLITE筑後店を掲載しています' },
      ],
    },
  },
}

/** ブランドの表示名に別表記を併記（「ステップゴルフ（STEP GOLF）」） */
export function brandLabel(slug: string, name: string): string {
  const f = BRAND_FACTS[slug]
  return f ? `${name}（${f.alt}）` : name
}

/**
 * 月会費（税込）の最小・最大を、掲載データ（公式の店舗ページの表記）から取る。
 * ⚠️ 表記の形がブランドで違うので、確実に読めるブランドだけ（BRAND_FACTS にあるもの）。
 *    「別途 登録料・入会金」は月会費ではないので除く。税込の表記が無い店は数えない。
 */
export function feeRange(
  slug: string,
  fs: { slug: string; name: string; monthly_fee: string | null }[],
): { min: number; minName: string; minSlug: string; minPlan: string; max: number; maxName: string; maxSlug: string; n: number } | null {
  if (!BRAND_FACTS[slug]) return null
  if (BRAND_FACTS[slug].feeFixed) return BRAND_FACTS[slug].feeFixed as NonNullable<ReturnType<typeof feeRange>>
  let min = Infinity, max = -Infinity, minName = '', maxName = '', minSlug = '', maxSlug = '', minPlan = '', n = 0
  for (const f of fs) {
    if (!f.monthly_fee) continue
    let vals: number[] = []
    if (slug === 'sanctuarygolf') {
      // 2026-11-27 「（入会金…別途）」の入会金と、つくば店のフィットネス会員（ゴルフの会員ではない）は月会費の範囲に入れない
      const s = f.monthly_fee.split('（入会金')[0].split('／').filter((x) => !x.startsWith('フィットネス')).join('／')
      vals = [...s.matchAll(/税込\s*([\d,]+)円/g)].map((m) => Number(m[1].replace(/,/g, '')))
    } else if (slug === 'mygol') {
      const s = f.monthly_fee.split('別途')[0]
      if (!/税込/.test(s)) continue
      vals = [...s.matchAll(/([\d,]{4,})円/g)].map((m) => Number(m[1].replace(/,/g, '')))
    } else {
      vals = [...f.monthly_fee.matchAll(/税込\s*([\d,]+)円/g)].map((m) => Number(m[1].replace(/,/g, '')))
    }
    if (!vals.length) continue
    n++
    for (const v of vals) {
      if (v < min) {
        min = v; minName = f.name; minSlug = f.slug
        // その金額が書かれているプランの一節（「ナイト（４）会員（4回枠/月） 月額…」）。条件つきの安いプランを隠さない
        const num = v.toLocaleString('ja-JP')
        minPlan = (f.monthly_fee.split('別途')[0].split('／').find((x) => x.includes(num)) ?? '').replace(/（「A→B」.*$/, '').replace(/（入会金.*$/, '').replace(/^・/, '').trim()
      }
      if (v > max) { max = v; maxName = f.name; maxSlug = f.slug }
    }
  }
  return n ? { min, minName, minSlug, minPlan, max, maxName, maxSlug, n } : null
}

export const yen = (v: number) => `${v.toLocaleString('ja-JP')}円`
