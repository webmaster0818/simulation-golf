import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, OPEN_FACILITIES, PREF_SLUG, asOf, GENERATED_AT,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'
import { JsonLd, breadcrumb, itemListLd } from '../../../lib/seo'

const trace = () => OPEN_FACILITIES.filter((f) => f.equipment === 'トップトレーサー・レンジ')

export const metadata: Metadata = {
  title: `トップトレーサー導入の練習場${trace().length}施設｜計測無料の施設も掲載`,
  description:
    `打球の軌跡を画面に表示するトップトレーサー・レンジを導入している練習場の一覧です。` +
    `利用料・打席数・飛距離を都道府県別に掲載しています。`,
  ...pageUrlMeta(`/equipment/toptracer/`),
}

export default function Toptracer() {
  const fs = trace()
  const free = fs.filter((f) => f.usage_fee === '無料')
  const paid = fs.filter((f) => f.usage_fee && f.usage_fee !== '無料')
  const long = fs.filter((f) => (f.distance_yard ?? 0) >= 200)

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
      { name: 'トップトレーサー', url: '/equipment/toptracer/' },
    ]),
    itemListLd('トップトレーサー導入施設', trace().map((f) => `/facility/${f.slug}/`)),
  ]
  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/equipment/">計測機器から探す</Link> / トップトレーサー
      </nav>

      <section className="hero">
        <div className="kicker">Toptracer Range</div>
        <h1>トップトレーサー導入の練習場（{fs.length}施設）</h1>
        <p className="lead">
          トップトレーサー・レンジは、打球の軌跡を画面上に表示する設備です。
          屋内のシミュレーションゴルフとは異なり、<strong>実際に飛んだ打球を追跡して表示する</strong>点が特長です。
        </p>
      </section>

      <div className="stats">
        <div><div className="v">{fs.length}</div><div className="k">導入施設</div></div>
        <div><div className="v">{free.length}</div><div className="k">計測が無料</div></div>
        <div><div className="v">{list.length}</div><div className="k">都道府県</div></div>
        <div><div className="v">{long.length}</div><div className="k">200ヤード以上</div></div>
      </div>

      <div className="verdict">
        <span className="tag">利用料について</span>
        <p>
          <strong>{fs.length}施設のうち{free.length}施設は、計測の利用料を「無料」と公表しています。</strong>
          これは<strong>計測機能の追加料金が不要</strong>という意味であり、
          練習場の打席料・ボール代は通常どおり必要です。
        </p>
        <p style={{ marginBottom: 0 }}>
          計測の利用料を有料と公表している施設は{paid.length}件です。金額は下表のとおりで、
          いずれも数百円以内となっています。
        </p>
      </div>

      <h2>計測が有料の施設（{paid.length}件）</h2>
      <div className="tablewrap">
        <table>
          <thead><tr><th>施設</th><th>所在地</th><th>公表されている利用料</th></tr></thead>
          <tbody>
            {paid.map((f) => (
              <tr key={f.slug}>
                <td><Link href={`/facility/${f.slug}/`}>{f.name}</Link></td>
                <td>{f.pref}</td>
                <td>{f.usage_fee}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        金額は出典の表記のまま掲載しています。
        {fs.filter((f) => !f.usage_fee).length > 0 && (
          <>
            {' '}なお、{fs.filter((f) => !f.usage_fee).length}件は出典に金額の記載がないため、
            無料・有料のいずれにも含めていません。
          </>
        )}
      </p>

      <h2>都道府県別の導入数</h2>
      <div className="tablewrap">
        <table>
          <thead><tr><th>都道府県</th><th>施設数</th><th>うち計測無料</th></tr></thead>
          <tbody>
            {list.map(([pref, items]) => (
              <tr key={pref}>
                <td><Link href={`/area/${PREF_SLUG[pref]}/`}>{pref}</Link></td>
                <td className="num">{items.length}</td>
                <td className="num">{items.filter((f) => f.usage_fee === '無料').length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {list.map(([pref, items]) => (
        <div key={pref}>
          <h2>{pref}（{items.length}施設）</h2>
          <div className="cards">
            {items.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
        </div>
      ))}

      <p className="source">
        出典：GDO トップトレーサー・レンジ 練習場一覧（{asOf(GENERATED_AT)}の情報）。
        施設ごとの出典URLは各施設ページに記載しています。
      </p>
    </main>
  )
}
