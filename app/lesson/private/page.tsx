import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { JsonLd, breadcrumb, faqLd } from '../../../lib/seo'
import { OPEN_FACILITIES } from '../../../lib/data'
import { ymd } from '../../../lib/rizap'
import data from '../../../data/kwexp/private-lessons.json'

// 2026-11-25 kwexp「ゴルフレッスン マンツーマン」（aramakijake 月800）。
// 公式サイトに1対1のレッスンの記載があり、料金をテキストで確認できた施設だけを並べる（data/kwexp/private-lessons.json）。

const ROWS = data.rows
const N = ROWS.length
const LESSON = OPEN_FACILITIES.filter((f) => f.segment === 'lesson')

export const metadata: Metadata = {
  title: `ゴルフのマンツーマンレッスン｜公式で確認した${N}施設の1回の時間と料金`,
  description:
    `マンツーマン（1対1）のゴルフレッスンを、公式サイトで料金を確認できた${N}施設（GOLFTEC・ライザップゴルフ・ガントゴルフ千里中央店ほか）で比較。` +
    `1回の時間（30分・50分）、料金の形（回数パック・コース・月額・チケット）、1回あたりの金額と体験の料金を掲載しています。`,
  ...pageUrlMeta('/lesson/private/'),
}

export default function PrivateLessonPage() {
  const faq = [
    {
      q: 'マンツーマンのゴルフレッスンは1回いくらですか。',
      a: `当サイトで確認した${N}施設では、1回あたり6,600円（ガントゴルフ千里中央店の56回券・30分）から23,925円（ライザップゴルフの16回コース・50分）まで幅があります。1回の時間が30分と50分の施設があるため、時間をそろえて比べることをおすすめします。`,
    },
    {
      q: 'グループレッスンとの違いは何ですか。',
      a: 'マンツーマンはコーチ1人に受講者1人で、レッスンの時間をすべて自分の課題に使えます。豊洲ゴルフベースの通常のレッスンは最多3名のグループで、1人で受ける場合は追加料金のプライベートレッスン（50分 11,000円）になると公式サイトに記載があります。',
    },
    {
      q: '入会金や月会費はかかりますか。',
      a: 'ブランドによって異なります。GOLFTEC は入会金・会費・打席利用料がかからないと公式サイトに記載があり、ライザップゴルフはコース料金とは別に入会金 税込55,000円がかかります。',
    },
  ]
  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'ゴルフのマンツーマンレッスン', url: '/lesson/private/' },
    ]),
    faqLd(faq),
  ]

  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs"><Link href="/">ホーム</Link> / ゴルフのマンツーマンレッスン</nav>

      <section className="hero">
        <div className="kicker">Lesson</div>
        <h1>ゴルフのマンツーマンレッスン：公式で確認した{N}施設の1回の時間と料金</h1>
        <p className="lead">
          マンツーマンのゴルフレッスンは、1回あたり6,600円から23,925円まで幅があります（当サイトで確認した{N}施設・1回の時間は30分・50分など）。
          料金の形は、回数をまとめて買うパック・回数券、期間を決めたコース、月額の回数制に分かれます。
        </p>
        <p className="lead">
          掲載しているのは、公式サイトにマンツーマン・プライベート・パーソナルなど1対1のレッスンの記載があり、料金をテキストで確認できた施設です。
          1回あたりの金額は、公式に記載があるものはそのまま、ないものは公式の総額を回数で割って当サイトが計算しています。
        </p>
      </section>

      <h2>施設別のマンツーマンレッスンの料金</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr><th>施設</th><th>レッスンの形（公式の表記）</th><th>1回の時間</th><th>料金</th><th>1回あたり</th><th>体験</th></tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.name}>
                <td><Link href={r.href}>{r.name}</Link>（{r.count_label}）</td>
                <td>{r.term}</td>
                <td>{r.minutes}</td>
                <td>{r.fee}（<a href={r.url} target="_blank" rel="noopener noreferrer">出典</a>・{ymd(r.checked)}確認）</td>
                <td>{r.per ?? '計算できません'}</td>
                <td>{r.trial}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        金額は各公式サイトの記載どおりで、税込・税抜の別も公式の表記に従っています。キャンペーン価格は含めていません。
        1回あたりの金額は入会金を含まず、円未満を切り捨てています。料金は変更される場合がありますので、ご利用前に公式サイトにてご確認ください。
      </p>

      <h2>比べるときに確認したい項目</h2>
      <dl className="spec">
        <div>
          <dt>1回の時間</dt>
          <dd>GOLFTEC とガントゴルフ千里中央店は1回30分、ライザップゴルフ・JIN-golf・豊洲ゴルフベース・INDOOR GOLF GARDEN 6 ASAKUSA は1回50分です。1回あたりの金額は時間をそろえて比べる必要があります。</dd>
        </div>
        <div>
          <dt>有効期限</dt>
          <dd>GOLFTEC の10回パックは有効3か月、25回・40回パックは12か月と公式サイトに記載があります。ライザップゴルフは全16回が2ヶ月のコースです。</dd>
        </div>
        <div>
          <dt>レッスン以外の練習</dt>
          <dd>ライザップゴルフは会員が空いているレッスンルームを1日1枠（50分）まで自主練習に使えます。GOLFTEC の自主練習（プラクティス）は都度利用 税込3,300円です。</dd>
        </div>
      </dl>

      <h2>ほかのレッスンの探し方</h2>
      <p>
        マンツーマン以外の形（セミパーソナル・月会費制のスクール）も含めた体験料金の比較は<Link href="/lesson/beginner/">ゴルフ初心者のレッスン選び</Link>に、
        月会費で通うスクールの料金の表記は<Link href="/guide/golf-subscription/">ゴルフのサブスク（月額定額のインドアゴルフ）</Link>にまとめています。
        当サイトに掲載しているシミュレーター併設のスクールは{LESSON.length}店舗です。
      </p>

      <h2>よくある質問</h2>
      <dl className="spec">
        {faq.map((x) => (
          <div key={x.q}><dt>{x.q}</dt><dd>{x.a}</dd></div>
        ))}
      </dl>

      <p className="source">
        当サイトは口コミ・評価点を掲載していません。順位付けは行っていません。
        掲載内容は各行に記載した確認日時点の公式サイトの記載にもとづいています。
      </p>
    </main>
  )
}
