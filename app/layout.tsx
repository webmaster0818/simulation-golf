import type { Metadata } from 'next'
import { Chakra_Petch, Zen_Kaku_Gothic_New } from 'next/font/google'
import Link from 'next/link'
import './globals.css'
import { SITE, REGIONS, PREF_SLUG, activePrefs, brands, FEATURES } from '../lib/data'

// 計測器の表示に寄せた角のある書体を英数字に、本文は読みやすい日本語ゴシックに分ける。
const tech = Chakra_Petch({
  subsets: ['latin'], weight: ['500', '700'], display: 'swap', variable: '--font-tech',
})
const jp = Zen_Kaku_Gothic_New({
  subsets: ['latin'], weight: ['400', '500', '700'], display: 'swap', variable: '--font-jp',
})

export const metadata: Metadata = {
  metadataBase: new URL(SITE.origin),
  title: {
    default: `${SITE.name}｜全国のシミュレーションゴルフを公式情報で比較`,
    template: `%s｜${SITE.name}`,
  },
  description: SITE.description,
  // ⚠️ ここに canonical を置かない。置くと全ページがトップを正規URLとして宣言してしまう。
  //    （他サイトで実際に起きた事故。canonical は各ページで個別に付ける）
  // OGPは1枚を全ページ共通で使う。施設ごとに画像を作ると、公式から借りた写真を
  // 出典の文脈から切り離して配ることになるので、サイトの版面を出す。
  openGraph: {
    type: 'website',
    siteName: SITE.name,
    locale: 'ja_JP',
    url: `${SITE.origin}/`,
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: SITE.name }],
  },
  twitter: { card: 'summary_large_image', images: ['/og-image.png'] },
  alternates: { types: { 'application/xml': `${SITE.origin}/sitemap.xml` } },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const prefs = activePrefs()

  return (
    <html lang="ja" className={`${tech.variable} ${jp.variable}`}>
      <body>
        <header className="site">
          <div className="inner">
            <Link href="/" className="logo">
              SIM GOLF NAVI
              <em>シミュレーションゴルフ ナビ</em>
            </Link>
            <nav>
              <Link href="/area/">エリアから探す</Link>
              <Link href="/brand/">ブランドから探す</Link>
              <Link href="/equipment/">機材から探す</Link>
              <Link href="/data/">掲載データについて</Link>
            </nav>
          </div>
        </header>

        {children}

        <footer className="site">
          <div className="wrap cols">
            <div>
              <h4>Area</h4>
              <ul>
                {REGIONS.map((r) => {
                  const has = r.prefs.filter((p) => prefs.includes(p))
                  if (!has.length) return null
                  return (
                    <li key={r.name}>
                      {has.map((p, i) => (
                        <span key={p}>
                          {i > 0 && ' / '}
                          <Link href={`/area/${PREF_SLUG[p]}/`}>{p}</Link>
                        </span>
                      ))}
                    </li>
                  )
                })}
              </ul>
            </div>
            <div>
              <h4>Brand</h4>
              <ul>
                {brands().map((b) => (
                  <li key={b.slug}>
                    <Link href={`/brand/${b.slug}/`}>{b.name}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Filter</h4>
              <ul>
                {FEATURES.map((f) => (
                  <li key={f.slug}>
                    <Link href={`/feature/${f.slug}/`}>{f.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4>About</h4>
              <ul>
                <li><Link href="/data/">掲載データについて</Link></li>
                <li><Link href="/equipment/">弾道計測の機材とは</Link></li>
              </ul>
            </div>
          </div>
          <div className="wrap">
            <p className="note">
              掲載している施設情報は、各施設・ブランドの公式サイトで公開されている内容をもとにしています。
              施設ごとに取得元のURLと取得日を明記しています。料金・営業時間・設備は変更されることがあるため、
              利用前に必ず公式サイトで最新の内容をご確認ください。
              <br />
              当サイトは口コミ・評価を掲載していません。公式サイトに書かれていない項目は「記載なし」と表示します。
            </p>
          </div>
        </footer>
      </body>
    </html>
  )
}
