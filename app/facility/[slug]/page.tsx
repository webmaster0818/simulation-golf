import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, PREF_SLUG, FACILITIES, OPEN_FACILITIES, bySlug, byPref, cityOf, wardOf,
  cities as cityPagesOf, asOf, REGIONS,
} from '../../../lib/data'
import FacilityCard from '../../../components/FacilityCard'
import { JsonLd, breadcrumb, facilityCrumbs, facilityLd, facilityDescription, clip, titleName } from '../../../lib/seo'

type Params = { slug: string }

export function generateStaticParams(): Params[] {
  return FACILITIES.map((f) => ({ slug: f.slug }))
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params
  const f = bySlug(slug)
  if (!f) return {}
  const where = [f.pref, cityOf(f)].filter(Boolean).join('')
  // ⚠️ 店名だけだとブランドをまたいで衝突する（「春日井店」が2ブランドにある）。
  //    店名にブランド名が含まれていないときだけ前に付ける。
  const label = f.brand && !f.name.includes(f.brand)
    ? `${f.brand} ${titleName(f.name)}`
    : titleName(f.name)
  return {
    title: clip(`${label}｜${where}のシミュレーションゴルフ`),
    description: facilityDescription(f),
    alternates: { canonical: `${SITE.origin}/facility/${slug}/` },
  }
}

/** 値が無いときは推測せず、無いと書く */
function Row({ k, v }: { k: string; v: string | null | undefined }) {
  return (
    <div>
      <dt>{k}</dt>
      {v ? <dd>{v}</dd> : <dd className="none">公式サイトに記載なし</dd>}
    </div>
  )
}

export default async function FacilityPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params
  const f = bySlug(slug)
  if (!f) return null

  const city = cityOf(f)
  // その施設がある市区町村のページ（3施設以上ある市区町村にだけ作っている）
  const ward = wardOf(f)
  const cityPage = f.pref && ward
    ? cityPagesOf().find((x) => x.pref === f.pref && x.city === ward)
    : undefined
  // ⚠️ 県内に自分しか無い施設は、県一覧からの1本だけになって実質孤立する（2026-10-01に判明）。
  //    その場合は同じ地方の施設に広げて導線を作る。
  const samePref = f.pref ? byPref(f.pref).filter((x) => x.slug !== f.slug) : []
  const region = f.pref ? REGIONS.find((r) => r.prefs.includes(f.pref as string)) : undefined
  const near = samePref.length
    ? samePref.slice(0, 6)
    : region
      ? OPEN_FACILITIES.filter((x) => x.pref && region.prefs.includes(x.pref) && x.slug !== f.slug).slice(0, 6)
      : []
  const nearIsRegion = samePref.length === 0
  const sameBrand = f.brand_slug
    ? OPEN_FACILITIES.filter((x) => x.brand_slug === f.brand_slug && x.slug !== f.slug)
    : []

  // 構造化データ。住所が取れているものだけ出す（不完全なデータを機械に渡さない）。
  const ld = [facilityLd(f), breadcrumb(facilityCrumbs(f))]

  return (
    <main className="wrap">
      <JsonLd data={ld} />

      <nav className="crumbs">
        <Link href="/">ホーム</Link>
        {f.pref && (
          <>
            {' / '}
            <Link href={`/area/${PREF_SLUG[f.pref]}/`}>{f.pref}</Link>
          </>
        )}
        {f.pref && cityPage && (
          <>
            {' / '}
            <Link href={`/area/${PREF_SLUG[f.pref]}/${cityPage.slug}/`}>{cityPage.city}</Link>
          </>
        )}
        {' / '}{f.name}
      </nav>

      <section className="hero">
        <div className="kicker">
          {f.brand ?? 'Driving range with ball tracing'}
        </div>
        <h1>{f.name}</h1>
        <p className="lead">
          {f.pref}
          {city && city !== f.pref ? city : ''}にある
          {f.segment === 'indoor'
            ? '屋内のシミュレーションゴルフ施設'
            : f.segment === 'lesson'
              ? 'コーチに教わるインドアゴルフスクール'
              : '弾道計測つきの練習場'}です。
          下の情報はすべて公式サイトに掲載されている内容で、{asOf(f.fetched_at)}のものです。
        </p>
      </section>

      {!f.open && (
        <div className="verdict">
          <span className="tag">Notice</span>
          <p style={{ marginBottom: 0 }}>
            この店舗は公式サイトで<strong>オープン準備中</strong>と案内されています。
            {f.hours ? '' : '営業条件は開業後に変わる可能性があります。'}
            利用前に公式サイトでご確認ください。
          </p>
        </div>
      )}

      <h2>基本情報</h2>
      <dl className="spec">
        <Row k="住所" v={f.zip ? `〒${f.zip} ${f.address}` : f.address} />
        <Row k="アクセス" v={f.access} />
        <Row k="電話番号" v={f.tel} />
        <Row k="営業時間" v={f.hours} />
        <Row k="定休日" v={f.closed} />
        <Row k="打席・個室" v={f.bays} />
        <Row k="駐車場" v={f.parking} />
        {/* 都度払いの屋内施設（盛岡のゴルフィン等）は月会費が無く利用料だけ。
            月会費欄だけ見て「料金を公開していません」と出していた（2026-10-03）。両方の欄を出す */}
        {f.segment === 'indoor'
          ? <>
              <Row k="月会費" v={f.monthly_fee} />
              {f.usage_fee && <Row k="都度利用の料金" v={f.usage_fee} />}
            </>
          : <Row k="弾道計測の利用料" v={f.usage_fee} />}
        {f.segment !== 'range' && f.equipment && (
          <Row k="計測の設備" v={f.equipment} />
        )}
        {/* 機材ページは一覧からの1本しか張られないので、該当施設から繋ぐ */}
        {f.equipment && /トラックマン|TRACKMAN|TrackMan/i.test(f.equipment) && (
          <div>
            <dt>同じ機材の施設</dt>
            <dd>
              <Link href="/equipment/trackman/">
                トラックマンを導入している施設の一覧を見る
              </Link>
            </dd>
          </div>
        )}
        {f.segment === 'range' && (
          <>
            <Row k="飛距離" v={f.distance_yard ? `${f.distance_yard}ヤード` : null} />
            <Row k="計測の設備" v={f.equipment} />
            {/* 機材ページへの導線。/equipment/toptracer/ が一覧からの1本しか
                張られていなかったので、該当施設から繋ぐ */}
            {f.equipment === 'トップトレーサー・レンジ' && (
              <div>
                <dt>同じ機材の施設</dt>
                <dd>
                  <Link href="/equipment/toptracer/">
                    トップトレーサーを導入している練習場の一覧を見る
                  </Link>
                </dd>
              </div>
            )}
          </>
        )}
      </dl>

      {/* ⚠️ 「このブランドは料金を公開していません」と言えるのは、ブランドの全店で
          料金が取れていないときだけ。ほかの店では公開されているブランド
          （Lounge Range は店舗別の料金ページがある）で同じ文を出すと事実と違う。 */}
      {f.segment === 'indoor' && !f.monthly_fee && !f.usage_fee && (
        f.brand_slug && OPEN_FACILITIES.some((x) => x.brand_slug === f.brand_slug && x.monthly_fee) ? (
          <div className="nodata">
            この店舗の料金は、当サイトでは確認できていません。
            同じブランドでも料金は店舗によって違うため、推測した金額を載せていません。
            公式サイトまたは店舗へ直接ご確認ください。
          </div>
        ) : !f.brand_slug ? (
          // ブランド無しの単独施設に「このブランドは…公開していません」と出ていた（2026-10-04）。
          // 料金表が画像だけの施設もあり、「公開していない」とは言えない
          <div className="nodata">
            この施設の料金は、当サイトでは確認できていません。
            推測した金額は載せていません。公式サイトまたは施設へ直接ご確認ください。
          </div>
        ) : (
          <div className="nodata">
            このブランドは、店舗ごとの料金を公式サイトで公開していません。
            料金は店舗によって違うことがあるため、当サイトでは推測した金額を載せていません。
            公式サイトまたは店舗へ直接ご確認ください。
          </div>
        )
      )}

      <p>
        {f.official && (
          <a className="official" href={f.official} target="_blank" rel="noopener noreferrer">
            公式サイトを見る
          </a>
        )}
        {f.address && (
          <a className="official"
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(f.address)}`}
            target="_blank" rel="noopener noreferrer">
            地図で見る
          </a>
        )}
      </p>

      <p className="source">
        出典：
        <a href={f.source_url} target="_blank" rel="noopener noreferrer">{f.source_url}</a>
        （{asOf(f.fetched_at)}に取得）。
        料金・営業時間・設備は変更されることがあります。利用前に公式サイトで最新の内容をご確認ください。
      </p>

      {sameBrand.length > 0 && f.brand_slug && (
        <>
          <h2>{f.brand}のほかの店舗</h2>
          <div className="cards">
            {sameBrand.slice(0, 6).map((x) => <FacilityCard key={x.slug} f={x} />)}
          </div>
          <p className="source">
            <Link href={`/brand/${f.brand_slug}/`}>
              {f.brand}の全{sameBrand.length + 1}店舗を見る
            </Link>
          </p>
        </>
      )}

      {near.length > 0 && f.pref && (
        <>
          <h2>{nearIsRegion && region ? `${region.name}のほかの施設` : `${f.pref}のほかの施設`}</h2>
          <div className="cards">
            {near.map((x) => <FacilityCard key={x.slug} f={x} />)}
          </div>
          <p className="source">
            <Link href={`/area/${PREF_SLUG[f.pref]}/`}>
              {f.pref}の施設をすべて見る（{byPref(f.pref).length}件）
            </Link>
          </p>
        </>
      )}
    </main>
  )
}
