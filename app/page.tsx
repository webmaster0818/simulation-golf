import { pageUrlMeta } from '../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { SITE, PREF_SLUG, byPref, activePrefs, GENERATED_AT, asOf } from '../lib/data'
import FacilityCard from '../components/FacilityCard'
import TopHero from '../components/TopHero'
import FeatureGrid from '../components/FeatureGrid'
import AreaAccordion from '../components/AreaAccordion'
import BrandGrid from '../components/BrandGrid'
import BallTrace from '../components/BallTrace'
import Reveal from '../components/Reveal'
import { JsonLd, websiteLd } from '../lib/seo'

export const metadata: Metadata = {
  title: `${SITE.name}｜全国のシミュレーションゴルフを公式情報で比較`,
  description: SITE.description,
  ...pageUrlMeta(`/`),
}

export default function Home() {
  const prefs = activePrefs()
  const ranked = prefs
    .map((p) => ({ pref: p, n: byPref(p).length }))
    .sort((a, b) => b.n - a.n)

  const ld = [websiteLd()]
  return (
    <>
      <JsonLd data={ld} />
      <TopHero />
      <Reveal />
      {/* 弾道ライン：この中の [data-landing] に着地する（BallTrace） */}
      <div className="g-trace-host">
        <BallTrace />
        <FeatureGrid />
        <AreaAccordion />

        <section className="g-section" aria-labelledby="popular-title" data-landing>
          <div className="wrap">
            <div className="g-head" data-reveal>
              <p className="g-eyebrow">POPULAR AREAS</p>
              <h2 id="popular-title" className="g-h2">掲載の多いエリア</h2>
            </div>
            <div className="cards" data-reveal>
              {ranked.slice(0, 6).flatMap((r) => byPref(r.pref).slice(0, 1)).map((f) => (
                <FacilityCard key={f.slug} f={f} />
              ))}
            </div>
            <p className="source">
              各エリアの全施設は{' '}
              {ranked.slice(0, 6).map((r, i) => (
                <span key={r.pref}>
                  {i > 0 && '・'}
                  <Link href={`/area/${PREF_SLUG[r.pref]}/`}>{r.pref}（{r.n}件）</Link>
                </span>
              ))}{' '}
              のページで確認できます。{asOf(GENERATED_AT)}の公式サイト掲載内容にもとづきます。
            </p>
          </div>
        </section>

        <BrandGrid />

        <section className="g-section" aria-labelledby="policy-title" data-landing>
          <div className="wrap narrow">
            <div className="g-head" data-reveal>
              <p className="g-eyebrow">POLICY</p>
              <h2 id="policy-title" className="g-h2">このサイトの方針</h2>
            </div>
            <div className="verdict" data-reveal>
              <p>
                施設の情報は、公式サイトに書かれている内容だけを載せています。
                公式サイトに記載が無い項目は、推測で埋めずに「公式サイトに記載なし」と表示します。口コミや評価は載せません。
              </p>
              <p>
                営業時間や料金は変わります。掲載内容には取得日を添えているので、
                利用前には必ずリンク先の公式サイトで最新の内容を確認してください。
              </p>
              <p style={{ marginBottom: 0 }}>
                <Link href="/data/">掲載データについて詳しく見る</Link>
              </p>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}
