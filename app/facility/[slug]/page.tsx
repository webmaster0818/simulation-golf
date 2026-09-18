import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, PREF_SLUG, FACILITIES, OPEN_FACILITIES, bySlug, byPref, cityOf, asOf,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'

type Params = { slug: string }

export function generateStaticParams(): Params[] {
  return FACILITIES.map((f) => ({ slug: f.slug }))
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params
  const f = bySlug(slug)
  if (!f) return {}
  const where = [f.pref, cityOf(f)].filter(Boolean).join('')
  return {
    title: `${f.name}｜${where}のシミュレーションゴルフ`,
    description:
      `${f.name}（${f.address ?? where}）の基本情報。` +
      [f.hours && `営業時間 ${f.hours}`, f.bays && `打席 ${f.bays}`, f.parking && `駐車場 ${f.parking}`]
        .filter(Boolean).join('／') +
      '。公式サイトの掲載内容をそのまま記載しています。',
    alternates: { canonical: `${SITE.origin}/facility/${slug}/` },
  }
}

/** 値が無いときは推測せず、無いと書く */
function Row({ k, v }: { k: string; v: string | null | undefined }) {
  return (
    <div>
      <dt>{k}</dt>
      {v ? <dd>{v}</dd> : <dd className="none">公式サイトに記載なし</dd>}
    </div>
  )
}

export default async function FacilityPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params
  const f = bySlug(slug)
  if (!f) return null

  const city = cityOf(f)
  const near = f.pref
    ? byPref(f.pref).filter((x) => x.slug !== f.slug).slice(0, 6)
    : []
  const sameBrand = f.brand_slug
    ? OPEN_FACILITIES.filter((x) => x.brand_slug === f.brand_slug && x.slug !== f.slug)
    : []

  // 構造化データ。住所が取れているものだけ出す（不完全なデータを機械に渡さない）。
  const ld = {
    '@context': 'https://schema.org',
    '@type': 'SportsActivityLocation',
    name: f.name,
    ...(f.address ? { address: { '@type': 'PostalAddress', streetAddress: f.address, addressRegion: f.pref, postalCode: f.zip ?? undefined, addressCountry: 'JP' } } : {}),
    ...(f.tel ? { telephone: f.tel } : {}),
    ...(f.official ? { sameAs: [f.official] } : {}),
    url: `${SITE.origin}/facility/${f.slug}/`,
  }

  return (
    <main className="wrap">
      <script type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />

      <nav className="crumbs">
        <Link href="/">ホーム</Link>
        {f.pref && (
          <>
            {' / '}
            <Link href={`/area/${PREF_SLUG[f.pref]}/`}>{f.pref}</Link>
          </>
        )}
        {' / '}{f.name}
      </nav>

      <section className="hero">
        <div className="kicker">
          {f.brand ?? 'Driving range with ball tracing'}
        </div>
        <h1>{f.name}</h1>
        <p className="lead">
          {f.pref}
          {city && city !== f.pref ? city : ''}にある
          {f.segment === 'indoor' ? '屋内のシミュレーションゴルフ施設' : '弾道計測つきの練習場'}です。
          下の情報はすべて公式サイトに掲載されている内容で、{asOf(f.fetched_at)}のものです。
        </p>
      </section>

      {!f.open && (
        <div className="verdict">
          <span className="tag">Notice</span>
          <p style={{ marginBottom: 0 }}>
            この店舗は公式サイトで<strong>オープン準備中</strong>と案内されています。
            {f.hours ? '' : '営業条件は開業後に変わる可能性があります。'}
            利用前に公式サイトでご確認ください。
          </p>
        </div>
      )}

      <h2>基本情報</h2>
      <dl className="spec">
        <Row k="住所" v={f.zip ? `〒${f.zip} ${f.address}` : f.address} />
        <Row k="アクセス" v={f.access} />
        <Row k="電話番号" v={f.tel} />
        <Row k="営業時間" v={f.hours} />
        <Row k="定休日" v={f.closed} />
        <Row k="打席・個室" v={f.bays} />
        <Row k="駐車場" v={f.parking} />
        {f.segment === 'indoor'
          ? <Row k="月会費" v={f.monthly_fee} />
          : <Row k="弾道計測の利用料" v={f.usage_fee} />}
        {f.segment === 'range' && (
          <>
            <Row k="飛距離" v={f.distance_yard ? `${f.distance_yard}ヤード` : null} />
            <Row k="計測の設備" v={f.equipment} />
          </>
        )}
      </dl>

      {f.segment === 'indoor' && !f.monthly_fee && (
        <div className="nodata">
          このブランドは、店舗ごとの料金を公式サイトで公開していません。
          料金は店舗によって違うことがあるため、当サイトでは推測した金額を載せていません。
          公式サイトまたは店舗へ直接ご確認ください。
        </div>
      )}

      <p>
        {f.official && (
          <a className="official" href={f.official} target="_blank" rel="noopener noreferrer">
            公式サイトを見る
          </a>
        )}
        {f.address && (
          <a className="official"
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(f.address)}`}
            target="_blank" rel="noopener noreferrer">
            地図で見る
          </a>
        )}
      </p>

      <p className="source">
        出典：
        <a href={f.source_url} target="_blank" rel="noopener noreferrer">{f.source_url}</a>
        （{asOf(f.fetched_at)}に取得）。
        料金・営業時間・設備は変更されることがあります。利用前に公式サイトで最新の内容をご確認ください。
      </p>

      {sameBrand.length > 0 && f.brand_slug && (
        <>
          <h2>{f.brand}のほかの店舗</h2>
          <div className="cards">
            {sameBrand.slice(0, 6).map((x) => <FacilityCard key={x.slug} f={x} />)}
          </div>
          <p className="source">
            <Link href={`/brand/${f.brand_slug}/`}>
              {f.brand}の全{sameBrand.length + 1}店舗を見る
            </Link>
          </p>
        </>
      )}

      {near.length > 0 && f.pref && (
        <>
          <h2>{f.pref}のほかの施設</h2>
          <div className="cards">
            {near.map((x) => <FacilityCard key={x.slug} f={x} />)}
          </div>
          <p className="source">
            <Link href={`/area/${PREF_SLUG[f.pref]}/`}>
              {f.pref}の施設をすべて見る（{byPref(f.pref).length}件）
            </Link>
          </p>
        </>
      )}
    </main>
  )
}
