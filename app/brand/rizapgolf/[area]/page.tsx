import { pageUrlMeta } from '../../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { JsonLd, breadcrumb } from '../../../../lib/seo'
import { OPEN_FACILITIES, cityOf, wardOf } from '../../../../lib/data'
import { RIZAP, RIZAP_AREAS, ymd } from '../../../../lib/rizap'
import { yen } from '../../../../lib/brand-facts'

// 2026-11-16 kwexp「ライザップゴルフ 名古屋／京都／銀座」。店舗の値は公式の店舗ページ（lib/rizap.ts）
type Params = { area: string }
const R = RIZAP
const c16 = R.course_fees[0]

export function generateStaticParams(): Params[] {
  return Object.keys(RIZAP_AREAS).map((area) => ({ area }))
}

const storesOf = (area: string) => R.stores.filter((s) => s.area === area)
const shortName = (n: string) => n.replace(/^RIZAP GOLF /, '')

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { area } = await params
  const a = RIZAP_AREAS[area]
  if (!a) return {}
  const ss = storesOf(area)
  const names = ss.map((s) => shortName(s.name)).join('・')
  return {
    title: `ライザップゴルフ${a.label}（${names}）の料金・営業時間・アクセス`,
    description:
      `ライザップゴルフ${names}の所在地・営業時間・最寄り駅・駐車場を公式の店舗ページどおりに掲載。` +
      `料金は全16回 税込${yen(c16.inc)}〜（別途入会金 税込${yen(R.admission_inc)}）。` +
      `${a.city}で当サイトに掲載しているほかのシミュレーションゴルフ施設も一覧にしています。`,
    ...pageUrlMeta(`/brand/rizapgolf/${area}/`),
  }
}

export default async function RizapAreaPage({ params }: { params: Promise<Params> }) {
  const { area } = await params
  const a = RIZAP_AREAS[area]
  if (!a) return null
  const ss = storesOf(area)
  const checked = ymd(R.checked)
  // 同じ市（銀座は中央区）で当サイトに掲載している施設。スクール（lesson）を先に
  const near = OPEN_FACILITIES
    .filter((f) => f.pref === a.pref && cityOf(f) === a.city)
    .sort((x, y) => (x.segment === 'lesson' ? 0 : 1) - (y.segment === 'lesson' ? 0 : 1) || (wardOf(x) ?? '').localeCompare(wardOf(y) ?? ''))
  const nLesson = near.filter((f) => f.segment === 'lesson').length
  // 同じ都府県のほかの RIZAP GOLF 店舗
  const samePref = R.stores.filter((s) => s.address.startsWith(a.pref) && s.area !== area)

  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'ブランドから探す', url: '/brand/' },
      { name: 'ライザップゴルフ', url: '/brand/rizapgolf/' },
      { name: a.label, url: `/brand/rizapgolf/${area}/` },
    ]),
  ]
  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/brand/">ブランドから探す</Link> /{' '}
        <Link href="/brand/rizapgolf/">ライザップゴルフ</Link> / {a.label}
      </nav>

      <section className="hero">
        <div className="kicker">rizapgolf / {area}</div>
        <h1>ライザップゴルフ {a.label}（{ss.map((s) => shortName(s.name)).join('・')}）</h1>
        <p className="lead">
          {a.label}のライザップゴルフは{ss.length}店舗です（{checked}時点の公式の店舗一覧）。
          {ss.map((s) => `${shortName(s.name)}は${s.stations[0].replace(/\s+/g, ' ')}`).join('、')}です。
          料金は全店共通で、通常コース全16回（2ヶ月）税込{yen(c16.inc)}〜、別途入会金 税込{yen(R.admission_inc)}です。
        </p>
      </section>

      {ss.map((s) => (
        <section key={s.id}>
          <h2>{s.name}</h2>
          <dl className="spec">
            <div><dt>所在地</dt><dd>〒{s.zip} {s.address}</dd></div>
            <div><dt>営業時間</dt><dd>{s.hours}{s.hours_note ? `（${s.hours_note.replace(/^※/, '')}）` : ''}</dd></div>
            <div><dt>最寄り駅</dt><dd>{s.stations.join('／')}</dd></div>
            <div>
              <dt>駐車場</dt>
              {s.parking ? <dd>{s.parking}</dd> : <dd className="none">公式サイトに記載なし</dd>}
            </div>
            <div><dt>設備</dt><dd>{R.equipment}</dd></div>
            <div><dt>料金</dt><dd>通常コース 全16回 税込{yen(R.course_fees[0].inc)}／全24回 税込{yen(R.course_fees[1].inc)}／全32回 税込{yen(R.course_fees[2].inc)}（別途 入会金 税込{yen(R.admission_inc)}）</dd></div>
            <div><dt>体験</dt><dd>{R.diagnosis.text}</dd></div>
          </dl>
          <p className="source">
            出典：<a href={s.source_url} target="_blank" rel="noopener noreferrer">{s.name}（公式の店舗ページ）</a>（{ymd(s.fetched_at)}確認）。
            「記載なし」は公式サイトに記載がないことを示しており、設備がないことを示すものではありません。
          </p>
        </section>
      ))}

      <p>
        1回あたりの金額・PRIMEプランの初期費用・返金保証の条件は、<Link href="/brand/rizapgolf/">ライザップゴルフの料金</Link>にまとめています。
      </p>

      {samePref.length > 0 && (
        <>
          <h2>{a.pref}のほかのライザップゴルフ（{samePref.length}店舗）</h2>
          <div className="tablewrap">
            <table>
              <thead><tr><th>店舗</th><th>所在地</th><th>最寄り駅（公式の記載の1行目）</th></tr></thead>
              <tbody>
                {samePref.map((s) => (
                  <tr key={s.id}>
                    <td>{s.area ? <Link href={`/brand/rizapgolf/${s.area}/`}>{s.name}</Link> : <a href={s.source_url} target="_blank" rel="noopener noreferrer">{s.name}</a>}</td>
                    <td>{s.address}</td>
                    <td>{s.stations[0]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <h2>{a.city}のほかのシミュレーションゴルフ（当サイト掲載 {near.length}施設）</h2>
      <p>
        当サイトに掲載している{a.city}の施設は{near.length}件で、そのうちレッスンを行うスクールは{nLesson}件です
        （ライザップゴルフは含みません）。スクールを先に並べています。
      </p>
      <div className="tablewrap">
        <table>
          <thead><tr><th>施設</th><th>区・市</th><th>種類</th><th>営業時間</th></tr></thead>
          <tbody>
            {near.map((f) => (
              <tr key={f.slug}>
                <td><Link href={`/facility/${f.slug}/`}>{f.name}</Link></td>
                <td>{wardOf(f)}</td>
                <td>{f.segment === 'lesson' ? 'スクール' : f.segment === 'range' ? '練習場' : '屋内シミュレーションゴルフ'}</td>
                <td>{f.hours ?? '公式サイトに記載なし'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {a.areaLink && <p className="source"><Link href={a.areaLink.href}>{a.areaLink.label}</Link></p>}

      <h2>ほかの地域のライザップゴルフ</h2>
      <div className="chips">
        {Object.entries(RIZAP_AREAS).filter(([k]) => k !== area).map(([k, x]) => (
          <Link key={k} href={`/brand/rizapgolf/${k}/`}>ライザップゴルフ {x.label}</Link>
        ))}
        <Link href="/brand/rizapgolf/">全{R.stores.length}店舗の一覧</Link>
      </div>

      <p className="source">
        当サイトは口コミ・評価点を掲載していません。掲載内容は{checked}時点の公式サイトの記載にもとづいています。
        ご利用前に、公式サイトにて最新情報をご確認ください。
      </p>
    </main>
  )
}
