import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, OPEN_FACILITIES, PREF_SLUG, asOf, GENERATED_AT,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'

const trace = () => OPEN_FACILITIES.filter((f) => f.equipment === 'トップトレーサー・レンジ')

export const metadata: Metadata = {
  title: `トップトレーサー導入の練習場${trace().length}施設｜無料で使える施設も一覧`,
  description:
    `打った球の軌跡が画面に出るトップトレーサー・レンジを導入している練習場の一覧です。` +
    `利用料・打席数・飛距離を都道府県別にまとめています。`,
  alternates: { canonical: `${SITE.origin}/equipment/toptracer/` },
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

  return (
    <main className="wrap">
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/equipment/">機材から探す</Link> / トップトレーサー
      </nav>

      <section className="hero">
        <div className="kicker">Toptracer Range</div>
        <h1>トップトレーサー導入の練習場（{fs.length}施設）</h1>
        <p className="lead">
          打った球の軌跡が、そのまま画面に線で表示される設備です。
          屋内のシミュレーションゴルフと違い、<strong>実際に飛んだ球を追いかけて表示している</strong>点が特徴です。
        </p>
      </section>

      <div className="stats">
        <div><div className="v">{fs.length}</div><div className="k">導入施設</div></div>
        <div><div className="v">{free.length}</div><div className="k">計測が無料</div></div>
        <div><div className="v">{list.length}</div><div className="k">都道府県</div></div>
        <div><div className="v">{long.length}</div><div className="k">200ヤード以上</div></div>
      </div>

      <div className="verdict">
        <span className="tag">知っておきたいこと</span>
        <p>
          <strong>{free.length}／{fs.length}施設は、計測の利用料が「無料」と公表されています。</strong>
          ただしこれは<strong>計測機能の追加料金がかからない</strong>という意味で、
          練習場の打席料・ボール代は通常どおりかかります。
        </p>
        <p style={{ marginBottom: 0 }}>
          計測に料金がかかると公表しているのは{paid.length}件です。金額は下の表のとおりで、
          いずれも数百円以内でした。
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
        表記は出典のままです。
        {fs.filter((f) => !f.usage_fee).length > 0 && (
          <>
            {' '}なお{fs.filter((f) => !f.usage_fee).length}件は出典側に金額の記載が無いため、
            無料・有料のどちらにも数えていません。
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
        出典：GDO トップトレーサー・レンジ 練習場一覧（{asOf(GENERATED_AT)}に取得）。
        施設ごとの取得元URLは各施設ページに記載しています。
      </p>
    </main>
  )
}
