import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, PREF_SLUG, brands, byBrand, cityOf, asOf, GENERATED_AT,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'

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
      `${b.name}の店舗${b.count}件を、公式サイトの情報で一覧にしました。` +
      `${b.prefs.length}都道府県に展開。${b.has.monthlyFee ? '店舗ごとの月会費も掲載しています。' : '店舗ごとの料金は公式サイトに記載がないため掲載していません。'}`,
    alternates: { canonical: `${SITE.origin}/brand/${slug}/` },
  }
}

export default async function BrandPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params
  const b = brands().find((x) => x.slug === slug)
  if (!b) return null
  const fs = byBrand(slug)
  const n24 = fs.filter((f) => f.open_24h).length
  const nPrivate = fs.filter((f) => f.private_room === true || /個室/.test(f.bays ?? '')).length

  const byPrefMap = new Map<string, typeof fs>()
  for (const f of fs) {
    if (!f.pref) continue
    byPrefMap.set(f.pref, [...(byPrefMap.get(f.pref) ?? []), f])
  }
  const groups = [...byPrefMap.entries()].sort((a, b2) => b2[1].length - a[1].length)

  return (
    <main className="wrap">
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/brand/">ブランドから探す</Link> / {b.name}
      </nav>

      <section className="hero">
        <div className="kicker">{slug}</div>
        <h1>{b.name}の店舗一覧（{b.count}件）</h1>
        <p className="lead">
          公式サイトに掲載されている{b.name}の店舗を、都道府県別に並べています。
          このブランドが公式で公開している項目だけを載せているため、
          他ブランドと比べて項目が少ない場合があります。
        </p>
      </section>

      <div className="stats">
        <div><div className="v">{b.count}</div><div className="k">掲載店舗</div></div>
        <div><div className="v">{b.prefs.length}</div><div className="k">都道府県</div></div>
        <div><div className="v">{n24}</div><div className="k">24時間営業</div></div>
        <div><div className="v">{nPrivate}</div><div className="k">個室で打てる</div></div>
      </div>

      <h2>このブランドで比較できること</h2>
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
          {b.name}は、店舗ごとの料金を公式サイトの店舗ページに載せていません。
          当サイトでは金額を推測して載せることはしないため、料金欄は空欄になります。
          料金は公式サイトの料金ページ、または各店舗へ直接ご確認ください。
        </div>
      )}

      {b.has.monthlyFee && (
        <>
          <h2>店舗ごとの月会費</h2>
          <div className="tablewrap">
            <table>
              <thead><tr><th>店舗</th><th>所在地</th><th>月会費（公式表記のまま）</th></tr></thead>
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
          <p className="source">
            ⚠️ 税抜と税込が店舗によって混在しています。公式サイトの表記をそのまま載せているため、
            金額だけを並べて比べないでください。
          </p>
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
              {pref}のシミュレーションゴルフをブランド横断で見る
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
      <p className="source">{asOf(GENERATED_AT)}の公式サイト掲載内容にもとづきます。</p>
    </main>
  )
}
