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
              <h2 id="policy-title" className="g-h2">掲載ポリシー</h2>
            </div>
            <div className="g-policy" data-reveal>
              {/* 2026-10-16 MediaXAI「fit-best.com/content-policy を参考に、シミュレーションゴルフの比較サイトとしての表記に」 */}
              <div>
                <h3>目的に合う一軒を、最短で見つけられるように</h3>
                <p>
                  シミュレーションゴルフは、24時間の無人店・完全個室・コーチ付きのスクール・弾道計測つきの練習場と、
                  形がさまざまです。エリア・ブランド・機材・こだわり条件から、目的に合う施設を探せるように整理しています。
                </p>
              </div>
              <div>
                <h3>公式サイトの情報を、正確に、新しく</h3>
                <p>
                  掲載するのは各施設・ブランドの公式サイトに書かれている内容だけです。施設ごとに出典のURLと取得日を添え、
                  チェーンの店舗一覧は定期的に取り直して、新店・閉店・オープン日の変更を反映しています。
                </p>
              </div>
              <div>
                <h3>口コミや点数で順位をつけません</h3>
                <p>
                  ★評価やランキングは載せていません。点数をつけると、情報を集めやすい店が有利になってしまうためです。
                  並び順や掲載内容は、どの施設にも同じ基準で出しています。
                </p>
              </div>
              <div>
                <h3>分からないことは、分からないと書きます</h3>
                <p>
                  公式サイトで確認できなかった項目は、推測で埋めずに「公式サイトに記載なし」と表示します。
                  料金や営業時間は変わるので、利用前にはリンク先の公式サイトで最新の内容をご確認ください。
                </p>
              </div>
            </div>
            <p className="g-policy-link" data-reveal>
              <Link href="/data/">掲載ポリシーと情報の集め方を詳しく見る</Link>
            </p>
          </div>
        </section>
      </div>
    </>
  )
}
