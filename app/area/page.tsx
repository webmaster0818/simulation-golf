import type { Metadata } from 'next'
import Link from 'next/link'
import { SITE, REGIONS, PREF_SLUG, activePrefs, byPref, OPEN_FACILITIES } from '../../lib/data'

export const metadata: Metadata = {
  title: '都道府県から探す｜シミュレーションゴルフの施設一覧',
  description:
    '全国のシミュレーションゴルフ施設を都道府県から探せます。掲載のある都道府県と施設数の一覧です。',
  alternates: { canonical: `${SITE.origin}/area/` },
}

export default function AreaIndex() {
  const prefs = activePrefs()
  return (
    <main className="wrap">
      <nav className="crumbs"><Link href="/">ホーム</Link> / エリアから探す</nav>
      <section className="hero">
        <div className="kicker">Area</div>
        <h1>都道府県から探す</h1>
        <p className="lead">
          掲載しているのは、公式サイトで施設情報を公開している{OPEN_FACILITIES.length}件です。
          掲載が0件の都道府県はページを作っていません（中身の無いページを置かないため）。
        </p>
      </section>

      {REGIONS.map((r) => {
        const has = r.prefs.filter((p) => prefs.includes(p))
        const none = r.prefs.filter((p) => !prefs.includes(p))
        if (!has.length) return null
        return (
          <div key={r.name}>
            <h2>{r.name}</h2>
            <div className="chips">
              {has.map((p) => (
                <Link key={p} href={`/area/${PREF_SLUG[p]}/`}>
                  {p}<span className="c">{byPref(p).length}</span>
                </Link>
              ))}
            </div>
            {none.length > 0 && (
              <p className="source">
                掲載なし：{none.join('・')}（公式サイトで情報を公開している施設が見つかっていません）
              </p>
            )}
          </div>
        )
      })}
    </main>
  )
}
