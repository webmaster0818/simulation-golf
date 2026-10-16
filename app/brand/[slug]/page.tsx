import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import BrandShot from '../../../components/BrandShot'
import {
  SITE, PREF_SLUG, brands, byBrand, cityOf, asOf, GENERATED_AT,
  FACILITIES,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'
import { JsonLd, breadcrumb, itemListLd } from '../../../lib/seo'

type Params = { slug: string }

export function generateStaticParams(): Params[] {
  return brands().map((b) => ({ slug: b.slug }))
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params
  const b = brands().find((x) => x.slug === slug)
  if (!b) return {}
  return {
    title: `${b.name}の店舗一覧${b.count}件｜料金・営業時間・個室の有無`,
    description:
      `${b.name}の店舗${b.count}件を、公式サイトの情報をもとに掲載しています。` +
      `${b.prefs.length}都道府県に展開。${b.has.monthlyFee ? '店舗ごとの月会費も掲載しています。' : '店舗ごとの料金は公式サイトに記載がないため掲載していません。'}`,
    ...pageUrlMeta(`/brand/${slug}/`),
  }
}

/** 月会費の税込・税抜の表記が店舗によって違うか（全店同じ表記のブランドでは注意書きを出さない） */
function taxMixed(fs: { monthly_fee: string | null }[]): boolean {
  const kinds = new Set(
    fs.filter((f) => f.monthly_fee).map((f) => {
      const v = f.monthly_fee as string
      const inc = /税込/.test(v), exc = /税抜|税別/.test(v)
      return inc && exc ? 'both' : inc ? 'inc' : exc ? 'exc' : 'none'
    }),
  )
  return kinds.size > 1 || kinds.has('both')
}

export default async function BrandPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params
  const b = brands().find((x) => x.slug === slug)
  if (!b) return null
  const fs = byBrand(slug)
  // 営業前の店舗もページは存在するので、ブランド側からも繋いでおく（営業中とは分ける）
  const soon = FACILITIES.filter((f) => !f.open && f.brand_slug === slug)
  const n24 = fs.filter((f) => f.open_24h).length
  const nPrivate = fs.filter((f) => f.private_room === true || /個室/.test(f.bays ?? '')).length

  const byPrefMap = new Map<string, typeof fs>()
  for (const f of fs) {
    if (!f.pref) continue
    byPrefMap.set(f.pref, [...(byPrefMap.get(f.pref) ?? []), f])
  }
  const groups = [...byPrefMap.entries()].sort((a, b2) => b2[1].length - a[1].length)

  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'ブランドから探す', url: '/brand/' },
      { name: b.name, url: `/brand/${slug}/` },
    ]),
    itemListLd(`${b.name}の店舗一覧`, fs.map((f) => `/facility/${f.slug}/`)),
  ]
  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/brand/">ブランドから探す</Link> / {b.name}
      </nav>

      <section className="hero">
        <div className="kicker">{slug}</div>
        <h1>{b.name}の店舗一覧（{b.count}件）</h1>
        <p className="lead">
          公式サイトに掲載されている{b.name}の店舗を、都道府県別に掲載しています。
          公式サイトで公開されている項目のみを掲載しているため、他のブランドと比べて掲載項目が少ない場合があります。
        </p>
        <div className="g-brand-hero-shot"><BrandShot slug={slug} name={b.name} /></div>
      </section>

      <div className="stats">
        <div><div className="v">{b.count}</div><div className="k">掲載店舗</div></div>
        <div><div className="v">{b.prefs.length}</div><div className="k">都道府県</div></div>
        <div><div className="v">{n24}</div><div className="k">24時間営業</div></div>
        <div><div className="v">{nPrivate}</div><div className="k">個室で打てる</div></div>
      </div>

      <h2>公式サイトでの情報公開状況</h2>
      <div className="tablewrap">
        <table>
          <thead><tr><th>項目</th><th>公式サイトでの公開状況</th></tr></thead>
          <tbody>
            <tr><td>営業時間</td><td>{b.has.hours ? '店舗ページに記載あり' : '店舗ページに記載なし'}</td></tr>
            <tr><td>打席・個室</td><td>{b.has.bays ? '店舗ページに記載あり' : '店舗ページに記載なし'}</td></tr>
            <tr><td>駐車場</td><td>{b.has.parking ? '店舗ページに記載あり' : '店舗ページに記載なし'}</td></tr>
            <tr><td>アクセス</td><td>{b.has.access ? '店舗ページに記載あり' : '店舗ページに記載なし'}</td></tr>
            <tr><td>料金（月会費）</td><td>{b.has.monthlyFee ? '店舗ごとに記載あり' : '店舗ページに記載なし'}</td></tr>
          </tbody>
        </table>
      </div>
      {!b.has.monthlyFee && (
        <div className="nodata">
          {b.name}は、公式サイトの店舗ページに店舗ごとの料金を掲載していません。
          当サイトでは推測による金額の掲載は行っていないため、料金欄は「公式サイトに記載なし」と表示しています。
          料金は、公式サイトの料金ページまたは各店舗にてご確認ください。
        </div>
      )}

      {b.has.monthlyFee && (
        <>
          <h2>店舗ごとの月会費</h2>
          <div className="tablewrap">
            <table>
              <thead><tr><th>店舗</th><th>所在地</th><th>月会費（公式サイト掲載の金額）</th></tr></thead>
              <tbody>
                {fs.filter((f) => f.monthly_fee).map((f) => (
                  <tr key={f.slug}>
                    <td><Link href={`/facility/${f.slug}/`}>{f.name}</Link></td>
                    <td>{f.pref}{cityOf(f) !== f.pref ? cityOf(f) : ''}</td>
                    <td>{f.monthly_fee}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {taxMixed(fs) && (
            <p className="source">
              ※税込・税抜の表記は店舗により異なります。公式サイトの表記のまま掲載していますので、
              金額を比較される際はご注意ください。
            </p>
          )}
        </>
      )}

      {groups.map(([pref, list]) => (
        <div key={pref}>
          <h2>
            {pref}の{b.name}（{list.length}件）
          </h2>
          <div className="cards">
            {list.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
          <p className="source">
            <Link href={`/area/${PREF_SLUG[pref]}/`}>
              {pref}のシミュレーションゴルフ施設をすべて見る
            </Link>
          </p>
        </div>
      ))}

      <h2>ほかのブランド</h2>
      <div className="chips">
        {brands().filter((x) => x.slug !== slug).map((x) => (
          <Link key={x.slug} href={`/brand/${x.slug}/`}>
            {x.name}<span className="c">{x.count}</span>
          </Link>
        ))}
      </div>
      <p className="source">{asOf(GENERATED_AT)}の公式サイトの掲載内容にもとづいています。</p>
      {soon.length > 0 && (
        <>
          <h2>開業準備中の店舗（{soon.length}件）</h2>
          <p>公式サイトで開業が告知されている店舗です。上記の掲載件数には含めていません。</p>
          <ul className="chips">
            {soon.map((f) => (
              <li key={f.slug}>
                <Link href={`/facility/${f.slug}/`}>{f.name}</Link>
                {f.pref && <span className="sub">　{f.pref}</span>}
              </li>
            ))}
          </ul>
        </>
      )}

    </main>
  )
}
