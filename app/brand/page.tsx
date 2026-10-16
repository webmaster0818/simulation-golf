import { pageUrlMeta } from '../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import BrandShot from '../../components/BrandShot'
import { SITE, brands, PREF_SLUG } from '../../lib/data'
import { JsonLd, breadcrumb, itemListLd } from '../../lib/seo'

export const metadata: Metadata = {
  title: 'ブランドから探す｜シミュレーションゴルフのチェーン一覧',
  description:
    'シミュレーションゴルフのブランド別に、店舗数・展開エリア・公式サイトで公開されている項目を比較できます。',
  ...pageUrlMeta(`/brand/`),
}

export default function BrandIndex() {
  const bs = brands()
  const ld = [
    breadcrumb([{ name: 'ホーム', url: '/' }, { name: 'ブランドから探す', url: '/brand/' }]),
    itemListLd('ブランドから探す', bs.map((b) => `/brand/${b.slug}/`)),
  ]
  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs"><Link href="/">ホーム</Link> / ブランドから探す</nav>
      <section className="hero">
        <div className="kicker">Brand</div>
        <h1>ブランドから探す</h1>
        <p className="lead">
          公式サイトで公開されている情報は、ブランドにより異なります。
          料金や打席数の公開状況も含めて、ブランドごとに掲載しています。
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
                <td><Link href={`/brand/${b.slug}/`} className="g-brand-cell"><BrandShot slug={b.slug} name={b.name} compact />{b.name}</Link></td>
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
        画像は、各ブランドの公式サイトのトップページを当サイトが撮影したものです（撮影日は各画像に記載しています）。
        「記載なし」は、該当ブランドの公式サイトの店舗ページに記載がないことを示しており、設備がないことを示すものではありません。
      </p>

      {bs.map((b) => (
        <div key={b.slug} className="g-brand-block">
          <h2>{b.name}</h2>
          <div className="g-brand-block-shot"><BrandShot slug={b.slug} name={b.name} /></div>
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
