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
}

export const ymd = (d: string) => d.replace(/^(\d+)-0?(\d+)-0?(\d+)$/, '$1年$2月$3日')
