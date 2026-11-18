/**
 * RIZAP GOLF（ライザップゴルフ）の公式情報（2026-11-16 kwexp で追加）。
 *
 * ⚠️ RIZAP GOLF は facilities.json（施設データベース）に入れていない。
 *    入れると19店舗の施設ページが一度にでき、エリア・ブランド・掲載件数の表示が連動して変わるため。
 *    ここではブランドの料金ページと、検索のある地域（名古屋・京都・銀座）のページだけを作る。
 *    値はすべて公式の店舗ページ（/golfschool/<id>）と料金ページ（/plan）で確認したもの。
 */
import raw from '../data/kwexp/rizapgolf.json'

export type RizapStore = {
  id: string
  name: string
  zip: string
  address: string
  hours: string
  hours_note: string | null
  parking: string | null
  stations: string[]
  area: string | null
  source_url: string
  fetched_at: string
}

export const RIZAP = raw as typeof raw & { stores: RizapStore[] }

/** 1回あたりの料金（税込・円未満切り捨て。公式の単価表示と同じ）。当サイトの計算 */
export const perLesson = (inc: number, lessons: number) => Math.floor(inc / lessons)

export const RIZAP_AREAS: Record<string, { label: string; pref: string; city: string; wards: string[]; areaLink?: { href: string; label: string } }> = {
  nagoya: { label: '名古屋', pref: '愛知県', city: '名古屋市', wards: ['名古屋市中区', '名古屋市中村区'] },
  kyoto: { label: '京都', pref: '京都府', city: '京都市', wards: ['京都市下京区', '京都市中京区'] },
  ginza: { label: '銀座', pref: '東京都', city: '中央区', wards: ['中央区'], areaLink: { href: '/area/tokyo/chuo/', label: '中央区のシミュレーションゴルフ施設をすべて見る' } },
  // 2026-11-17 kwexp（4店舗の値は公式の店舗ページで 11/17 に再確認）
  yokohama: { label: '横浜', pref: '神奈川県', city: '横浜市', wards: ['横浜市神奈川区'], areaLink: { href: '/area/kanagawa/yokohama-kanagawa/', label: '横浜市神奈川区のシミュレーションゴルフ施設をすべて見る' } },
  kawasaki: { label: '川崎', pref: '神奈川県', city: '川崎市', wards: ['川崎市川崎区'], areaLink: { href: '/area/kanagawa/', label: '神奈川県のシミュレーションゴルフ施設をすべて見る' } },
  chiba: { label: '千葉', pref: '千葉県', city: '千葉市', wards: ['千葉市中央区'], areaLink: { href: '/area/chiba/chiba-chuo/', label: '千葉市中央区のシミュレーションゴルフ施設をすべて見る' } },
  hiroshima: { label: '広島', pref: '広島県', city: '広島市', wards: ['広島市中区'], areaLink: { href: '/area/hiroshima/', label: '広島県のシミュレーションゴルフ施設をすべて見る' } },
  // 2026-11-18 kwexp（5店舗の値は公式の店舗ページで 11/18 に再確認。神戸市・大阪市・さいたま市大宮区・立川市は市区町村ページが無いので areaLink は都府県ページ）
  kobe: { label: '神戸', pref: '兵庫県', city: '神戸市', wards: ['神戸市中央区'], areaLink: { href: '/area/hyogo/', label: '兵庫県のシミュレーションゴルフ施設をすべて見る' } },
  umeda: { label: '梅田', pref: '大阪府', city: '大阪市', wards: ['大阪市北区'], areaLink: { href: '/area/osaka/', label: '大阪府のシミュレーションゴルフ施設をすべて見る' } },
  omiya: { label: '大宮', pref: '埼玉県', city: 'さいたま市', wards: ['さいたま市大宮区'], areaLink: { href: '/area/saitama/', label: '埼玉県のシミュレーションゴルフ施設をすべて見る' } },
  mita: { label: '三田', pref: '東京都', city: '港区', wards: ['港区'], areaLink: { href: '/area/tokyo/minato/', label: '港区のシミュレーションゴルフ施設をすべて見る' } },
  tachikawa: { label: '立川', pref: '東京都', city: '立川市', wards: ['立川市'], areaLink: { href: '/area/tokyo/', label: '東京都のシミュレーションゴルフ施設をすべて見る' } },
}

export const ymd = (d: string) => d.replace(/^(\d+)-0?(\d+)-0?(\d+)$/, '$1年$2月$3日')
