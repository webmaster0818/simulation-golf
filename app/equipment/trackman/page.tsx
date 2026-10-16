import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, OPEN_FACILITIES, PREF_SLUG,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'
import { JsonLd, breadcrumb, itemListLd } from '../../../lib/seo'

// ⚠️ 判定は equipment の文字列にトラックマンが含まれるかで見る。
//    表記ゆれ（トラックマン4 / TRACKMAN RANGE / トラックマンレンジ）があるため完全一致にしない。
const isTrackman = (s: string | null) =>
  !!s && /トラックマン|TRACKMAN|TrackMan/i.test(s)
const trackman = () => OPEN_FACILITIES.filter((f) => isTrackman(f.equipment))

export const metadata: Metadata = {
  title: `トラックマン導入の施設${trackman().length}件｜都道府県別に一覧`,
  description:
    'レーダーで打球を計測するトラックマンを導入している施設の一覧です。' +
    '所在地・打席数・料金を、各施設の公式サイトを出典として都道府県別に掲載しています。',
  ...pageUrlMeta(`/equipment/trackman/`),
}

export default function Trackman() {
  const fs = trackman()
  const indoor = fs.filter((f) => f.segment === 'indoor')
  const range = fs.filter((f) => f.segment === 'range')

  const groups = new Map<string, typeof fs>()
  for (const f of fs) {
    if (!f.pref) continue
    groups.set(f.pref, [...(groups.get(f.pref) ?? []), f])
  }
  const list = [...groups.entries()].sort((a, b) => b[1].length - a[1].length)

  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: '計測機器から探す', url: '/equipment/' },
      { name: 'トラックマン', url: '/equipment/trackman/' },
    ]),
    itemListLd('トラックマン導入施設', fs.map((f) => `/facility/${f.slug}/`)),
  ]

  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/equipment/">計測機器から探す</Link> / トラックマン
      </nav>

      <section className="hero">
        <div className="kicker">TrackMan</div>
        <h1>トラックマン導入の施設（{fs.length}件）</h1>
        <p className="lead">
          トラックマンは、<strong>打球をレーダーで追跡して計測する</strong>機器です。
          カメラで打ち出し直後のボールを撮影し、弾道を算出する方式とは計測の仕組みが異なります。
          屋内の個室型施設と、屋外練習場の両方に導入されています。
        </p>
      </section>

      <div className="stats">
        <div><div className="v">{fs.length}</div><div className="k">掲載施設</div></div>
        <div><div className="v">{indoor.length}</div><div className="k">屋内型</div></div>
        <div><div className="v">{range.length}</div><div className="k">練習場併設</div></div>
        <div><div className="v">{list.length}</div><div className="k">都道府県</div></div>
      </div>

      <div className="verdict">
        <span className="tag">掲載範囲について</span>
        <p style={{ marginBottom: 0 }}>
          トラックマンは、全国の導入施設一覧が公表されていません。
          本ページに掲載しているのは、<strong>当サイトが各施設の公式サイトで導入を確認できた{fs.length}件</strong>です。
          国内のすべての導入施設を網羅したものではありませんので、あらかじめご了承ください。
        </p>
      </div>

      <h2>都道府県別</h2>
      <div className="tablewrap">
        <table>
          <thead><tr><th>都道府県</th><th>施設数</th><th>うち屋内型</th></tr></thead>
          <tbody>
            {list.map(([pref, items]) => (
              <tr key={pref}>
                <td><Link href={`/area/${PREF_SLUG[pref]}/`}>{pref}</Link></td>
                <td className="num">{items.length}</td>
                <td className="num">{items.filter((f) => f.segment === 'indoor').length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {list.map(([pref, items]) => (
        <div key={pref}>
          <h2>{pref}（{items.length}件）</h2>
          <div className="cards">
            {items.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
        </div>
      ))}

      <p className="source">
        出典：各施設の公式サイト（取得日と出典URLは各施設ページに記載しています）。
        料金・営業時間・設備は変更される場合がありますので、ご利用前に公式サイトにてご確認ください。
      </p>
    </main>
  )
}
