import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, REGIONS, PREF_SLUG, OPEN_FACILITIES, byPref, activePrefs, brands,
  FEATURES, byFeature, GENERATED_AT, asOf,
} from '../lib/data'
import FacilityCard from '../components/FacilityCard'

export const metadata: Metadata = {
  title: `${SITE.name}｜全国のシミュレーションゴルフを公式情報で比較`,
  description: SITE.description,
  alternates: { canonical: `${SITE.origin}/` },
}

export default function Home() {
  const all = OPEN_FACILITIES
  const indoor = all.filter((f) => f.segment === 'indoor')
  const range = all.filter((f) => f.segment === 'range')
  const prefs = activePrefs()
  const ranked = prefs
    .map((p) => ({ pref: p, n: byPref(p).length }))
    .sort((a, b) => b.n - a.n)

  return (
    <main className="wrap">
      <section className="hero">
        <svg className="trace-arc" viewBox="0 0 460 220" aria-hidden="true">
          {/* 打ち出しから着地までの軌跡。このサイトが扱う「弾道計測」そのもの */}
          <path d="M8 206 C 120 -8, 300 12, 452 150" fill="none" stroke="#c4f542"
            strokeWidth="1.6" strokeDasharray="4 7" strokeLinecap="round" />
          <circle cx="8" cy="206" r="3.5" fill="#c4f542" />
          <circle cx="452" cy="150" r="5" fill="none" stroke="#c4f542" strokeWidth="1.4" />
        </svg>
        <div className="kicker">Simulation Golf / Japan</div>
        <h1>
          シミュレーションゴルフの施設を、
          <br />
          公式サイトの情報だけで比べる。
        </h1>
        <p className="lead">
          屋内のシミュレーションゴルフ施設と、弾道計測つきの練習場を、
          個室の有無・打席数・営業時間・駐車場まで並べて比較できます。
          口コミや評価は載せません。載せているのは、各施設の公式サイトに書かれていることだけです。
        </p>
      </section>

      <div className="stats">
        <div>
          <div className="v">{all.length}</div>
          <div className="k">掲載施設</div>
        </div>
        <div>
          <div className="v">{indoor.length}</div>
          <div className="k">屋内シミュレーションゴルフ</div>
        </div>
        <div>
          <div className="v">{range.length}</div>
          <div className="k">弾道計測つき練習場</div>
        </div>
        <div>
          <div className="v">{prefs.length}</div>
          <div className="k">掲載のある都道府県</div>
        </div>
      </div>
      <p className="source">
        {asOf(GENERATED_AT)}の公式サイト掲載内容にもとづきます。
        施設ごとの取得元URLと取得日は、各施設ページに記載しています。
      </p>

      <h2>条件で絞る</h2>
      <div className="chips">
        {FEATURES.map((f) => (
          <Link key={f.slug} href={`/feature/${f.slug}/`}>
            {f.label}
            <span className="c">{byFeature(f.slug).length}</span>
          </Link>
        ))}
      </div>

      <h2>エリアから探す</h2>
      {REGIONS.map((r) => {
        const has = r.prefs.filter((p) => prefs.includes(p))
        if (!has.length) return null
        return (
          <div key={r.name}>
            <h3>{r.name}</h3>
            <div className="chips">
              {has.map((p) => (
                <Link key={p} href={`/area/${PREF_SLUG[p]}/`}>
                  {p}
                  <span className="c">{byPref(p).length}</span>
                </Link>
              ))}
            </div>
          </div>
        )
      })}

      <h2>掲載の多いエリア</h2>
      <div className="cards">
        {ranked.slice(0, 6).flatMap((r) => byPref(r.pref).slice(0, 1)).map((f) => (
          <FacilityCard key={f.slug} f={f} />
        ))}
      </div>
      <p className="source">
        各エリアの全施設は{' '}
        {ranked.slice(0, 6).map((r, i) => (
          <span key={r.pref}>
            {i > 0 && '・'}
            <Link href={`/area/${PREF_SLUG[r.pref]}/`}>
              {r.pref}（{r.n}件）
            </Link>
          </span>
        ))}{' '}
        のページで確認できます。
      </p>

      <h2>ブランドから探す</h2>
      <div className="chips">
        {brands().map((b) => (
          <Link key={b.slug} href={`/brand/${b.slug}/`}>
            {b.name}
            <span className="c">{b.count}</span>
          </Link>
        ))}
      </div>

      <h2>このサイトの方針</h2>
      <div className="verdict">
        <span className="tag">Policy</span>
        <p>
          施設の情報は、公式サイトに書かれている内容だけを載せています。
          公式サイトに記載が無い項目は、推測で埋めずに「公式サイトに記載なし」と表示します。
        </p>
        <p>
          営業時間や料金は変わります。掲載内容には取得日を添えているので、
          利用前には必ずリンク先の公式サイトで最新の内容を確認してください。
        </p>
        <p style={{ marginBottom: 0 }}>
          <Link href="/data/">掲載データについて詳しく見る</Link>
        </p>
      </div>
    </main>
  )
}
