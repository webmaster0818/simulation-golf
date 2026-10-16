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
              のページでご確認いただけます。{asOf(GENERATED_AT)}の公式サイトの掲載内容にもとづいています。
            </p>
          </div>
        </section>

        <BrandGrid />

        <section className="g-section" aria-labelledby="policy-title" data-landing>
          <div className="wrap narrow">
            <div className="g-head" data-reveal>
              <p className="g-eyebrow">POLICY</p>
              <h2 id="policy-title" className="g-h2">掲載ポリシー</h2>
            </div>
            <div className="g-policy" data-reveal>
              {/* 2026-10-16 MediaXAI「fit-best.com/content-policy を参考に」「ビジネスライクな日本語に」 */}
              <div>
                <h3>利用者の目的に沿った施設選びを支援します</h3>
                <p>
                  当サイトでは、24時間営業の無人店舗、完全個室型の施設、コーチ付きのインドアゴルフスクール、
                  弾道計測を導入した練習場など、さまざまな形態のシミュレーションゴルフ施設を掲載しています。
                  エリア・ブランド・計測機器・設備条件から、施設を比較・検索いただけます。
                </p>
              </div>
              <div>
                <h3>公式情報にもとづく正確な情報提供に努めます</h3>
                <p>
                  掲載情報は、各施設・ブランドの公式サイトで公開されている内容に限定しています。
                  施設ごとに出典URLと情報取得日を明記し、新規開業・閉店・料金改定などは定期的に確認のうえ更新しています。
                </p>
              </div>
              <div>
                <h3>中立的な立場で情報を掲載します</h3>
                <p>
                  当サイトでは、口コミ・評価点・ランキングを掲載していません。
                  特定の施設が有利または不利にならないよう、すべての施設を同一の基準で掲載しています。
                </p>
              </div>
              <div>
                <h3>未確認の情報は掲載しません</h3>
                <p>
                  公式サイトで確認できない項目は推測による補完を行わず、「公式サイトに記載なし」と表示しています。
                  料金や営業時間は変更される場合がありますので、ご利用前に各施設の公式サイトにて最新情報をご確認ください。
                </p>
              </div>
            </div>
            <p className="g-policy-link" data-reveal>
              <Link href="/data/">掲載ポリシーの詳細はこちら</Link>
            </p>
          </div>
        </section>
      </div>
    </>
  )
}
