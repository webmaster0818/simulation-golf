import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, PREF_SLUG, SLUG_PREF, activePrefs, byPref, cityOf, asOf, GENERATED_AT,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'

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
  const n24 = fs.filter((f) => f.open_24h).length
  const nPrivate = fs.filter((f) => f.private_room === true || /個室/.test(f.bays ?? '')).length

  // 市区町村ごとの件数。エリア内のどこに集まっているかを、データのまま出す。
  const cities = new Map<string, number>()
  for (const f of fs) {
    const c = cityOf(f)
    if (c) cities.set(c, (cities.get(c) ?? 0) + 1)
  }
  const cityList = [...cities.entries()].sort((a, b) => b[1] - a[1])

  const others = activePrefs().filter((p) => p !== pref)

  return (
    <main className="wrap">
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/area/">エリアから探す</Link> / {pref}
      </nav>

      <section className="hero">
        <div className="kicker">{slug}</div>
        <h1>{pref}のシミュレーションゴルフ{fs.length}施設</h1>
        <p className="lead">
          {pref}で公式サイトが情報を公開している施設を、すべて並べています。
          口コミによる順位づけはしていません。並び順は屋内施設・練習場の順です。
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
                  const inC = fs.filter((f) => cityOf(f) === c)
                  return (
                    <tr key={c}>
                      <td>{c}</td>
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
