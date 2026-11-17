import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { JsonLd, breadcrumb, faqLd } from '../../../lib/seo'
import { OPEN_FACILITIES, FEATURES, PREF_SLUG, asOf, GENERATED_AT, type Facility } from '../../../lib/data'

// 2026-11-17 kwexp「インドアゴルフとは」（aramakijake 月72）。
// 一般的な説明に加え、当サイトの掲載データ（各施設の公式ページから集めた値）を形態別に集計して示す。

type Seg = Facility['segment']
const SEGS: { seg: Seg; label: string; what: string }[] = [
  {
    seg: 'indoor',
    label: '屋内シミュレーションゴルフ',
    what: '屋内の打席で、弾道計測器・シミュレーターの表示を見ながら自分で打つ施設です。コーチはつかず、空いている時間に自分のペースで練習する形です。',
  },
  {
    seg: 'lesson',
    label: 'インドアゴルフスクール',
    what: 'シミュレーターを備えた屋内の打席で、コーチのレッスンを受ける施設です。予約制で、月会費制・コース制などの料金の形があります。',
  },
  {
    seg: 'range',
    label: '屋外練習場（弾道計測あり）',
    what: '屋外の打ちっぱなし練習場に弾道計測（トップトレーサー・レンジ、トラックマン）を導入した施設です。屋内ではありませんが、計測の表示を見ながら打てる点が共通しています。',
  },
]

const PRIVATE = FEATURES.find((x) => x.slug === 'private-room')!.match
const pct = (n: number, d: number) => (d ? Math.round((n / d) * 100) : 0)

function stats(seg: Seg) {
  const fs = OPEN_FACILITIES.filter((f) => f.segment === seg)
  const byBrand = new Map<string, { name: string; n: number }>()
  for (const f of fs) {
    if (!f.brand_slug || !f.brand) continue
    const b = byBrand.get(f.brand_slug) ?? { name: f.brand, n: 0 }
    b.n++
    byBrand.set(f.brand_slug, b)
  }
  const top = [...byBrand.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 3)
  return {
    n: fs.length,
    h24: fs.filter((f) => f.open_24h === true).length,
    priv: fs.filter(PRIVATE).length,
    equip: fs.filter((f) => !!f.equipment).length,
    brands: byBrand.size,
    top,
  }
}

const ROWS = SEGS.map((s) => ({ ...s, ...stats(s.seg) }))
const INDOOR = ROWS.find((r) => r.seg === 'indoor')!
const LESSON = ROWS.find((r) => r.seg === 'lesson')!
const RANGE = ROWS.find((r) => r.seg === 'range')!
const IN_ALL = INDOOR.n + LESSON.n
const TT = OPEN_FACILITIES.filter((f) => f.segment === 'range' && f.equipment === 'トップトレーサー・レンジ').length

export const metadata: Metadata = {
  title: `インドアゴルフとは｜3つの形と掲載${OPEN_FACILITIES.length.toLocaleString()}施設の設備の集計`,
  description:
    `インドアゴルフとは、屋内の打席で弾道計測器・シミュレーターを使って練習する施設のことです。` +
    `自分で打つ施設・スクール・計測つきの屋外練習場の違いと、当サイト掲載${OPEN_FACILITIES.length.toLocaleString()}施設の24時間営業・個室・計測機器の件数を形態別に集計しています。`,
  ...pageUrlMeta('/guide/indoor-golf/'),
}

export default function IndoorGolfGuide() {
  const asof = asOf(GENERATED_AT)

  // 屋内（シミュレーション＋スクール）の都道府県別件数
  const byPref = new Map<string, number>()
  for (const f of OPEN_FACILITIES) if (f.segment !== 'range' && f.pref) byPref.set(f.pref, (byPref.get(f.pref) ?? 0) + 1)
  const prefs = [...byPref.entries()].sort((a, b) => b[1] - a[1])

  const faq = [
    {
      q: 'インドアゴルフとシミュレーションゴルフは違うものですか。',
      a: '明確な使い分けの定義はありません。屋内の打席で弾道計測器・シミュレーターを使う施設は、どちらの名前でも呼ばれています。当サイトでは両方を同じ施設として掲載しています。',
    },
    {
      q: 'インドアゴルフは24時間使えますか。',
      a: `施設によります。当サイトに掲載している屋内シミュレーションゴルフ${INDOOR.n}件のうち、公式サイトに24時間営業と明記されているのは${INDOOR.h24}件（${pct(INDOOR.h24, INDOOR.n)}%）です。インドアゴルフスクールでは${LESSON.n}件中${LESSON.h24}件です。`,
    },
    {
      q: '個室で打てる施設はどのくらいありますか。',
      a: `公式サイトに個室・半個室の記載がある施設は、屋内シミュレーションゴルフで${INDOOR.priv}件（${pct(INDOOR.priv, INDOOR.n)}%）、インドアゴルフスクールで${LESSON.priv}件です。記載がない施設にも個室がある場合があります。`,
    },
  ]
  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'インドアゴルフとは', url: '/guide/indoor-golf/' },
    ]),
    faqLd(faq),
  ]

  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs"><Link href="/">ホーム</Link> / インドアゴルフとは</nav>

      <section className="hero">
        <div className="kicker">Guide</div>
        <h1>インドアゴルフとは：施設の3つの形と、掲載{OPEN_FACILITIES.length.toLocaleString()}施設の設備の集計</h1>
        <p className="lead">
          インドアゴルフとは、屋内の打席でボールを打ち、弾道計測器やシミュレーターで飛距離・弾道を確かめながら練習する施設のことです。
          屋内のため、雨の日や日没後でも同じ条件で打つことができます。
        </p>
        <p className="lead">
          当サイトに掲載している屋内の施設は{IN_ALL.toLocaleString()}件で、自分で打つ屋内シミュレーションゴルフが{INDOOR.n}件、
          コーチのいるインドアゴルフスクールが{LESSON.n}件です。
          以下の件数は、当サイトが各施設の公式ページから集めた掲載データ（{asof}）を形態別に集計したものです。
        </p>
      </section>

      <h2>インドアゴルフ施設の3つの形</h2>
      <dl className="spec">
        {ROWS.map((r) => (
          <div key={r.seg}><dt>{r.label}</dt><dd>{r.what}</dd></div>
        ))}
      </dl>

      <h2>形態別の掲載件数と設備（当サイトの集計）</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>形態</th><th>掲載件数</th><th>24時間営業の明記</th><th>個室・半個室の記載</th><th>計測機器の機種を確認</th><th>ブランド数</th><th>掲載の多いブランド</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.seg}>
                <td>{r.label}</td>
                <td className="num">{r.n}</td>
                <td className="num">{r.h24}（{pct(r.h24, r.n)}%）</td>
                <td className="num">{r.priv}（{pct(r.priv, r.n)}%）</td>
                <td className="num">{r.equip}（{pct(r.equip, r.n)}%）</td>
                <td className="num">{r.brands}</td>
                <td>
                  {r.top.length
                    ? r.top.map(([slug, b], i) => (
                        <span key={slug}>{i > 0 && '・'}<Link href={`/brand/${slug}/`}>{b.name}</Link>（{b.n}）</span>
                      ))
                    : '練習場ごとに掲載（ブランド単位では集計していません）'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        件数は営業中の施設のみで、開業準備中の施設は含みません。
        「24時間営業の明記」「個室・半個室の記載」は、公式サイトにその記載がある施設の数です。記載がない施設に設備がないことを示すものではありません。
        「計測機器の機種を確認」は、公式サイトで機種名を確認できた施設の数です。集計方法は<Link href="/data/">掲載ポリシー</Link>をご覧ください。
      </p>

      <h2>集計から分かること</h2>
      <ul>
        <li>
          屋内シミュレーションゴルフは{pct(INDOOR.h24, INDOOR.n)}%が24時間営業を明記しており、早朝・深夜にも利用できる施設が中心です。
          インドアゴルフスクールで24時間営業を明記しているのは{pct(LESSON.h24, LESSON.n)}%で、レッスンの営業時間内に通う形が中心です。
        </li>
        <li>
          個室・半個室の記載があるのは、屋内シミュレーションゴルフで{pct(INDOOR.priv, INDOOR.n)}%、スクールで{pct(LESSON.priv, LESSON.n)}%です。
          個室を重視する場合は、<Link href="/feature/private-room/">個室で打てる施設の一覧</Link>から探せます。
        </li>
        <li>
          計測機器の機種名を公式サイトで公開している屋内の施設は{IN_ALL.toLocaleString()}件中{INDOOR.equip + LESSON.equip}件です。
          計測方式の違いは<Link href="/equipment/">計測機器から探す</Link>にまとめています。
        </li>
        <li>
          屋外練習場（弾道計測あり）{RANGE.n}件のうち、{TT}件はトップトレーサー・レンジ、{RANGE.n - TT}件はトラックマンの導入施設です。
        </li>
      </ul>

      <h2>目的別の探し方</h2>
      <div className="chips">
        <Link href="/feature/open-24h/">24時間営業の施設</Link>
        <Link href="/feature/private-room/">個室で打てる施設</Link>
        <Link href="/feature/parking/">駐車場のある施設</Link>
        <Link href="/lesson/beginner/">初心者向けのレッスン選び（スクールの体験料金）</Link>
        <Link href="/brand/">ブランドから探す</Link>
        <Link href="/equipment/">計測機器から探す</Link>
      </div>

      <h2>都道府県別の屋内施設の数（当サイト掲載）</h2>
      <p>屋内シミュレーションゴルフとインドアゴルフスクールの合計{IN_ALL.toLocaleString()}件の所在地です。</p>
      <div className="chips">
        {prefs.map(([p, n]) => (
          <Link key={p} href={`/area/${PREF_SLUG[p]}/`}>{p}<span className="c">{n}</span></Link>
        ))}
      </div>

      <h2>よくある質問</h2>
      <dl className="spec">
        {faq.map((x) => (
          <div key={x.q}><dt>{x.q}</dt><dd>{x.a}</dd></div>
        ))}
      </dl>

      <p className="source">
        当サイトは口コミ・評価点を掲載していません。順位付けは行っていません。
        各施設の料金・営業時間は変更される場合がありますので、ご利用前に公式サイトにてご確認ください。
      </p>
    </main>
  )
}
