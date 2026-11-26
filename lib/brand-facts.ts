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
    if (slug === 'mygol') {
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
        minPlan = (f.monthly_fee.split('別途')[0].split('／').find((x) => x.includes(num)) ?? '').replace(/（「A→B」.*$/, '').replace(/^・/, '').trim()
      }
      if (v > max) { max = v; maxName = f.name; maxSlug = f.slug }
    }
  }
  return n ? { min, minName, minSlug, minPlan, max, maxName, maxSlug, n } : null
}

export const yen = (v: number) => `${v.toLocaleString('ja-JP')}円`
