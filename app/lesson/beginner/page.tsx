import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { JsonLd, breadcrumb, faqLd } from '../../../lib/seo'
import { OPEN_FACILITIES, PREF_SLUG, brands } from '../../../lib/data'
import { RIZAP, ymd } from '../../../lib/rizap'
import { yen, BRAND_FACTS } from '../../../lib/brand-facts'
import trials from '../../../data/kwexp/lesson-trials.json'

// 2026-11-16 kwexp「ゴルフ 初心者 レッスン」（aramakijake 月3,520）。
// 当サイトの掲載データ（スクールの店舗数・月会費）と、各ブランド公式の体験の案内（data/kwexp/lesson-trials.json）で作る。

/** 月会費（税込）の最小・最大。公式の店舗ページの表記から「税込◯円」だけを読む。読めない店は数えない */
function feeRange(slug: string): { min: number; max: number; n: number } | null {
  // ZEN GOLF は掲載データの月会費がレッスン会員・全日だけなので、全店の公式料金表を読んだ値（brand-facts の feeFixed）を使う
  const fixed = BRAND_FACTS[slug]?.feeFixed
  if (fixed) return { min: fixed.min, max: fixed.max, n: fixed.n }
  let min = Infinity, max = -Infinity, n = 0
  for (const f of OPEN_FACILITIES) {
    if (f.brand_slug !== slug || !f.monthly_fee) continue
    const vals = [...f.monthly_fee.split('別途')[0].split('入会金')[0].matchAll(/税込\s*([\d,]+)円/g)].map((m) => Number(m[1].replace(/,/g, '')))
    if (!vals.length) continue
    n++
    min = Math.min(min, ...vals)
    max = Math.max(max, ...vals)
  }
  return n ? { min, max, n } : null
}

const LESSON = OPEN_FACILITIES.filter((f) => f.segment === 'lesson')
const checked = ymd(trials.checked)

export const metadata: Metadata = {
  title: `ゴルフ初心者のレッスン選び｜スクール9ブランドの体験料金と料金の形を比較`,
  description:
    `ゴルフ初心者がスクールを選ぶときに、体験の料金（無料〜税込11,000円）と料金の形（月会費・コース制・チケット制）を公式サイトの掲載どおりに比較。` +
    `当サイトに掲載しているシミュレーター併設スクール${LESSON.length}店舗の都道府県別の件数も掲載しています。`,
  ...pageUrlMeta('/lesson/beginner/'),
}

export default function BeginnerLessonPage() {
  const bs = brands()
  const name = (slug: string) => (slug === 'rizapgolf' ? 'ライザップゴルフ（RIZAP GOLF）' : bs.find((b) => b.slug === slug)?.name ?? slug)
  const count = (slug: string) => (slug === 'rizapgolf' ? RIZAP.stores.length : LESSON.filter((f) => f.brand_slug === slug).length)
  const rows = trials.brands.map((t) => ({ ...t, name: name(t.brand_slug), n: count(t.brand_slug), fee: t.brand_slug === 'rizapgolf' ? null : feeRange(t.brand_slug) }))
  const free = rows.filter((r) => r.trial_inc === 0)

  const byPref = new Map<string, number>()
  for (const f of LESSON) if (f.pref) byPref.set(f.pref, (byPref.get(f.pref) ?? 0) + 1)
  const prefs = [...byPref.entries()].sort((a, b) => b[1] - a[1])

  const faq = [
    {
      q: 'ゴルフ初心者がレッスンの体験にかかる費用はいくらですか。',
      a: `当サイトで確認した9ブランドでは、無料（${free.map((r) => r.name).join('・')}）から税込11,000円（GOLFTEC・JIN-golf）まで幅があります（${checked}時点の公式サイトの記載）。`,
    },
    {
      q: '道具を持っていなくても始められますか。',
      a: 'クラブ・シューズなどの無料レンタルを案内しているスクールがあります（チキンゴルフ・インザゴルフ・GOLFTEC・ライザップゴルフなど。ライザップゴルフはグローブのみ持参）。対象の道具はスクールにより異なります。',
    },
    {
      q: '月会費制とコース制はどう違いますか。',
      a: `月会費制は毎月定額を払って通う形で、ステップゴルフ・ZEN GOLF・インザゴルフなどが該当します。コース制は回数を決めて申し込む形で、ライザップゴルフは全16回（2ヶ月）税込${yen(RIZAP.course_fees[0].inc)}〜です。`,
    },
  ]
  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'ゴルフ初心者のレッスン選び', url: '/lesson/beginner/' },
    ]),
    faqLd(faq),
  ]

  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs"><Link href="/">ホーム</Link> / ゴルフ初心者のレッスン選び</nav>

      <section className="hero">
        <div className="kicker">Lesson</div>
        <h1>ゴルフ初心者のレッスン選び：スクール9ブランドの体験料金と料金の形</h1>
        <p className="lead">
          シミュレーターを備えたゴルフスクール9ブランドの体験は、無料から税込11,000円までです。
          無料の体験を案内しているのは{free.map((r) => r.name).join('・')}の{free.length}ブランドです。
          料金の形は、月会費で通う形・回数を決めるコース制・チケット制に分かれます。
        </p>
        <p className="lead">
          体験の内容と料金は{checked}に各ブランドの公式サイトで確認したものです。
          店舗数と月会費は、当サイトが各公式の店舗ページから集めたデータ（スクール{LESSON.length}店舗）から計算しています。
        </p>
      </section>

      <h2>ブランド別の体験・料金の形</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr><th>ブランド</th><th>店舗数</th><th>体験（公式の案内）</th><th>料金の形</th><th>月会費（税込・店舗ページの掲載額）</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.brand_slug}>
                <td><Link href={`/brand/${r.brand_slug}/`}>{r.name}</Link></td>
                <td className="num">{r.n}</td>
                <td>{r.trial}（<a href={r.url} target="_blank" rel="noopener noreferrer">出典</a>）</td>
                <td>{r.format}</td>
                <td>
                  {r.brand_slug === 'rizapgolf'
                    ? 'コース制のため月会費なし'
                    : r.fee
                      ? `${yen(r.fee.min)}〜${yen(r.fee.max)}（${r.fee.n}店舗）`
                      : '店舗ページに記載なし'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        店舗数は当サイトの掲載件数（営業中）で、ライザップゴルフのみ公式の店舗一覧の件数です。
        月会費は各店舗ページの「税込◯円」の表記を読み、最も低い額と最も高い額を出しています。プランの利用時間帯（平日昼のみ等）や会員区分により金額が異なるため、
        最も低い額は条件付きのプランであることがあります。入会金・打席料などは含みません。
        体験の料金はキャンペーンにより変わることがありますので、ご利用前に公式サイトにてご確認ください。
      </p>

      <h2>体験の前に確認しておきたい項目</h2>
      <dl className="spec">
        <div>
          <dt>体験の長さ</dt>
          <dd>公式に記載のある範囲では、30分（インザゴルフ）・50分（サンクチュアリゴルフ・GANTT GOLF 江坂店）・60分（GOLFTEC・ライザップゴルフ）です。</dd>
        </div>
        <div>
          <dt>入会金</dt>
          <dd>
            チキンゴルフは入会金35,000円、ライザップゴルフは税込{yen(RIZAP.admission_inc)}と公式サイトに記載があります。
            ステップゴルフは別途 入会初期費用（税込43,780円・体験後7日以内の入会は32,780円）がかかります。
          </dd>
        </div>
        <div>
          <dt>レッスンの形</dt>
          <dd>マンツーマン（GOLFTEC・JIN-golf・ライザップゴルフ）と、セミパーソナル（チキンゴルフ・GANTT GOLF 江坂店）があります。形式の詳細は各公式サイトの案内をご確認ください。マンツーマンの1回の時間と料金は<Link href="/lesson/private/">ゴルフのマンツーマンレッスン</Link>、月会費制のスクールの料金の表記は<Link href="/guide/golf-subscription/">ゴルフのサブスク</Link>にまとめています。</dd>
        </div>
      </dl>

      <h2>都道府県別のスクールの数（当サイト掲載）</h2>
      <p>
        当サイトに掲載しているシミュレーター併設スクール{LESSON.length}店舗（ライザップゴルフを除く）の所在地です。
        コーチのつかない屋内シミュレーションゴルフとの違いは<Link href="/guide/indoor-golf/">インドアゴルフとは</Link>にまとめています。
      </p>
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
        掲載内容は{checked}時点の各公式サイトの記載にもとづいています。
      </p>
    </main>
  )
}
