import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { JsonLd, breadcrumb, faqLd } from '../../../lib/seo'
import { OPEN_FACILITIES, asOf, GENERATED_AT, type Facility } from '../../../lib/data'
import { BRAND_FACTS } from '../../../lib/brand-facts'

// 2026-11-25 kwexp「ゴルフ サブスク」（aramakijake 月1,040）。
// 月会費を払って期間中に練習・レッスンを受ける形（いわゆるサブスク型）のインドアゴルフを、
// 当サイトの掲載データ（各施設の公式ページから集めた月会費の表記）でブランドごとに並べる。
// 表記はブランドごとに形が違うため、金額を機械的に比べず、最も多い表記をそのまま出す。

type Row = {
  slug: string
  name: string
  seg: Facility['segment']
  n: number
  withFee: number
  modeText: string
  modeN: number
  example: Facility
  h24: number
  feeNote?: string
  answerChecked?: string
  fixed?: boolean
}

const INDOOR_ALL = OPEN_FACILITIES.filter((f) => f.segment !== 'range')
const WITH_FEE = INDOOR_ALL.filter((f) => !!f.monthly_fee)

function rows(): Row[] {
  const map = new Map<string, Facility[]>()
  for (const f of INDOOR_ALL) {
    if (!f.brand_slug) continue
    map.set(f.brand_slug, [...(map.get(f.brand_slug) ?? []), f])
  }
  const out: Row[] = []
  for (const [slug, fs] of map) {
    const fee = fs.filter((f) => !!f.monthly_fee)
    if (!fee.length) continue
    const count = new Map<string, number>()
    for (const f of fee) count.set(f.monthly_fee as string, (count.get(f.monthly_fee as string) ?? 0) + 1)
    const [modeText, modeN] = [...count.entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))[0]
    const example = fee.filter((f) => f.monthly_fee === modeText).sort((a, b) => (a.slug < b.slug ? -1 : 1))[0]
    // 公式の料金表全体を確認済みのブランド（brand-facts の answer）は、最も多い表記ではなくその幅を出す（マイゴルは店舗ごとに金額が違い、最も多い表記がマイゴルフレンジの料金になる）
    const ans = BRAND_FACTS[slug]?.answer?.rows.find((x) => x.k.startsWith('月会費'))
    // 掲載データの月会費が代表の1区分だけのブランド（ZEN GOLF RANGE・ラハゴルフ24）は、公式の料金表を全店読んだ幅（feeFixed）を出す
    const fx = BRAND_FACTS[slug]?.feeFixed
    const fxText = fx
      ? `税込${fx.min.toLocaleString('ja-JP')}円〜${fx.max.toLocaleString('ja-JP')}円（最も低いのは${fx.minName}の${fx.minPlan}、最も高いのは${fx.maxName}。${fx.n}店舗の公式の料金表を集計）`
      : null
    out.push({
      slug,
      name: fs[0].brand as string,
      seg: fs[0].segment,
      n: fs.length,
      withFee: fee.length,
      modeText: ans ? ans.v : fxText ?? modeText.replace(/^・/, ''),
      modeN: ans || fxText ? 0 : modeN,
      fixed: !!fxText,
      answerChecked: ans ? BRAND_FACTS[slug]!.answer!.checked : undefined,
      example,
      h24: fs.filter((f) => f.open_24h === true).length,
      feeNote: BRAND_FACTS[slug]?.feeNote,
    })
  }
  return out.sort((a, b) => b.n - a.n || (a.slug < b.slug ? -1 : 1))
}

const ROWS = rows()
const INDOOR_ROWS = ROWS.filter((r) => r.seg === 'indoor')
const LESSON_ROWS = ROWS.filter((r) => r.seg === 'lesson')
const INDEP = WITH_FEE.filter((f) => !f.brand_slug)
const pct = (n: number, d: number) => (d ? Math.round((n / d) * 100) : 0)

export const metadata: Metadata = {
  title: `ゴルフのサブスク（月額定額のインドアゴルフ）｜${ROWS.length}ブランドの月会費の表記と別途かかる費用`,
  description:
    `月会費を払って通う、いわゆるサブスク型のインドアゴルフを、当サイト掲載${ROWS.length}ブランドの公式の月会費の表記で比較。` +
    `打ち放題の練習施設とレッスンに通うスクールの違い、入会金・打席料・回数枠など月会費のほかにかかる費用の確認点をまとめています。`,
  ...pageUrlMeta('/guide/golf-subscription/'),
}

function Table({ list }: { list: Row[] }) {
  return (
    <div className="tablewrap">
      <table>
        <thead>
          <tr><th>ブランド</th><th>掲載店舗</th><th>月会費の表記（最も多い表記・公式の店舗ページ）</th><th>同じ表記の店舗</th><th>24時間営業の明記</th></tr>
        </thead>
        <tbody>
          {list.map((r) => (
            <tr key={r.slug}>
              <td><Link href={`/brand/${r.slug}/`}>{r.name}</Link></td>
              <td className="num">{r.n}</td>
              <td>
                {r.modeText}
                {r.feeNote && !/別途|入会金/.test(r.modeText) && <>（{r.feeNote}）</>}
                <br />
                {r.answerChecked
                  ? <span className="source">全店舗の公式の料金ページを集計（{asOf(r.answerChecked)}）</span>
                  : r.fixed
                  ? <span className="source">各店舗の公式の料金表を集計した値</span>
                  : <span className="source">例：<Link href={`/facility/${r.example.slug}/`}>{r.example.name}</Link>（{asOf(r.example.fetched_at)}）</span>}
              </td>
              <td className="num">{r.modeN ? `${r.modeN}／${r.withFee}` : '—'}</td>
              <td className="num">{r.h24}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function GolfSubscriptionGuide() {
  const asof = asOf(GENERATED_AT)
  const faq = [
    {
      q: 'ゴルフのサブスクとは何ですか。',
      a: '決まった呼び方の定義はありませんが、月会費を払うと、その月は練習場の打席やレッスンを決められた範囲で使える料金の形を指して使われています。当サイトでは、屋内の練習施設・インドアゴルフスクールのうち、公式サイトに月会費の記載がある施設を集計しています。',
    },
    {
      q: '月会費だけで通えますか。',
      a: '施設によります。入会金・登録料のほか、ZEN GOLF RANGE の多くの店舗では打席料（55分 税込550円）、MIRA GOLF では打席料1回200円が月会費とは別にかかると公式サイトに記載されています。DOOR TO GOLF のように月4回・8回などの回数枠がある会員区分もあります。',
    },
    {
      q: '24時間使えるサブスク型の施設はありますか。',
      a: `あります。当サイトで月会費の記載がある屋内の施設${WITH_FEE.length.toLocaleString()}件のうち、公式サイトに24時間営業と明記されているのは${WITH_FEE.filter((f) => f.open_24h === true).length.toLocaleString()}件です。プランによって利用できる時間帯が決まっている場合があります（平日デイ・ナイトなど）。`,
    },
  ]
  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'ゴルフのサブスク（月額定額のインドアゴルフ）', url: '/guide/golf-subscription/' },
    ]),
    faqLd(faq),
  ]

  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs"><Link href="/">ホーム</Link> / ゴルフのサブスク（月額定額のインドアゴルフ）</nav>

      <section className="hero">
        <div className="kicker">Guide</div>
        <h1>ゴルフのサブスク：月額定額のインドアゴルフ{ROWS.length}ブランドの月会費の表記</h1>
        <p className="lead">
          ゴルフのサブスクは、月会費を払って屋内の練習施設やゴルフスクールに通う料金の形を指して使われています。
          当サイトに掲載している屋内の施設{INDOOR_ALL.length.toLocaleString()}件のうち、公式サイトに月会費の記載があるのは{WITH_FEE.length.toLocaleString()}件（{pct(WITH_FEE.length, INDOOR_ALL.length)}%）です。
        </p>
        <p className="lead">
          自分で打つ練習施設が{INDOOR_ROWS.length}ブランド、コーチのレッスンに通うスクールが{LESSON_ROWS.length}ブランドあり、ほかにブランドに属さない単独の施設が{INDEP.length}件です。
          以下は、当サイトが各施設の公式ページから集めた掲載データ（{asof}）をブランドごとに集計したものです。
        </p>
      </section>

      <h2>サブスク型の2つの形</h2>
      <dl className="spec">
        <div>
          <dt>練習し放題（屋内シミュレーションゴルフ）</dt>
          <dd>月会費で打席を予約して自分で練習する形です。1回の利用時間（50分・90分など）や1日の予約回数に上限がある施設が多く、平日昼だけ・夜だけなど時間帯を限ったプランもあります。</dd>
        </div>
        <div>
          <dt>レッスンに通う（インドアゴルフスクール）</dt>
          <dd>月会費でコーチのレッスンを受ける形です。月2回・月4回などの回数制と、回数の上限がない通い放題があり、レッスンのない時間に打席を使えるかどうかは会員区分によって異なります。</dd>
        </div>
      </dl>

      <h2>練習し放題のブランド（{INDOOR_ROWS.length}ブランド）</h2>
      <Table list={INDOOR_ROWS} />

      <h2>レッスンに通うスクール（{LESSON_ROWS.length}ブランド）</h2>
      <Table list={LESSON_ROWS} />
      <p className="source">
        「月会費の表記」は、そのブランドの掲載店舗の中で最も多い月会費の表記を、公式の店舗ページの記載どおりに載せたものです（「例」の店舗の確認日）。
        マイゴル・ZEN GOLF RANGE・ラハゴルフ24 は店舗や会員区分ごとに金額が異なるため、各店舗の公式の料金表を集計した幅を載せています。
        店舗ごとに金額が異なるブランドがあるため、ほかの店舗の金額は各店舗のページをご確認ください。
        税込・税抜の別は公式の表記に従っており、表記がないものはそのまま載せています。
        「24時間営業の明記」は、公式サイトに24時間営業と記載がある掲載店舗の数です。
        月会費の記載がないブランド（チキンゴルフ・GOLFTEC など）は表に含めていません。
      </p>

      <h2>月会費のほかに確認しておきたい費用</h2>
      <ul>
        <li>入会金・登録料：多くのブランドで別途かかります。キャンペーンで無料になる店舗もあり、期間・条件は店舗ごとに異なります。</li>
        <li>打席料：ZEN GOLF RANGE（多くの店舗で55分 税込550円）、MIRA GOLF（1回200円）など、月会費とは別に1回ごとの打席料がかかるブランドがあります。</li>
        <li>回数枠：DOOR TO GOLF のライト会員（月4回枠）のように、月に使える回数が決まっている会員区分があります。</li>
        <li>利用できる店舗：SMART GOLF は公式サイトで会員の相互利用を案内しています。マイゴルは月額プランによって利用できる店舗が変わると公式サイトに記載があります。</li>
      </ul>

      <h2>目的別の探し方</h2>
      <div className="chips">
        <Link href="/feature/open-24h/">24時間営業の施設</Link>
        <Link href="/feature/private-room/">個室で打てる施設</Link>
        <Link href="/lesson/beginner/">初心者向けのレッスン選び（スクールの体験料金）</Link>
        <Link href="/guide/indoor-golf/">インドアゴルフとは（施設の3つの形）</Link>
        <Link href="/brand/">ブランドから探す</Link>
      </div>

      <h2>よくある質問</h2>
      <dl className="spec">
        {faq.map((x) => (
          <div key={x.q}><dt>{x.q}</dt><dd>{x.a}</dd></div>
        ))}
      </dl>

      <p className="source">
        当サイトは口コミ・評価点を掲載していません。順位付けは行っていません。
        月会費・キャンペーンは変更される場合がありますので、ご利用前に公式サイトにてご確認ください。
      </p>
    </main>
  )
}
