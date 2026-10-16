import { pageUrlMeta } from '../../../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, PREF_SLUG, SLUG_PREF, cities, wardOf, byPref, asOf, GENERATED_AT, CITY_MIN, hasOwnParking,
} from '../../../../lib/data'
import { JsonLd, breadcrumb, itemListLd } from '../../../../lib/seo'
import FacilityCard from '../../../../components/FacilityCard'

type Params = { pref: string; city: string }

/**
 * 市区町村ページ。
 *
 * 検索は市区町村・駅の単位で来ているのに（GSC実測: 「小手指 ゴルフシミュレーター」
 * 「蕨 ゴルフシミュレーター」「御堂筋本町 24時間 インドアゴルフ」）、受け皿が
 * 都道府県までしか無かった。都道府県ページの順位は44〜77位。
 *
 * ⚠️ 1施設しかない市区町村は282ある。全部作ると施設ページの焼き直しになるので、
 *    3施設以上（= 比べられる）だけ作る。lib/data.ts の CITY_MIN。
 */
export function generateStaticParams(): Params[] {
  return cities().map((c) => ({ pref: PREF_SLUG[c.pref], city: c.slug }))
}

function find(prefSlug: string, citySlug: string) {
  const pref = SLUG_PREF[prefSlug]
  return cities().find((c) => c.pref === pref && c.slug === citySlug)
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { pref, city } = await params
  const c = find(pref, city)
  if (!c) return {}
  const n24 = c.items.filter((f) => f.open_24h).length
  return {
    title: `${c.city}のシミュレーションゴルフ${c.items.length}施設｜インドアゴルフ・ゴルフシミュレーター`,
    description:
      `${c.pref}${c.city}にあるシミュレーションゴルフ・インドアゴルフ${c.items.length}施設を、` +
      `公式サイトの情報で比較できます。${n24 > 0 ? `24時間営業は${n24}施設。` : ''}` +
      `打席数・個室の有無・駐車場・料金を、出典を明記して掲載しています。`,
    ...pageUrlMeta(`/area/${pref}/${city}/`),
  }
}

export default async function CityPage({ params }: { params: Promise<Params> }) {
  const { pref: prefSlug, city: citySlug } = await params
  const c = find(prefSlug, citySlug)
  if (!c) return null

  const fs = c.items
  const indoor = fs.filter((f) => f.segment === 'indoor')
  const lesson = fs.filter((f) => f.segment === 'lesson')
  const range = fs.filter((f) => f.segment === 'range')
  const n24 = fs.filter((f) => f.open_24h).length
  const nPrivate = fs.filter((f) => f.private_room === true || /個室/.test(f.bays ?? '')).length
  const nPark = fs.filter((f) => hasOwnParking(f)).length

  // 同じ都道府県にある、ページのある他の市区町村
  const siblings = cities().filter((x) => x.pref === c.pref && x.slug !== c.slug)
  // この市区町村に無い施設も含めた都道府県の全件数（「もっと広く探す」の導線に使う）
  const prefTotal = byPref(c.pref).length

  const ld = [
    breadcrumb([
      { name: 'ホーム', url: '/' },
      { name: 'エリアから探す', url: '/area/' },
      { name: c.pref, url: `/area/${prefSlug}/` },
      { name: c.city, url: `/area/${prefSlug}/${citySlug}/` },
    ]),
    itemListLd(`${c.pref}${c.city}のシミュレーションゴルフ施設`,
      fs.map((f) => `/facility/${f.slug}/`)),
  ]

  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs">
        <Link href="/">ホーム</Link> / <Link href="/area/">エリアから探す</Link> /{' '}
        <Link href={`/area/${prefSlug}/`}>{c.pref}</Link> / {c.city}
      </nav>

      <section className="hero">
        <div className="kicker">{citySlug}</div>
        <h1>{c.city}のシミュレーションゴルフ{fs.length}施設</h1>
        <p className="lead">
          {c.pref}{c.city}で、公式サイトに施設情報が公開されているシミュレーションゴルフ施設をすべて掲載しています。
          「シミュレーションゴルフ」「インドアゴルフ」「ゴルフシミュレーター」は同様の施設を指す名称のため、本ページではまとめて掲載しています。
          口コミ等による順位付けは行っていません。
        </p>
      </section>

      <div className="stats">
        <div><div className="v">{fs.length}</div><div className="k">掲載施設</div></div>
        <div><div className="v">{n24}</div><div className="k">24時間営業</div></div>
        <div><div className="v">{nPrivate}</div><div className="k">個室で打てる</div></div>
        <div><div className="v">{nPark}</div><div className="k">駐車場あり</div></div>
      </div>
      <p className="source">{asOf(GENERATED_AT)}の公式サイトの掲載内容にもとづいています。</p>

      <h2>{c.city}の施設一覧</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr><th>施設</th><th>住所</th><th>24時間</th><th>個室</th><th>駐車場</th></tr>
          </thead>
          <tbody>
            {fs.map((f) => (
              <tr key={f.slug}>
                <td><Link href={`/facility/${f.slug}/`}>{f.name}</Link></td>
                <td>{f.address ?? '—'}</td>
                {/* ⚠️ 値が無いのは「無い」ではなく「公式に記載が無い」。記号を分ける */}
                <td className="num">{f.open_24h === true ? '○' : f.open_24h === false ? '—' : '?'}</td>
                <td className="num">
                  {f.private_room === true || /個室/.test(f.bays ?? '') ? '○' : '?'}
                </td>
                <td className="num">{hasOwnParking(f) ? '○' : '?'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        ○：公式サイトに記載あり　—：公式サイトに「なし」と記載　?：公式サイトに記載なし
        （「?」は設備がないことを示すものではありません）。
      </p>

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
          <h2>インドアゴルフスクール（{lesson.length}件）</h2>
          <p>
            コーチによるレッスンを受けられる、完全予約制・月会費制のスクールです。弾道測定器を備えていますが、
            予約なしで自由に練習できる施設とは利用方法が異なるため、分けて掲載しています。
          </p>
          <div className="cards">
            {lesson.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
        </>
      )}

      {range.length > 0 && (
        <>
          <h2>弾道計測を導入した練習場（{range.length}件）</h2>
          <div className="cards">
            {range.map((f) => <FacilityCard key={f.slug} f={f} />)}
          </div>
        </>
      )}

      <h2>周辺エリアから探す</h2>
      <p>
        <Link href={`/area/${prefSlug}/`}>{c.pref}全体（{prefTotal}施設）</Link>
        からも施設を探すことができます。
      </p>
      {siblings.length > 0 && (
        <>
          <h3>{c.pref}のほかの市区町村</h3>
          <div className="chips">
            {siblings.map((x) => (
              <Link key={x.slug} href={`/area/${prefSlug}/${x.slug}/`}>
                {x.city}（{x.items.length}）
              </Link>
            ))}
          </div>
        </>
      )}
    </main>
  )
}
