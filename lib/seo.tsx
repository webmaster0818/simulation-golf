import { SITE, PREF_SLUG, cityOf, type Facility } from './data'

/**
 * 構造化データの組み立て。
 *
 * ⚠️ このサイトは評価や口コミを持たないので aggregateRating / Review は絶対に出さない。
 *    星がリッチリザルトに出るのは魅力的だが、実データが無いものを機械に渡すのは
 *    「公式サイトの情報だけを出典つきで載せる」というこのサイトの前提を壊す。
 * ⚠️ 料金も Offer にしない。載せている月会費は公式表記の写しであって、
 *    条件・期間まで機械可読で正確に表せる粒度ではない。
 */

type Crumb = { name: string; url: string }

export function breadcrumb(items: Crumb[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.name,
      item: c.url.startsWith('http') ? c.url : `${SITE.origin}${c.url}`,
    })),
  }
}

export function websiteLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE.name,
    url: `${SITE.origin}/`,
    description: SITE.description,
    inLanguage: 'ja',
    publisher: { '@type': 'Organization', name: SITE.name, url: `${SITE.origin}/` },
  }
}

/** 一覧ページの中身を機械に伝える。urls は自サイトの相対パス */
export function itemListLd(name: string, urls: string[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name,
    numberOfItems: urls.length,
    itemListElement: urls.map((u, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: `${SITE.origin}${u}`,
    })),
  }
}

export function faqLd(items: { q: string; a: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: items.map((x) => ({
      '@type': 'Question',
      name: x.q,
      acceptedAnswer: { '@type': 'Answer', text: x.a },
    })),
  }
}

/**
 * 施設の構造化データ。値が取れているものだけを出す。
 * openingHours は「24時間」のように営業時間が一意に確定するときだけ Mo-Su 00:00-23:59 にする。
 * 公式表記が自由記述（「平日10:00〜／土日は変動」等）のものは機械可読に落とせないので出さない。
 */
export function facilityLd(f: Facility) {
  const amenities = [
    f.open_24h ? '24時間営業' : null,
    f.private_room ? '個室あり' : null,
    f.parking ? '駐車場あり' : null,
  ].filter(Boolean) as string[]

  return {
    '@context': 'https://schema.org',
    '@type': 'SportsActivityLocation',
    name: f.name,
    ...(f.address
      ? {
          address: {
            '@type': 'PostalAddress',
            streetAddress: f.address,
            addressRegion: f.pref,
            postalCode: f.zip ?? undefined,
            addressCountry: 'JP',
          },
        }
      : {}),
    ...(f.tel ? { telephone: f.tel } : {}),
    ...(f.open_24h ? { openingHours: 'Mo-Su 00:00-23:59' } : {}),
    ...(f.bays_num ? { maximumAttendeeCapacity: f.bays_num } : {}),
    ...(amenities.length
      ? {
          amenityFeature: amenities.map((n) => ({
            '@type': 'LocationFeatureSpecification',
            name: n,
            value: true,
          })),
        }
      : {}),
    ...(f.official ? { sameAs: [f.official] } : {}),
    url: `${SITE.origin}/facility/${f.slug}/`,
  }
}

/** 施設ページのパンくず。都道府県ページが実在するときだけ間に挟む */
export function facilityCrumbs(f: Facility): Crumb[] {
  const c: Crumb[] = [{ name: 'ホーム', url: '/' }]
  if (f.pref && PREF_SLUG[f.pref]) {
    c.push({ name: 'エリアから探す', url: '/area/' })
    c.push({ name: f.pref, url: `/area/${PREF_SLUG[f.pref]}/` })
  }
  c.push({ name: f.name, url: `/facility/${f.slug}/` })
  return c
}

/** 施設ページの説明文。公式表記をそのまま繋ぐと 265 字になることがあったので長さで切る */
export function facilityDescription(f: Facility): string {
  const where = [f.pref, cityOf(f)].filter(Boolean).join('')
  const head = `${f.name}（${f.address ?? where}）の基本情報。`
  const parts = [
    f.hours && `営業時間 ${f.hours}`,
    f.bays && `打席 ${f.bays}`,
    f.parking && `駐車場 ${f.parking}`,
  ].filter(Boolean) as string[]
  const tail = '公式サイトの掲載内容をそのまま記載しています。'
  // 検索結果で切られる前に意味が閉じるよう、入るところまで足して残りは落とす
  let s = head
  for (const p of parts) {
    if (s.length + p.length + 1 > 110 - tail.length) break
    s += (s === head ? '' : '／') + p
  }
  return clip(`${s}。${tail}`.replace('。。', '。'), 118)
}

/** タイトルは長いと検索結果で切られるので、施設名を優先して後半を落とす */
export function clip(s: string, max = 58): string {
  return s.length <= max ? s : `${s.slice(0, max - 1)}…`
}

/**
 * タイトル用の施設名。
 * 店名に入っている補足の括弧（「（TSUTAYA札幌菊水店内）」「（ステップゴルフエクストラ○○）」）は
 * 検索結果では切られるだけなので落とす。本文と構造化データには正式名称をそのまま出す。
 */
export function titleName(name: string): string {
  const s = name.replace(/[（(][^）)]*[）)]\s*$/, '').trim()
  return s.length >= 4 ? s : name
}

export function JsonLd({ data }: { data: object | object[] }) {
  const arr = Array.isArray(data) ? data : [data]
  return (
    <>
      {arr.map((d, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(d) }}
        />
      ))}
    </>
  )
}
