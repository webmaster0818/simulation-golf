import { pageUrlMeta } from '../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { JsonLd, breadcrumb, faqLd } from '../../../lib/seo'
import { RIZAP, RIZAP_AREAS, perLesson, ymd } from '../../../lib/rizap'
import { yen } from '../../../lib/brand-facts'

// 2026-11-16 kwexp「ライザップゴルフ 料金」（aramakijake 月1,280）。施設データベースには入れていない（lib/rizap.ts の注記）
const R = RIZAP
const c16 = R.course_fees[0]

export const metadata: Metadata = {
  title: `ライザップゴルフ（RIZAP GOLF）の料金｜16回 税込${yen(c16.inc)}〜・入会金${yen(R.admission_inc)}・全${R.stores.length}店舗`,
  description:
    `ライザップゴルフの料金を公式サイトの掲載どおりに掲載。通常コースは全16回（2ヶ月）税込${yen(c16.inc)}〜、別途入会金 税込${yen(R.admission_inc)}。` +
    `1回あたりの金額、PRIMEプランの初期費用、体験（ゴルフ力診断 税込${yen(R.diagnosis.inc)}）、全${R.stores.length}店舗の営業時間と所在地も掲載しています。`,
  ...pageUrlMeta('/brand/rizapgolf/'),
}

export default function RizapGolfPage() {
  const checked = ymd(R.checked)
  const rows = R.course_fees.map((c) => ({
    ...c,
    per: perLesson(c.inc, c.lessons),
    perWithAdm: perLesson(c.inc + R.admission_inc, c.lessons),
  }))
  const faq = [
    {
      q: 'ライザップゴルフの料金はいくらですか。',
      a: `公式サイトの店舗ページでは、通常コースが全16回 税込${yen(c16.inc)}・全24回 税込${yen(R.course_fees[1].inc)}・全32回 税込${yen(R.course_fees[2].inc)}と案内されています。いずれのコースも別途 入会金 税込${yen(R.admission_inc)}がかかります（${checked}確認）。`,
    },
    {
      q: '月額制ですか。',
      a: '公式サイトの料金はレッスン回数ごとのコース料金で、通い放題の月会費の形ではありません。分割払いの案内があります。',
    },
    {
      q: '体験はできますか。',
      a: `初回限定の「${R.diagnosis.text}」が案内されています。`,
    },
  ]
  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'ブランドから探す', url: '/brand/' },
      { name: 'ライザップゴルフ', url: '/brand/rizapgolf/' },
    ]),
    faqLd(faq),
  ]
  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/brand/">ブランドから探す</Link> / ライザップゴルフ
      </nav>

      <section className="hero">
        <div className="kicker">rizapgolf</div>
        <h1>ライザップゴルフ（RIZAP GOLF）の料金</h1>
        <p className="lead">
          ライザップゴルフの通常コースは、全16回（2ヶ月）で税込{yen(c16.inc)}からです。
          別途、入会金 税込{yen(R.admission_inc)}がかかるため、16回コースの支払総額は税込{yen(c16.inc + R.admission_inc)}です。
          1回（{R.lesson_minutes}分）あたりに直すと、入会金を含めて約{yen(rows[0].perWithAdm)}です（当サイトの計算）。
        </p>
        <p className="lead">
          金額は{checked}に公式サイトの料金ページと全{R.stores.length}店舗の店舗ページで確認したもので、店舗による違いはありませんでした。
        </p>
      </section>

      <h2>コース料金と1回あたりの金額</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr><th>コース</th><th>コース料金（税込）</th><th>1回あたり（税込）</th><th>入会金を含む1回あたり（税込）</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.lessons}>
                <td>全{r.lessons}回</td>
                <td className="num">{yen(r.inc)}<br /><span className="sub">（税抜{yen(r.ex)}）</span></td>
                <td className="num">約{yen(r.per)}</td>
                <td className="num">約{yen(r.perWithAdm)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        コース料金は公式の店舗ページ「プラン・料金」の通常コース（飛距離アッププログラムも同額）の掲載額です。
        1回あたりの金額は、当サイトがコース料金（と入会金 税込{yen(R.admission_inc)}）を回数で割って円未満を切り捨てたものです。
        公式サイトでは16回コース・入会金込みの単価を「27,362円(税込)/回」と案内しており、当サイトの計算と一致します。
        回数が増えるほど1回あたりの金額は下がります。
      </p>

      <h2>初期費用・プランの違い</h2>
      <dl className="spec">
        <div><dt>入会金</dt><dd>税込{yen(R.admission_inc)}（50,000円＋税）。いずれのコースにもかかります</dd></div>
        <div><dt>PRIMEプラン</dt><dd>{R.prime.note}。公式サイトでは「長期コミット」のプランとして、PRIMEプラン契約者の平均継続期間26ヶ月（2022年度実績）が示されています</dd></div>
        <div><dt>分割払い</dt><dd>{R.installment}</dd></div>
        <div><dt>返金保証</dt><dd>{R.refund}</dd></div>
        <div><dt>体験</dt><dd>{R.diagnosis.text}</dd></div>
      </dl>
      <p className="source">
        出典：<a href={R.plan_url} target="_blank" rel="noopener noreferrer">ライザップゴルフ公式「プラン・料金」</a>（{checked}確認）。
        料金・条件は変更される場合がありますので、ご利用前に公式サイトにてご確認ください。
      </p>

      <h2>料金に含まれるもの（公式サイトの案内）</h2>
      <ul>
        <li>{R.equipment}でのマンツーマンレッスン（1回{R.lesson_minutes}分）</li>
        <li>{R.self_practice}</li>
        <li>{R.rental}</li>
        <li>レッスン外のオンラインでのアドバイス・レッスンのレビュー動画</li>
      </ul>

      <h2>ほかのシミュレーター併設スクールとの料金の形の違い</h2>
      <p>
        当サイトに掲載しているステップゴルフ・ZEN GOLF・インザゴルフなどのスクールは、月会費を払って通う形です。
        ライザップゴルフは回数を決めて申し込むコース制で、料金の比べ方が異なります。
        スクールごとの体験料金と料金の形は、<Link href="/lesson/beginner/">ゴルフ初心者のレッスン選び（スクール9ブランドの体験と料金の形）</Link>にまとめています。
      </p>

      <h2>店舗一覧（全{R.stores.length}店舗）</h2>
      <p>{R.official_count.text}（<a href={R.official_count.url} target="_blank" rel="noopener noreferrer">出典</a>）。各店舗の公式の店舗ページで確認した内容です。</p>
      <div className="tablewrap">
        <table>
          <thead><tr><th>店舗</th><th>所在地</th><th>営業時間</th><th>最寄り駅（公式の記載の1行目）</th></tr></thead>
          <tbody>
            {R.stores.map((s) => (
              <tr key={s.id}>
                <td>
                  {s.area ? <Link href={`/brand/rizapgolf/${s.area}/`}>{s.name}</Link> : s.name}
                  <br /><a className="sub" href={s.source_url} target="_blank" rel="noopener noreferrer">公式の店舗ページ</a>
                </td>
                <td>〒{s.zip} {s.address}</td>
                <td>{s.hours}</td>
                <td>{s.stations[0]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        営業時間は、公式サイトに「従業員の稼働状況により、営業時間が短縮となる場合があります」と記載されています。
        立川店のみ営業時間が異なります（平日祝 10:00～23:00、土日 8:00～19:00）。
      </p>

      <h2>地域別のページ</h2>
      <div className="chips">
        {Object.entries(RIZAP_AREAS).map(([k, a]) => (
          <Link key={k} href={`/brand/rizapgolf/${k}/`}>ライザップゴルフ {a.label}</Link>
        ))}
      </div>

      <h2>よくある質問</h2>
      <dl className="spec">
        {faq.map((x) => (
          <div key={x.q}><dt>{x.q}</dt><dd>{x.a}</dd></div>
        ))}
      </dl>

      <p className="source">
        当サイトは口コミ・評価点を掲載していません。掲載内容は{checked}時点の公式サイトの記載にもとづいています。
        ライザップゴルフの店舗は、当サイトの施設データベース（エリア・条件からの検索）には現在含めていません。
      </p>
    </main>
  )
}
