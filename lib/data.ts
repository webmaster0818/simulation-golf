// 施設データの読み込みと、ページから使う集計。
//
// ⚠️ このファイルに「たぶんこうだろう」を書かない。
//    data/facilities.json は各ブランドの公式サイトから取った値で、
//    載っていない項目は null のまま入っている。null は null のまま扱い、
//    ページ側で「公式サイトに記載なし」と出す。
import raw from '../data/facilities.json'

export type Facility = {
  /** indoor = 屋内シミュレーションゴルフ / range = 屋外練習場＋弾道計測 */
  segment: 'indoor' | 'range'
  brand: string | null
  brand_slug: string | null
  slug: string
  name: string
  pref: string | null
  zip: string | null
  address: string | null
  access: string | null
  tel: string | null
  hours: string | null
  open_24h: boolean | null
  closed: string | null
  /** 打席・個室の表記そのまま（「半個室3打席＋完全個室VIP1打席」等） */
  bays: string | null
  bays_num: number | null
  private_room: boolean | null
  parking: string | null
  monthly_fee: string | null
  /** 屋外練習場のトップトレーサー利用料（月会費ではない） */
  usage_fee?: string | null
  equipment: string | null
  distance_yard?: number | null
  /** false = オープン準備中。営業中の店舗と混ぜて数えない */
  open: boolean
  official: string | null
  source_url: string
  fetched_at: string
}

export const FACILITIES: Facility[] = (raw as { facilities: Facility[] }).facilities
export const GENERATED_AT: string = (raw as { generated_at: string }).generated_at

export const SITE = {
  name: 'シミュレーションゴルフ ナビ',
  // ⚠️ ドメイン確定後にここだけ差し替える。canonical・sitemap・構造化データが全てここを見る。
  origin: 'https://golf-simulate.com',
  description:
    '全国のシミュレーションゴルフ施設を、公式サイトの情報だけで比較できるサイト。個室の有無・打席数・24時間営業・駐車場・弾道計測の機材まで、出典つきで掲載しています。',
}

/** 都道府県 → URL用スラッグ。47件を固定で持つ（自動生成しない＝誤りが混ざらない） */
export const PREF_SLUG: Record<string, string> = {
  北海道: 'hokkaido', 青森県: 'aomori', 岩手県: 'iwate', 宮城県: 'miyagi',
  秋田県: 'akita', 山形県: 'yamagata', 福島県: 'fukushima', 茨城県: 'ibaraki',
  栃木県: 'tochigi', 群馬県: 'gunma', 埼玉県: 'saitama', 千葉県: 'chiba',
  東京都: 'tokyo', 神奈川県: 'kanagawa', 新潟県: 'niigata', 富山県: 'toyama',
  石川県: 'ishikawa', 福井県: 'fukui', 山梨県: 'yamanashi', 長野県: 'nagano',
  岐阜県: 'gifu', 静岡県: 'shizuoka', 愛知県: 'aichi', 三重県: 'mie',
  滋賀県: 'shiga', 京都府: 'kyoto', 大阪府: 'osaka', 兵庫県: 'hyogo',
  奈良県: 'nara', 和歌山県: 'wakayama', 鳥取県: 'tottori', 島根県: 'shimane',
  岡山県: 'okayama', 広島県: 'hiroshima', 山口県: 'yamaguchi', 徳島県: 'tokushima',
  香川県: 'kagawa', 愛媛県: 'ehime', 高知県: 'kochi', 福岡県: 'fukuoka',
  佐賀県: 'saga', 長崎県: 'nagasaki', 熊本県: 'kumamoto', 大分県: 'oita',
  宮崎県: 'miyazaki', 鹿児島県: 'kagoshima', 沖縄県: 'okinawa',
}
export const SLUG_PREF: Record<string, string> = Object.fromEntries(
  Object.entries(PREF_SLUG).map(([k, v]) => [v, k])
)

/** 地方のまとまり。TOPと都道府県一覧で使う */
export const REGIONS: { name: string; prefs: string[] }[] = [
  { name: '北海道・東北', prefs: ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県'] },
  { name: '関東', prefs: ['茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県'] },
  { name: '甲信越・北陸', prefs: ['新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県'] },
  { name: '東海', prefs: ['岐阜県', '静岡県', '愛知県', '三重県'] },
  { name: '近畿', prefs: ['滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県'] },
  { name: '中国・四国', prefs: ['鳥取県', '島根県', '岡山県', '広島県', '山口県', '徳島県', '香川県', '愛媛県', '高知県'] },
  { name: '九州・沖縄', prefs: ['福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'] },
]

export const OPEN_FACILITIES = FACILITIES.filter((f) => f.open)

export const byPref = (pref: string): Facility[] =>
  OPEN_FACILITIES.filter((f) => f.pref === pref)

export const byBrand = (brandSlug: string): Facility[] =>
  OPEN_FACILITIES.filter((f) => f.brand_slug === brandSlug)

export const bySlug = (slug: string): Facility | undefined =>
  FACILITIES.find((f) => f.slug === slug)

/** 掲載のある都道府県だけ。0件の県はページを作らない（中身のないページを増やさない） */
export const activePrefs = (): string[] =>
  Object.keys(PREF_SLUG).filter((p) => byPref(p).length > 0)

export type Brand = {
  slug: string
  name: string
  count: number
  prefs: string[]
  /** そのブランドで公式が公開している項目（ページで「何が比較できるか」を正直に出すため） */
  has: { hours: boolean; bays: boolean; parking: boolean; monthlyFee: boolean; access: boolean }
}

export const brands = (): Brand[] => {
  const map = new Map<string, Facility[]>()
  for (const f of OPEN_FACILITIES) {
    if (!f.brand_slug) continue
    const k = f.brand_slug
    map.set(k, [...(map.get(k) ?? []), f])
  }
  return [...map.entries()]
    .map(([slug, fs]) => ({
      slug,
      name: fs[0].brand as string,
      count: fs.length,
      prefs: [...new Set(fs.map((f) => f.pref).filter(Boolean) as string[])],
      has: {
        hours: fs.some((f) => f.hours),
        bays: fs.some((f) => f.bays),
        parking: fs.some((f) => f.parking),
        monthlyFee: fs.some((f) => f.monthly_fee),
        access: fs.some((f) => f.access),
      },
    }))
    .sort((a, b) => b.count - a.count)
}

/** 絞り込みの軸。実データで判定できるものだけを置く */
export const FEATURES: { slug: string; label: string; note: string; match: (f: Facility) => boolean }[] = [
  {
    slug: 'private-room',
    label: '個室で打てる',
    note: '公式サイトに個室・半個室の記載がある施設',
    match: (f) => f.private_room === true || /個室/.test(f.bays ?? ''),
  },
  {
    slug: 'open-24h',
    label: '24時間営業',
    note: '公式サイトが24時間営業と明記している施設',
    match: (f) => f.open_24h === true,
  },
  {
    slug: 'parking',
    label: '駐車場あり',
    note: '公式サイトに駐車場の記載がある施設（「近隣にコインパーキング」は含めない）',
    match: (f) => !!f.parking && !/^無|なし/.test(f.parking) && !/近隣|近く/.test(f.parking),
  },
  {
    slug: 'free-trace',
    label: '弾道計測が無料で使える',
    note: 'トップトレーサー・レンジの利用料が無料と公表されている練習場',
    match: (f) => f.segment === 'range' && f.usage_fee === '無料',
  },
]

export const byFeature = (slug: string): Facility[] => {
  const ft = FEATURES.find((x) => x.slug === slug)
  return ft ? OPEN_FACILITIES.filter(ft.match) : []
}

/** 住所から市区町村を切り出す。エリアページの見出しに使う */
export const cityOf = (f: Facility): string | null => {
  if (!f.address || !f.pref) return null
  const rest = f.address.replace(f.pref, '')
  const m = rest.match(/^(.+?[市区町村])/)
  return m ? m[1] : null
}

/** 「2026年9月12日時点」のような表記を1か所で作る */
export const asOf = (d: string): string => {
  const [y, m, day] = d.split('-')
  return `${y}年${Number(m)}月${Number(day)}日時点`
}
