import type { Metadata } from 'next'
import Link from 'next/link'
import { SITE, brands, PREF_SLUG } from '../../lib/data'

export const metadata: Metadata = {
  title: 'ブランドから探す｜シミュレーションゴルフのチェーン一覧',
  description:
    'シミュレーションゴルフのチェーン別に、店舗数・展開エリア・公式サイトで公開されている項目を比較できます。',
  alternates: { canonical: `${SITE.origin}/brand/` },
}

export default function BrandIndex() {
  const bs = brands()
  return (
    <main className="wrap">
      <nav className="crumbs"><Link href="/">ホーム</Link> / ブランドから探す</nav>
      <section className="hero">
        <div className="kicker">Brand</div>
        <h1>ブランドから探す</h1>
        <p className="lead">
          チェーンによって、公式サイトで公開している項目が違います。
          「料金が比較できるか」「打席数が分かるか」まで含めて並べています。
        </p>
      </section>

      <h2>ブランド別の掲載状況</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>ブランド</th><th>店舗数</th><th>展開</th>
              <th>営業時間</th><th>打席</th><th>駐車場</th><th>料金</th>
            </tr>
          </thead>
          <tbody>
            {bs.map((b) => (
              <tr key={b.slug}>
                <td><Link href={`/brand/${b.slug}/`}>{b.name}</Link></td>
                <td className="num">{b.count}</td>
                <td>{b.prefs.length}都道府県</td>
                <td>{b.has.hours ? '公開あり' : '記載なし'}</td>
                <td>{b.has.bays ? '公開あり' : '記載なし'}</td>
                <td>{b.has.parking ? '公開あり' : '記載なし'}</td>
                <td>{b.has.monthlyFee ? '店舗別に公開' : '店舗ページに記載なし'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        「記載なし」は、そのブランドの公式サイトの店舗ページにその項目が載っていないという意味です。
        設備が無いという意味ではありません。
      </p>

      {bs.map((b) => (
        <div key={b.slug}>
          <h2>{b.name}</h2>
          <p>
            {b.count}店舗を掲載しています。展開エリアは{' '}
            {b.prefs.map((p, i) => (
              <span key={p}>
                {i > 0 && '・'}
                <Link href={`/area/${PREF_SLUG[p]}/`}>{p}</Link>
              </span>
            ))}
            です。
          </p>
          <p className="source"><Link href={`/brand/${b.slug}/`}>{b.name}の店舗一覧を見る</Link></p>
        </div>
      ))}
    </main>
  )
}
