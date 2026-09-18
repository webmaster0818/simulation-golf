import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, FEATURES, byFeature, PREF_SLUG, asOf, GENERATED_AT,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'

type Params = { slug: string }

export function generateStaticParams(): Params[] {
  return FEATURES.map((f) => ({ slug: f.slug }))
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params
  const ft = FEATURES.find((x) => x.slug === slug)
  if (!ft) return {}
  const n = byFeature(slug).length
  return {
    title: `${ft.label}シミュレーションゴルフ${n}施設｜全国一覧`,
    description: `${ft.note}を全国から集めた一覧です（${n}件）。公式サイトの掲載内容で判定しています。`,
    alternates: { canonical: `${SITE.origin}/feature/${slug}/` },
  }
}

export default async function FeaturePage({ params }: { params: Promise<Params> }) {
  const { slug } = await params
  const ft = FEATURES.find((x) => x.slug === slug)
  if (!ft) return null
  const fs = byFeature(slug)

  const groups = new Map<string, typeof fs>()
  for (const f of fs) {
    if (!f.pref) continue
    groups.set(f.pref, [...(groups.get(f.pref) ?? []), f])
  }
  const list = [...groups.entries()].sort((a, b) => b[1].length - a[1].length)

  return (
    <main className="wrap">
      <nav className="crumbs"><Link href="/">ホーム</Link> / {ft.label}</nav>
      <section className="hero">
        <div className="kicker">Filter</div>
        <h1>{ft.label}シミュレーションゴルフ（{fs.length}件）</h1>
        <p className="lead">{ft.note}を集めた一覧です。</p>
      </section>

      <div className="verdict">
        <span className="tag">判定の基準</span>
        <p style={{ marginBottom: 0 }}>
          {ft.note}だけを載せています。公式サイトにその記載が無い施設は、
          設備が無いとは限りませんが、確認できないためこの一覧には含めていません。
        </p>
      </div>

      {list.map(([pref, items]) => (
        <div key={pref}>
          <h2>{pref}（{items.length}件）</h2>
          <div className="cards">
            {items.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
          <p className="source">
            <Link href={`/area/${PREF_SLUG[pref]}/`}>{pref}の施設をすべて見る</Link>
          </p>
        </div>
      ))}

      <h2>ほかの条件で絞る</h2>
      <div className="chips">
        {FEATURES.filter((x) => x.slug !== slug).map((x) => (
          <Link key={x.slug} href={`/feature/${x.slug}/`}>
            {x.label}<span className="c">{byFeature(x.slug).length}</span>
          </Link>
        ))}
      </div>
      <p className="source">{asOf(GENERATED_AT)}の公式サイト掲載内容にもとづきます。</p>
    </main>
  )
}
