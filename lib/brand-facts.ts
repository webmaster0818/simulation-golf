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
    checked: '2026-11-02',
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
    checked: '2026-11-02',
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
