import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, PREF_SLUG, SLUG_PREF, activePrefs, byPref, wardOf, asOf, GENERATED_AT,
  FACILITIES,
  cities as cityPagesOf,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'
import { JsonLd, breadcrumb, itemListLd } from '../../../lib/seo'

type Params = { pref: string }

export function generateStaticParams(): Params[] {
  return activePrefs().map((p) => ({ pref: PREF_SLUG[p] }))
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { pref: slug } = await params
  const pref = SLUG_PREF[slug]
  const fs = byPref(pref)
  const n24 = fs.filter((f) => f.open_24h).length
  const title = `${pref}のシミュレーションゴルフ${fs.length}施設を比較｜個室・24時間・打席数`
  return {
    title,
    description:
      `${pref}のシミュレーションゴルフ施設${fs.length}件を、公式サイトの情報で比較。` +
      `24時間営業${n24}件。個室の有無・打席数・駐車場・弾道計測の機材まで、出典つきで掲載しています。`,
    alternates: { canonical: `${SITE.origin}/area/${slug}/` },
  }
}

export default async function AreaPage({ params }: { params: Promise<Params> }) {
  const { pref: slug } = await params
  const pref = SLUG_PREF[slug]
  const fs = byPref(pref)
  const indoor = fs.filter((f) => f.segment === 'indoor')
  const range = fs.filter((f) => f.segment === 'range')
  const lesson = fs.filter((f) => f.segment === 'lesson')
  const n24 = fs.filter((f) => f.open_24h).length
  const nPrivate = fs.filter((f) => f.private_room === true || /個室/.test(f.bays ?? '')).length

  // 市区町村ごとの件数。エリア内のどこに集まっているかを、データのまま出す。
  const cities = new Map<string, number>()
  for (const f of fs) {
    const c = wardOf(f)
    if (c) cities.set(c, (cities.get(c) ?? 0) + 1)
  }
  const cityList = [...cities.entries()].sort((a, b) => b[1] - a[1])

  const others = activePrefs().filter((p) => p !== pref)
  const cityPages = cityPagesOf().filter((x) => x.pref === pref)
  // ⚠️ open:false（オープン準備中）の施設もページは作られ sitemap にも載るのに、
  //    一覧は営業中だけなので**どこからも辿れない**状態だった（3件）。
  //    営業中と混ぜず、別枠で出して繋ぐ。
  const soon = FACILITIES.filter((f) => !f.open && f.pref === pref)

  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'エリアから探す', url: '/area/' },
      { name: pref, url: `/area/${slug}/` },
    ]),
    itemListLd(`${pref}のシミュレーションゴルフ施設`, fs.map((f) => `/facility/${f.slug}/`)),
  ]
  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/area/">エリアから探す</Link> / {pref}
      </nav>

      <section className="hero">
        <div className="kicker">{slug}</div>
        <h1>{pref}のシミュレーションゴルフ{fs.length}施設</h1>
        <p className="lead">
          {pref}で公式サイトが情報を公開している施設を、すべて並べています。
          口コミによる順位づけはしていません。並び順は屋内施設・スクール・練習場の順です。
        </p>
      </section>

      <div className="stats">
        <div><div className="v">{fs.length}</div><div className="k">掲載施設</div></div>
        <div><div className="v">{indoor.length}</div><div className="k">屋内シミュレーションゴルフ</div></div>
        <div><div className="v">{n24}</div><div className="k">24時間営業</div></div>
        <div><div className="v">{nPrivate}</div><div className="k">個室で打てる</div></div>
      </div>
      <p className="source">{asOf(GENERATED_AT)}の公式サイト掲載内容にもとづきます。</p>

      {cityList.length > 1 && (
        <>
          <h2>{pref}のどこに多いか</h2>
          <div className="tablewrap">
            <table>
              <thead>
                <tr><th>市区町村</th><th>施設数</th><th>内訳</th></tr>
              </thead>
              <tbody>
                {cityList.map(([c, n]) => {
                  const inC = fs.filter((f) => wardOf(f) === c)
                  // その市区町村のページがあるならリンクする（3施設以上だけ作っている）
                  const page = cityPages.find((x) => x.city === c)
                  return (
                    <tr key={c}>
                      <td>
                        {page
                          ? <Link href={`/area/${slug}/${page.slug}/`}>{c}</Link>
                          : c}
                      </td>
                      <td className="num">{n}</td>
                      <td>
                        {inC.map((f, i) => (
                          <span key={f.slug}>
                            {i > 0 && '・'}
                            <Link href={`/facility/${f.slug}/`}>{f.name}</Link>
                          </span>
                        ))}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {indoor.length > 0 && (
        <>
          <h2>屋内シミュレーションゴルフ（{indoor.length}件）</h2>
          <div className="cards">
            {indoor.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
        </>
      )}

      {lesson.length > 0 && (
        <>
          <h2>コーチに教わるインドアゴルフスクール（{lesson.length}件）</h2>
          <p>
            完全予約制でコーチが付き、月会費で通うスクールです。弾道測定機は置かれていますが、
            好きな時間に自分で打ちに行く施設とは使い方が違うので、分けて掲載しています。
          </p>
          <div className="cards">
            {lesson.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
        </>
      )}

      {range.length > 0 && (
        <>
          <h2>弾道計測つきの練習場（{range.length}件）</h2>
          <p>
            屋外の打ちっぱなし練習場に、打球を計測して画面に軌跡を出す設備（トップトレーサー・レンジ）が
            入っている施設です。屋内の個室とは体験が違うので、分けて掲載しています。
            {range.filter((f) => f.usage_fee === '無料').length > 0 && (
              <>
                {' '}このうち
                <strong>{range.filter((f) => f.usage_fee === '無料').length}件は計測の利用料が無料</strong>
                と公表されています（通常の打席料は別途かかります）。
              </>
            )}
          </p>
          <div className="cards">
            {range.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
        </>
      )}

      {soon.length > 0 && (
        <>
          <h2>{pref}でオープン準備中（{soon.length}件）</h2>
          <p>
            公式サイトが開業を告知している施設です。まだ営業していないため、
            上の掲載件数には含めていません。
          </p>
          <ul className="chips">
            {soon.map((f) => (
              <li key={f.slug}>
                <Link href={`/facility/${f.slug}/`}>{f.name}</Link>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2>ほかのエリア</h2>
      <div className="chips">
        {others.map((p) => (
          <Link key={p} href={`/area/${PREF_SLUG[p]}/`}>
            {p}<span className="c">{byPref(p).length}</span>
          </Link>
        ))}
      </div>
    </main>
  )
}
